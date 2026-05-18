<template>
    <a-drawer
        placement="bottom"
        :visible="visible"
        class="widgets_drawer"
        :wrapClassName="`${useDrag ? 'drag_active' : ''} widgets_drag_drawer`"
        :class="[draggable && 'draggable', isMobile && 'mobile']"
        :mask="isMobile"
        :height="drawerHeight"
        ref="widgetsDrawer"
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div v-if="isMobile" class="drawer_header">
            <a-input-search 
                :value="search"
                :placeholder="$t('dashboard.search_placeholder')" 
                style="width: 100%" 
                size="large"
                @change="searchInput" />
            <a-button 
                type="ui" 
                ghost
                flaticon 
                class="ml-3"
                icon="fi-rr-bars-sort" 
                shape="circle"
                @click="categoryVisible = true" />
        </div>
        <div class="drawer_body">
            <div v-if="!isMobile" class="drawer_body__aside">
                <div class="drawer_body__aside--search">
                    <a-input-search 
                        :value="search"
                        :placeholder="$t('dashboard.search_placeholder')" 
                        style="width: 100%" 
                        size="large"
                        @change="searchInput" />
                </div>
                <div class="drawer_body__aside--list">
                    <div 
                        class="category_item" 
                        :class="activeCategory === 'all' && 'active'"
                        @click="selectCategory('all')">
                        {{ $t('dashboard.all_widgets') }}
                    </div>
                    <div v-if="categoryLoading" class="flex justify-center mt-2"><a-spin size="small" /></div>
                    <div 
                        v-for="cat in categoryList" 
                        :key="cat.id"
                        class="category_item"
                        :class="activeCategory === cat.id && 'active'"
                        @click="selectCategory(cat.id)">
                        {{ cat.name }}
                    </div>
                </div>
            </div>
            <div class="drawer_body__cont">
                <RecycleScroller
                    ref="scroller"
                    class="widget_grid"
                    :items="widgetList.results"
                    :item-size="102"
                    :grid-items="gridItems"
                    :item-secondary-size="secondarySize">
                    <template #before>
                        <div v-if="widgetsEmpty">
                            <a-empty :description="$t('dashboard.no_widgets')" />
                        </div>
                    </template>
                    <template #default="{ item }">
                        <div class="widget_pd" @click="addWidgetMobile(item)">
                            <div
                                class="widget_item select-none cursor-move"
                                unselectable="on"
                                draggable="true"
                                @drag="drag(item)" 
                                @dragend="dragend(item)">
                                <i class="fi icon" :class="item.icon" />
                                <div class="name">{{ item.name }}</div>
                                <div class="ver">
                                    <i 
                                        v-if="item.is_desktop && item.is_mobile" 
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                        :content="!isMobile && $t('dashboard.mobile_and_pc')"
                                        class="fi fi-rr-devices" />
                                    <i 
                                        v-if="item.is_desktop && !item.is_mobile" 
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                        :content="!isMobile && $t('dashboard.only_pc')"
                                        class="fi fi-rr-computer" />
                                </div>
                                <div v-if="!isMobile" class="added_button">
                                    <a-button 
                                        type="success" 
                                        flaticon 
                                        size="small"
                                        icon="fi-rr-plus" 
                                        shape="circle"
                                        @click="addWidget(item)" />
                                </div>
                            </div>
                        </div>
                    </template>
                    <template #after>
                        <infinite-loading 
                            ref="widgetsInfinity"
                            @infinite="getWidgets"
                            v-bind:distance="10">
                            <div 
                                slot="spinner"
                                class="flex items-center justify-center inf_spinner">
                                <a-spin />
                            </div>
                            <div slot="no-more"></div>
                            <div slot="no-results"></div>
                        </infinite-loading>
                    </template>
                </RecycleScroller>
            </div>
        </div>
        <div class="drawer_footer">
            <template v-if="isMobile">
                <a-button 
                    type="ui" 
                    ghost 
                    block 
                    @click="visible = false">
                    {{ $t('dashboard.close') }}
                </a-button>
            </template>
            <template v-else>
                <div>{{ $t('dashboard.drag_widget') }}</div>
                <a-button type="primary" @click="visible = false">
                    {{ $t('dashboard.done') }}
                </a-button>
            </template>
        </div>
        <a-drawer
            v-if="isMobile"
            placement="right"
            :visible="categoryVisible"
            class="category_drawer"
            :title="$t('dashboard.widget_categories')"
            width="100%"
            @close="categoryVisible = false">
            <div class="category_drawer__body">
                <div 
                    class="category_item" 
                    :class="activeCategory === 'all' && 'active'"
                    @click="selectCategory('all')">
                    {{ $t('dashboard.all_widgets') }}
                </div>
                <div v-if="categoryLoading" class="flex justify-center mt-2"><a-spin size="small" /></div>
                <div 
                    v-for="cat in categoryList" 
                    :key="cat.id"
                    class="category_item"
                    :class="activeCategory === cat.id && 'active'"
                    @click="selectCategory(cat.id)">
                    {{ cat.name }}
                </div>
            </div>
            <div class="category_drawer__footer">
                <a-button 
                    type="ui" 
                    ghost 
                    block 
                    @click="categoryVisible = false">
                    {{ $t('dashboard.close') }}
                </a-button>
            </div>
        </a-drawer>
    </a-drawer>
