<template>
    <div class="dashboard">
        <div class="dashboard__header">
            <h1>{{ $t('dashboard.dashboard_title') }}</h1>
            <div class="dashboard_list_w">
                <div
                    class="dashboard_list_scroll_w"
                    @mouseenter="onListWrapperEnter"
                    @mouseleave="onListWrapperLeave">
                    <a-button
                        v-if="showLeftArrow"
                        class="scroll_arrow left"
                        shape="circle"
                        size="small"
                        type="flat_primary"
                        flaticon
                        icon="fi-rr-angle-small-left"
                        @mouseenter="startHoverScroll('left')"
                        @mouseleave="stopHoverScroll" />
                    <a-button
                        v-if="showRightArrow"
                        class="scroll_arrow right"
                        shape="circle"
                        size="small"
                        type="flat_primary"
                        flaticon
                        icon="fi-rr-angle-small-right"
                        @mouseenter="startHoverScroll('right')"
                        @mouseleave="stopHoverScroll" />
                    <div ref="dashboardListScroll" class="dashboard_list_scroll" @scroll="onListScroll">
                        <draggable
                            v-model="dashboardList"
                            class="dashboard_list"
                            draggable=".drag_item"
                            handle=".drag_handle"
                            ghost-class="ghost"
                            @start="onDragStart"
                            @end="onDragEnd">
                            <div 
                                v-for="item in dashboardList" 
                                :key="item.id" 
                                :ref="'dashboardItem_' + item.id"
                                :class="active === item.id && 'active'"
                                class="dashboard_list__item select-none drag_item">
                                <div class="name" @click="selectDashboard(item)">
                                    {{ item.name }}
                                </div>
                                <div 
                                    class="actions" 
                                    :style="dragging && 'opacity: 0;'"
                                    :class="[dashboardList.length === 1 && 'one']">
                                    <div class="actions__item" @click="editDashboard(item)">
                                        <i class="fi fi-rr-pencil"></i>
                                    </div>
                                    <template v-if="dashboardList.length > 1">
                                        <div class="line"></div>
                                        <div class="actions__item drag_handle">
                                            <i class="fi fi-rr-arrows-alt"></i>
                                        </div>
                                        <div class="line"></div>
                                        <div class="actions__item" @click="deleteDashboard(item)">
                                            <i class="fi fi-rr-trash"></i>
                                        </div>
                                    </template>
                                </div>
                            </div>
                            <div v-if="dLoading" class="dashboard_list__item active px-10">
                                <a-spin />
                            </div>
                            <a-tooltip :title="$t('dashboard.addTitle')">
                                <a-button 
                                    type="ui" 
                                    ghost 
                                    class="ml-2"
                                    flaticon 
                                    shape="circle"
                                    icon="fi-rr-plus"
                                    @click="addDashboard()" />
                            </a-tooltip>
                        </draggable>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2 pl-3">
                <a-button 
                    type="primary" 
                    icon="fi-rr-plus-small"
                    flaticon
                    @click="selectWidget()">
                    {{ $t('dashboard.add_widget') }}
                </a-button>
                <HelpButton partCode="dashboard" type="button" />
            </div>
        </div>
        <div class="dashboard__body">
            <a-spin class="ds_spin" :spinning="loading">
                <component :is="dashboardWidget" />
            </a-spin>
        </div>
        <a-modal 
            v-model="visible" 
            :footer="false"
            destroyOnClose
            :afterClose="afterClose"
            @afterVisibleChange="afterVisibleChange"
            :title="edit ? $t('dashboard.edit_dashboard') : $t('dashboard.add_dashboard')">
            <div ref="formWrapper">
                <a-form-model
                    ref="ruleForm"
                    :model="form"
                    :rules="rules">
                    <a-form-model-item ref="name" class="mb-2" :label="$t('dashboard.desktop_name')" prop="name">
                        <a-input v-model="form.name" ref="nameInput" size="large" @pressEnter="formSubmit" />
                    </a-form-model-item>
                    <a-form-model-item v-if="!edit" ref="desktop_template" :label="$t('dashboard.desktop_template')" prop="desktop_template">
                        <DSelect
                            v-model="form.desktop_template"
                            size="large"
                            apiUrl="/widgets/desktop_templates/"
                            class="w-full"
                            infinity
                            :maxTagCount="1"
                            :initList="false"
                            :listObject="false"
                            labelKey="name"
                            :placeholder="$t('dashboard.select_desktop_template')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null" />
                    </a-form-model-item>
                    <a-button type="primary" size="large" block :loading="formLoading" @click="formSubmit">
                        {{ $t('dashboard.save') }}
                    </a-button>
                </a-form-model>
            </div>
        </a-modal>
        <WidgetsDrawer />
        <SettingDrawer />
    </div>
