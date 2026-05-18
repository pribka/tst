<template>
    <div id="content" class="h-full">
        <grid-layout 
            :layout.sync="widgets"
            class="dashboard_grid"
            :class="isDrag && 'grid_drag'"
            :col-num="12"
            :row-height="30"
            :margin="[15, 15]"
            ref="gridlayout"
            :is-draggable="draggable"
            :is-resizable="resizable"
            :vertical-compact="true"
            :responsive="isMobile"
            :use-css-transforms="true"
            @layout-updated="layoutUpdatedEvent"
            @layout-mounted="layoutMountedEvent"
            @layout-ready="layoutReadyEvent"
            @layout-created="layoutCreatedEvent"
            @breakpoint-changed="breakpointChangedEvent">
            <grid-item 
                v-for="item in widgets"
                :key="item.id"
                :static="item.static"
                :x="item.x"
                :y="item.y"
                :w="item.w"
                :h="item.h"
                :i="item.i"
                :minW="item.minW"
                :minH="item.minH"
                :maxW="item.maxW"
                :maxH="item.maxH"
                drag-allow-from=".vue-draggable-handle"
                drag-ignore-from=".no-drag"
                @resize="resizeEvent"
                @resized="resizedEvent"
                @move="moveEvent"
                @moved="movedEvent">
                <WidgetCard :widget="item" />
            </grid-item>
        </grid-layout>
    </div>
</template>

<script>
import { GridLayout, GridItem } from "vue-grid-layout"
import { errorHandler } from '@/utils/index.js'
let timer
export default {
    components: {
        GridLayout,
        GridItem,
        WidgetCard: () => import('./WidgetCard.vue')
    },
    computed: {
        widgets: {
            get() {
                return this.$store.state.dashboard.widgets
            },
            set(val) {
                // console.log(val)
            }
        },
        isMobile() { 
            return this.$store.state.isMobile
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
                
            }
        },
        async breakpointChangedEvent(e, newLayout) {
            if(newLayout.length && this.ready && this.widgetsReady) {
                try {
                    await this.$store.dispatch('dashboard/updateDashboardWidgets', { widgets: newLayout })
                } catch(error) {
                    errorHandler({error})
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
                        await this.$store.dispatch('dashboard/updateDashboardWidgets', { widgets: this.gridlayout.layout })
                    } catch(error) {
                        errorHandler({error})
                    }
                }, 500)
            })
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.$store.commit('dashboard/SET_GRID_LAYOUT', this.gridlayout)
        })
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
            border: 0px;
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