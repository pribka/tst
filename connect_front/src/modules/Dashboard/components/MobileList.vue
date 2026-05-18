<template>
    <DynamicScroller
        :items="widgets"
        :min-item-size="20"
        class="scroller"
        ref="scroller"
        pageMode
        typeField="id"
        :emit-update="true">
        <template #default="{ item, index, active }">
            <DynamicScrollerItem
                :item="item"
                :active="active"
                watchData
                :size-dependencies="[
                    item.mobile_index
                ]"
                :data-index="index"
                :data-active="active">
                <div class="pb-2">
                    <WidgetCard :widget="item" />
                </div>
            </DynamicScrollerItem>
        </template>
    </DynamicScroller>
</template>

<script>
let timer
const updateKey = 'widgets_update'
import eventBus from '@/utils/eventBus'
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
export default {
    components: {
        DynamicScroller,
        DynamicScrollerItem,
        WidgetCard: () => import('./WidgetCard.vue')
    },
    computed: {
        widgets: {
            get() {
                return [...this.$store.state.dashboard.widgets].sort((a, b) => a.mobile_index - b.mobile_index)
            },
            set(val) {
                
            }
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        gridlayout() {
            return this.$refs.gridlayout
        },
        widgetsReady() {
            return this.$store.state.dashboard.ready
        },
        catalogVisible() {
            return this.$store.state.dashboard.catalogVisible
        },
        colNum() {
            if(this.windowWidth >= 1500) {
                return 12
            } else {
                if(this.windowWidth <= 1324) {
                    return 10
                }
            }
            return 12
        }
    },
    data() {
        return {
            draggable: true,
            resizable: true,
            index: 0,
            ready: false,
            isDrag: false
        }
    },
    methods: {
        layoutUpdatedEvent(widgets) {
            if(this.ready && this.widgetsReady) {
                /*
                clearTimeout(timer)
                timer = setTimeout(async () => {
                    try {
                        this.$message.loading({ content: 'Обновление', key: updateKey })
                        await this.$store.dispatch('dashboard/updateDashboardWidgets', { widgets })
                        this.$message.success({ content: 'Обновлено', key: updateKey, duration: 2 })
                    } catch(e) {
                        console.log(e)
                        this.$message.error({ content: 'Ошибка обновления', key: updateKey, duration: 2 })
                    }
                }, 1000)*/
            }
        },
        async breakpointChangedEvent(e, newLayout) {
            if(newLayout.length && this.ready && this.widgetsReady) {
                try {
                    await this.$store.dispatch('dashboard/updateDashboardWidgets', { widgets: newLayout })
                } catch(e) {
                    console.log(e)
                }
            }
        },
        layoutMountedEvent(e) {
        },
        layoutReadyEvent(e) {
            this.ready = true
        },
        layoutCreatedEvent(e) {
        },
        moveEvent() {
            this.isDrag = true
            clearTimeout(timer)
            if(this.catalogVisible)
                this.$store.commit('dashboard/SET_CATALOG_VISIBLE', false)
        },
        resizeEvent() {
            this.isDrag = true
            clearTimeout(timer)
            if(this.catalogVisible)
                this.$store.commit('dashboard/SET_CATALOG_VISIBLE', false)
        },
        resizedEvent() {
            this.isDrag = false
            this.updateGrid()
        },
        movedEvent() {
            this.isDrag = false
            this.updateGrid()
        },
        updateGrid() {
            this.$nextTick(() => {
                clearTimeout(timer)
                timer = setTimeout(async () => {
                    try {
                        // this.$message.loading({ content: 'Обновление', key: updateKey })
                        await this.$store.dispatch('dashboard/updateDashboardWidgets', { widgets: this.gridlayout.layout })
                        // this.$message.success({ content: 'Обновлено', key: updateKey, duration: 2 })
                    } catch(e) {
                        console.log(e)
                        // this.$message.error({ content: 'Ошибка обновления', key: updateKey, duration: 2 })
                    }
                }, 500)
            })
        },
        scrollDown() {
            this.$nextTick(() => {
                this.$refs.scroller.scrollToItem(this.widgets.length)
            })
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.$store.commit('dashboard/SET_GRID_LAYOUT', this.gridlayout)
        })
        eventBus.$on('scrollDown', () => {
            this.scrollDown()
        })
    },
    beforeDestroy() {
        eventBus.$off('scrollDown')
    }
}
</script>

<style lang="scss" scoped>
.dashboard_grid{
    min-height: 100%;
    &:not(.grid_drag) {
        transition: none;
        &::v-deep{
            .vue-grid-item {
                transition: none;
            }
        }
    }
    &::v-deep{
        .vue-grid-item{
            border: 1px solid var(--border2);
            border-radius: var(--borderRadius);
            background: #ffffff;
            .vue-resizable-handle{
                opacity: 0;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                bottom: 5px;
                right: 5px;
            }
            &:hover{
                .vue-draggable-handle{
                    opacity: 1;
                }
                .vue-resizable-handle{
                    opacity: 1;
                }
            }
        }
        .vue-grid-placeholder{
            background: #eff2f5;
            opacity: 0.7;
            border: 0px;
            border-radius: var(--borderRadius);
            .vue-resizable-handle{
                display: none;
            }
        }
    }
}
</style>