</template>

<script>
const updateKey = 'update_dashboard'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        WidgetsDrawer: () => import('./WidgetsDrawer/index.vue'),
        draggable: () => import('vuedraggable').then(m => m.default || m),
        SettingDrawer: () => import('./SettingDrawer/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        showLeftArrow() {
            return !this.isMobile && this.isListHover && this.canScrollLeft
        },
        showRightArrow() {
            return !this.isMobile && this.isListHover && this.canScrollRight
        },
        dashboardList: {
            get() {
                return this.$store.state.dashboard.dashboardList
            },
            set(val) {
                this.$store.dispatch('dashboard/updateDashboardPosition', val)
            }
        },
        active: {
            get() {
                return this.$store.state.dashboard.active
            },
            set(val) {
                this.$store.commit('dashboard/SET_ACTIVE', val)
            }
        },
        dashboardWidget() {
            return () => import('./Grid.vue')
        }
    },
    data() {
        return {
            dragging: false,
            isListHover: false,
            canScrollLeft: false,
            canScrollRight: false,
            hoverScrollTimer: null,
            hoverScrollDir: null,
            form: {
                name: '',
                desktop_template: null
            },
            rules: {
                name: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { max: 100, message: this.$t('required_sym', { sym: 100 }), trigger: 'change' }
                ]
            },
            edit: false,
            dLoading: false,
            loading: false,
            formLoading: false,
            visible: false
        }
    },
    created() {
        if(!this.dashboardList.length)
            this.getDashboardList()
        else
            this.updatedState()
    },
    mounted() {
        window.addEventListener('resize', this.updateArrows)
        this.$nextTick(() => this.updateArrows())
    },
    beforeDestroy() {
        this.stopHoverScroll()
        window.removeEventListener('resize', this.updateArrows)
    },
    watch: {
        dashboardList() {
            this.$nextTick(() => this.updateArrows())
        },
        active(id) {
            this.$nextTick(() => this.scrollActiveToStart(id))
        },
        isMobile() {
            this.$nextTick(() => this.updateArrows())
        }
    },
    methods: {
        onListWrapperEnter() {
            this.isListHover = true
            this.$nextTick(() => this.updateArrows())
        },
        onListWrapperLeave() {
            this.isListHover = false
            this.stopHoverScroll()
        },
        onListScroll() {
            this.updateArrows()
        },
        getScrollEl() {
            return this.$refs.dashboardListScroll
        },
        updateArrows() {
            const el = this.getScrollEl()
            if(!el || this.isMobile) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if(max <= 0) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollLeft = left > eps
            this.canScrollRight = left < max - eps
        },
        startHoverScroll(dir) {
            if(this.isMobile || !this.isListHover) return

            const el = this.getScrollEl()
            if(!el) return

            this.stopHoverScroll()
            this.hoverScrollDir = dir

            const step = 8
            const tick = 16

            this.hoverScrollTimer = setInterval(() => {
                if(!this.isListHover) {
                    this.stopHoverScroll()
                    return
                }

                const max = el.scrollWidth - el.clientWidth
                if(max <= 0) {
                    this.updateArrows()
                    this.stopHoverScroll()
                    return
                }

                let next = el.scrollLeft
                if(this.hoverScrollDir === 'left') next = next - step
                if(this.hoverScrollDir === 'right') next = next + step

                if(next < 0) next = 0
                if(next > max) next = max

                el.scrollLeft = next
                this.updateArrows()

                if(next === 0 || next === max) this.stopHoverScroll()
            }, tick)
        },
        stopHoverScroll() {
            if(this.hoverScrollTimer) {
                clearInterval(this.hoverScrollTimer)
                this.hoverScrollTimer = null
            }
            this.hoverScrollDir = null
        },
        scrollActiveToStart(id) {
            const container = this.getScrollEl()
            const refEl = this.$refs['dashboardItem_' + id]
            const el = Array.isArray(refEl) ? refEl[0] : refEl
            if(!container || !el) return

            const offset = this.isMobile ? 15 : 30
            const containerRect = container.getBoundingClientRect()
            const elRect = el.getBoundingClientRect()

            const leftDelta = elRect.left - containerRect.left - offset
            const rightDelta = elRect.right - containerRect.right
            if(leftDelta >= 0 && rightDelta <= 0) return

            const targetLeft = container.scrollLeft + leftDelta
            if(typeof container.scrollTo === 'function') {
                container.scrollTo({ left: targetLeft, behavior: 'smooth' })
            } else {
                container.scrollLeft = targetLeft
            }

            this.$nextTick(() => this.updateArrows())
        },
        onDragStart() {
            this.dragging = true
        },
        onDragEnd() {
            this.dragging = false
            this.$nextTick(() => this.updateArrows())
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    if(this.$refs.nameInput)
                        this.$refs.nameInput.focus()
                })
            }
        },
        async updatedState() {
            try {
                //this.$message.loading({ content: this.$t('dashboard.updating'), key: updateKey })
                await this.$store.dispatch('dashboard/updatedState')
                this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 0.5 })
            } catch(e) {
                console.log(e)
                //this.$message.error({ content: this.$t('dashboard.update_error'), key: updateKey, duration: 2 })
            }
        },
        selectTemplate(item) {
            if(this.form.desktop_template === item.id) {
                this.form.desktop_template = null
            } else {
                this.form.desktop_template = item.id
            }
        },
        addDashboard() {
            this.visible = true
        },
        selectDashboard(item) {
            if(this.active !== item.id) {
                this.active = item.id
                localStorage.setItem('active_dashboard', item.id)
                this.getWidgets()
            }
        },
        async getDashboardList() {
            try {
                this.loading = true
                this.dLoading = true 
                await this.$store.dispatch('dashboard/getDashboardList') 
                this.getWidgets()
            } catch(error) {
                errorHandler({error, show: false})
                this.loading = false
            } finally {
                this.dLoading = false
                this.$nextTick(() => this.updateArrows())
            }
        },
        async getWidgets() {
            try {
                if(!this.loading)
                    this.loading = true
                await this.$store.dispatch('dashboard/getActiveWidgets', {
                    id: this.active
                })
            } catch(error) {
                if(error?.detail && error.detail.includes("Страница не найдена.")) {
                    localStorage.removeItem('active_dashboard')
                    this.reInit()
                }
                if(error?.data?.detail && error.data.detail.includes("Страница не найдена.")) {
                    localStorage.removeItem('active_dashboard')
                    this.reInit()
                }
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        editDashboard(item) {
            this.visible = true
            this.edit = true
            this.form = {...item}
        },
        reInit() {
            if(this.dashboardList.length) {
                this.active = this.dashboardList[0].id
                this.getWidgets()
            }
        },
        deleteDashboard(item) {
            this.$confirm({
                title: this.$t('dashboard.confirm_delete'),
                okText: this.$t('dashboard.delete'),
                okType: 'danger',
                cancelText: this.$t('dashboard.cancel'),
                maskClosable: true,
                mask: true,
                closable: true,
                onOk: async () => {
                    try { 
                        await this.$store.dispatch('dashboard/deleteDashboard', {
                            id: item.id
                        }) 
                        if(this.active === item.id)
                            this.reInit()
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },
        afterClose() {
            this.form = {
                name: '',
                desktop_template: null
            }
            this.edit = false
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        if(this.edit) {
                            const data = await this.$store.dispatch('dashboard/updateDashboard', {
                                form: this.form
                            }) 
                            if(data) {
                                this.$message.success(this.$t('dashboard.updated_success', { d_name: data.name }))
                                this.visible = false
                            }
                        } else {
                            const data = await this.$store.dispatch('dashboard/addDashboard', {
                                form: this.form
                            }) 
                            if(data) {
                                this.$message.success(this.$t('dashboard.created_success', { d_name: data.name }))
                                this.visible = false
                                this.getWidgets()
                            }
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.formLoading = false
                    }
                } else {
                    return false;
                }
            })
        },
        selectWidget() {
            this.$store.commit('dashboard/SET_CATALOG_VISIBLE', true)
        }
    }
}
</script>

<style lang="scss" scoped>
.d_templates{
    &__item{
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        text-align: center;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        cursor: pointer;
        &.active,
        &:hover{
            border-color: var(--blue);
        }
    }
}
.dashboard_list_w{
    display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    left: 50%;
    bottom: 0px;
    transform: translateX(-50%);
    height: 100%;
    width: 100%;
    max-width: calc(100% - 550px);
    @media (min-width: 1500px) {
        max-width: calc(100% - 550px);
    }
}
.dashboard_list_scroll_w{
    position: relative;
    flex: 1;
    min-width: 0;
}
.dashboard_list_scroll{
    max-width: 100%;
    overflow-x: scroll;
    overflow-y: hidden;
    -ms-overflow-style: none;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    &::-webkit-scrollbar{
        display: none;
    }
}
.dashboard_list{
    display: flex;
    align-items: center;
    justify-content: center;
    width: max-content;
    min-width: 100%;
    &__item{
        cursor: pointer;
        margin: 0 15px;
        position: relative;
        .name{
            padding: 18px 0px;
            font-weight: 400;
            font-size: 14px;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            text-align: center;
            opacity: 0.6;
            &:hover{
                opacity: 1;
            }
        }
        &.active{
            .name{
                color: #000;
                opacity: 1;
                &::after{
                    content: "";
                    background: #ff9a01;
                    height: 3px;
                    position: absolute;
                    bottom: 0px;
                    left: 0;
                    width: 100%;
                    border-radius: 1px;
                }
            }
        }
        .actions{
            position: absolute;
            display: flex;
            align-items: center;
            top: 2px;
            right: 0px;
            z-index: 5;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &__item{
                font-size: 10px;
                cursor: pointer;
                background: var(--text);
                height: 18px;
                padding: 0 5px;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                &:last-child{
                    border-radius: 0 18px 18px 0;
                }
                &:first-child{
                    border-radius: 18px 0 0 18px;
                }
                i{
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                }
                &:hover{
                    i{
                        opacity: 0.6;
                    }
                }
            }
            .line{
                background: #f7f9fc;
                height: 18px;
                width: 2px;
            }
            &.one{
                .actions__item{
                    border-radius: 18px;
                }
            }
        }
        &:hover{
            .actions{
                opacity: 1;
            }
        }
    }
}
.scroll_arrow{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    &.left{
        left: -10px;
    }
    &.right{
        right: -10px;
    }
}
.dashboard{
    height: 100%;
    overflow: hidden;
    display: flex;
    width: 100%;
    flex-direction: column;
    &__header{
        padding: 10px 0;
        margin: var(--wrapperMargin);
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--border2);
        background: var(--mBg);
        position: relative;
        h1{
            font-weight: 400;
            font-size: 18px;
            margin: 0px;
        }
    }
    &__body{
        flex-grow: 1;
        overflow: auto;
        padding: 10px 0;
        .ds_spin{
            height: 100%;
            &::v-deep{
                & > div{
                    .ant-spin{
                        max-height: 100%;
                    }
                }
                & > .ant-spin-container{
                    height: 100%;
                }
            }
        }
    }
}
</style>