</template>

<script>
import { onClickOutside } from '@vueuse/core'
import eventBus from '@/utils/eventBus'
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

let timer;

const updateKey = 'widgets_update',
    mouseXY = {"x": null, "y": null},
    DragPos = {"x": null, "y": null, "w": 1, "h": 1, "i": null}

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        RecycleScroller
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        windowHeight() {
            return this.$store.state.windowHeight
        },
        gridlayout() {
            return this.$store.state.dashboard.gridlayout
        },
        categoryList() {
            return this.$store.state.dashboard.categoryList
        },
        widgetList() {
            return this.$store.state.dashboard.widgetList
        },
        activeCategory() {
            return this.$store.state.dashboard.activeCategory
        },
        widgetsEmpty() {
            return this.$store.state.dashboard.widgetsEmpty
        },
        drawerHeight() {
            if(this.isMobile) {
                return '100%'
            } else {
                if(this.windowHeight >= 650) {
                    return 500
                } else {
                    if(this.windowHeight <= 400) {
                        return this.windowHeight - 50
                    } else
                        return 400
                }
            }
        },
        gridItems() {
            if(this.isMobile) {
                return 2
            } else {
                if(this.windowWidth < 1200) {
                    return 2
                } else
                    return 3
            }
        },
        secondarySize() {
            if(this.isMobile) {
                return (this.windowWidth - 24) / 2
            } else {
                return 224.66
            }
        },
        widgets: {
            get() {
                return this.$store.state.dashboard.widgets
            },
            set(val) {
                // console.log(val)
            }
        },
        visible: {
            get() {
                return this.$store.state.dashboard.catalogVisible
            },
            set(val) {
                this.$store.commit('dashboard/SET_CATALOG_VISIBLE', val)
            }
        },
        search() {
            return this.$store.state.dashboard.searchWidget
        }
    },
    data() {
        return {
            categoryLoading: false,
            widgetsLoading: false,
            widgetsList: [],
            draggable: false,
            useDrag: false,
            categoryVisible: false
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                this.getCategory()
            } else {
                this.clearData()
            }
        },
        clearData() {
            
        },
        searchInput(e) {
            const value = e.target.value
            clearTimeout(timer)

            timer = setTimeout(() => {
                this.$store.commit('dashboard/SET_SEARCH_WIDGET', value)
                this.clearWidgetsList()
            }, 400)
        },
        async getWidgets($state) {
            if(!this.widgetsLoading && this.widgetList.next) {
                try {
                    this.widgetsLoading = true
                    await this.$store.dispatch('dashboard/getWidgets')
                    if(this.widgetList.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.widgetsLoading = false
                }
            } else {
                $state.complete()
            }
        },
        async getCategory() {
            try {
                this.categoryLoading = true
                await this.$store.dispatch('dashboard/getCategory')
            } catch(e) {
                console.log(e)
            } finally {
                this.categoryLoading = false
            }
        },
        async addWidgetMobile(widget) {
            if (this.isMobile) {
                try {
                    this.visible = false;
                    this.$message.loading({ content: this.$t('dashboard.loading_update'), key: updateKey });
                    await this.$store.dispatch('dashboard/addWidgetMobile', { 
                        widget: {
                            ...widget,
                            added: true
                        }
                    });
                    this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 1 });
                } catch (e) {
                    console.log(e);
                    this.$message.error({ content: this.$t('dashboard.update_error'), key: updateKey, duration: 2 });
                }
            }
        },
        async addWidget(widget) {
            try {
                this.$message.loading({ content: this.$t('dashboard.loading_update'), key: updateKey });
                await this.$store.dispatch('dashboard/addWidgetButton', { 
                    widget: {
                        ...widget,
                        added: true
                    }
                });
                this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 2 });
            } catch (e) {
                console.log(e);
                this.$message.error({ content: this.$t('dashboard.update_error'), key: updateKey, duration: 2 });
            }
        },
        drag(widget) {
            if(!this.isMobile) {
                this.useDrag = true
                const parentRect = document.getElementById('content').getBoundingClientRect()
                let mouseInGrid = false
                const widgetId = widget.id
                if (((mouseXY.x > parentRect.left) && (mouseXY.x < parentRect.right)) && ((mouseXY.y > parentRect.top) && (mouseXY.y < parentRect.bottom))) {
                    mouseInGrid = true
                }
                if (mouseInGrid === true && (this.widgets.findIndex(item => item.i === widgetId)) === -1) {
                    this.$store.commit('dashboard/PUSH_WIDGETS_ANY', {
                        x: (this.widgets.length * 2) % (this.colNum || 12),
                        y: this.widgets.length + (this.colNum || 12),
                        w: widget.w,
                        h: widget.h,
                        i: widgetId,
                        added: true,
                        widget: widget,
                        maxH: widget.maxH,
                        maxW: widget.maxW,
                        minH: widget.minH,
                        minW: widget.minW,
                        is_desktop: widget.is_desktop,
                        is_mobile: widget.is_mobile
                    })
                }
                let index = this.widgets.findIndex(item => item.i === widgetId)
                if (index !== -1) {
                    try {
                        this.gridlayout.$children[this.widgets.length].$refs.item.style.display = "none"
                    } catch {
                    }
                    let el = this.gridlayout.$children[index]
                    el.dragging = {"top": mouseXY.y - parentRect.top, "left": mouseXY.x - parentRect.left}
                    let new_pos = el.calcXY(mouseXY.y - parentRect.top, mouseXY.x - parentRect.left)

                    if (mouseInGrid === true) {
                        this.gridlayout.dragEvent('dragstart', widgetId, new_pos.x, new_pos.y, 1, 1)
                        DragPos.i = String(index)
                        DragPos.x = this.widgets[index].x
                        DragPos.y = this.widgets[index].y
                    }
                    if (mouseInGrid === false) {
                        this.gridlayout.dragEvent('dragend', widgetId, new_pos.x, new_pos.y, 1, 1)
                        this.widgets = this.widgets
                    }
                }
            }
        },
        dragend(widget) {
            const parentRect = document.getElementById('content').getBoundingClientRect();
            let mouseInGrid = false
            const widgetId = widget.id
            if (((mouseXY.x > parentRect.left) && (mouseXY.x < parentRect.right)) && ((mouseXY.y > parentRect.top) && (mouseXY.y < parentRect.bottom))) {
                mouseInGrid = true
            }
            if (mouseInGrid === true) {
                this.gridlayout.dragEvent('dragend', widgetId, DragPos.x, DragPos.y, 1, 1)
                // this.widgets = this.widgets
                this.$store.dispatch('dashboard/addWidgetDrag')
                //this.visible = true
            }
            this.useDrag = false
        },
        selectCategory(id) {
            if(this.activeCategory !== id) {
                if(this.categoryVisible)
                    this.categoryVisible = false
                this.$store.commit('dashboard/SET_ACTIVE_CATEGORY', id)
                this.clearWidgetsList()
            }
        },
        clearWidgetsList() {
            this.$nextTick(() => {
                this.$store.commit('dashboard/CLEAR_WIDGETS')
                this.$refs['widgetsInfinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on('selectWidget', () => {
            this.visible = true
        })

        if(!this.isMobile) {
            document.addEventListener("dragover", function (e) {
                mouseXY.x = e.clientX;
                mouseXY.y = e.clientY;
            }, false)
            this.$nextTick(() => {
                if(this.$refs.widgetsDrawer) {
                    onClickOutside(this.$refs.widgetsDrawer, () => {
                        if(this.visible)
                            this.visible = false
                    })
                }
            })
        }
    },
    beforeDestroy() {
        eventBus.$off('selectWidget')
        if(this.visible)
            this.$store.commit('dashboard/SET_CATALOG_VISIBLE', false)
    }
}
</script>

<style lang="scss">
.drag_active{
    .ant-drawer-content-wrapper{
        transform: translateY(470px);
    }
}
</style>

<style lang="scss" scoped>
.category_drawer{
    &::v-deep{
        .category_item{
            cursor: pointer;
            border-radius: var(--borderRadius);
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            padding: 9px 10px;
            margin: 0 -8px;
            &:not(:last-child){
                margin-bottom: 2px;
            }
            &:hover{
                color: var(--blue);
            }
            &.active{
                background: rgba(227, 230, 234, 0.7);
                color: var(--text);
            }
        }
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .category_drawer__body{
            overflow-y: auto;
            height: calc(100% - 40px);
            padding: 15px;
        }
        .category_drawer__footer{
            padding: 5px 15px;
            border-top: 1px solid var(--border2);
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 40px;
        }
    }
}
.widgets_drawer{
    transition: all 0.1s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.draggable{
        display: none;
        opacity: 0;
    }
    .drawer_header{
        height: 60px;
        padding: 5px 15px;
        display: flex;
        align-items: center;
    }
    &:not(.mobile){
        &::v-deep{
            .ant-drawer-content-wrapper{
                border-radius: var(--borderRadius) var(--borderRadius) 0 0;
                -webkit-backdrop-filter: saturate(180%) blur(20px);
                backdrop-filter: saturate(180%) blur(20px);
                background: rgba(251,251,253,0.8);
                position: absolute;
                max-width: 720px;
                left: calc(50% - 360px);
                @media (min-width: 1200px) {
                    max-width: 1000px;
                    left: calc(50% - 500px);
                }
                .ant-drawer-content{
                    background: transparent;
                }
            }
            .drawer_footer{
                height: 50px;
            }
            .drawer_body{
                height: calc(100% - 50px);
                grid-template-columns: 250px 1fr;
                display: grid;
                gap: 0px;
                @media (min-width: 1200px) {
                    grid-template-columns: 300px 1fr;
                }
            }
        }
    }
    &::v-deep{
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: 100%;
        }
        .drawer_body{
            height: calc(100% - 100px);
            &__aside{
                width: 250px;
                border-right: 1px solid var(--border2);
                display: flex;
                flex-direction: column;
                height: 100%;
                overflow: hidden;
                @media (min-width: 1200px) {
                    width: 300px;
                }
                .category_item{
                    cursor: pointer;
                    border-radius: var(--borderRadius);
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                    padding: 9px 10px;
                    margin: 0 -8px;
                    &:not(:last-child){
                        margin-bottom: 2px;
                    }
                    &:hover{
                        color: var(--blue);
                    }
                    &.active{
                        background: rgba(227, 230, 234, 0.7);
                        color: var(--text);
                    }
                }
                &--search{
                    padding-bottom: 10px;
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-top: 15px;
                    border-bottom: 1px solid var(--border2);
                }
                &--list{
                    overflow-y: auto;
                    flex-grow: 1;
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-bottom: 15px;
                    padding-top: 10px;
                }
            }
            &__cont{
                height: 100%;
                overflow: hidden;
                .widget_grid{
                    height: 100%;
                    padding-top: 15px;
                    padding-bottom: 10px;
                    padding-left: 12px;
                    padding-right: 12px;
                }
                .widget_pd{
                    padding-left: 3px;
                    padding-right: 3px;
                    padding-bottom: 6px;
                }
                .widget_item{
                    border: 1px solid var(--border2);
                    border-radius: var(--borderRadius);
                    text-align: center;
                    padding: 20px 15px;
                    position: relative;
                    .ver{
                        position: absolute;
                        top: 5px;
                        left: 7px;
                        z-index: 5;
                        color: var(--gray);
                    }
                    .icon{
                        font-size: 28px;
                    }
                    .name{
                        margin-top: 6px;
                        line-height: 16px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    .added_button{
                        position: absolute;
                        top: 3px;
                        right: 3px;
                        z-index: 15;
                        opacity: 0;
                        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                        .ant-btn{
                            width: 20px;
                            height: 20px;
                            min-width: 20px;
                            font-size: 12px;
                        }
                    }
                    &:hover{
                        .added_button{
                            opacity: 1;
                        }
                    }
                }
            }
        }
        .drawer_footer{
            padding: 5px 15px;
            border-top: 1px solid var(--border2);
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 40px;
        }
    }
}
</style>