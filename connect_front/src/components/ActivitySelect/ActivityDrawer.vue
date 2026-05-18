<template>
    <a-drawer
        placement="bottom"
        :visible="visible"
        class="activity_views"
        height="auto"
        :zIndex="zIndex"
        closable
        :afterVisibleChange="afterVisibleChange"
        destroyOnClose
        :getContainer="getContainer"
        @close="closeDrawer()">
        <div class="drawer_handler" @click="closeDrawer()">
            <div class="handler_item"></div>
        </div>
        <div class="drawer_body" @click="handleBodyClick">
            <slot />
        </div>
        <div class="drawer_footer">
            <a-button 
                type="ui_ghost" 
                block 
                size="large" 
                @click="closeDrawer()">
                Закрыть
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import { v1 as uuidv1 } from 'uuid'
export default {
    name:'ActivityDrawer',
    props: {
        value: {
            type: Boolean,
            default: false
        },
        hardZIndex: {
            type: Number,
            default: null,
        },
        vis: {
            type: Boolean,
            default: false
        },
        useVis: {
            type: Boolean,
            default: false
        },
        visibleChange: {
            type: Function,
            default: () => {}
        },
        cDrawer: {
            type: Function,
            default: () => {}
        },
        closeOnBodyClick: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        visible: {
            get() {
                return this.value || this.vis
            },
            set(val) {
                this.$emit('input', val)
            }
        },
        zIndex() {
            if (this.hardZIndex) { return this.hardZIndex }

            const openDrawers = this.$store.state.openDrawers
            const currentDrawer = openDrawers.find(drawer => drawer.uid === this.drawerUid)
            return currentDrawer?.zIndex || openDrawers?.[openDrawers.length-1]?.zIndex + 100 || 1000
        },
        getContainer() {
            return () => document.body
        }
    },
    data() {
        return {
            drawerUid: uuidv1()
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                this.$store.commit('PUSH_OPEN_DRAWERS', this.drawerUid)
            } else {
                this.$store.commit('REMOVE_OPEN_DRAWERS', this.drawerUid)
            }
            this.$nextTick(() => {
                this.$emit('afterVisibleChange', vis)
            })
            this.visibleChange(vis)
        },
        closeDrawer() {
            if(this.useVis) {
                this.cDrawer()
            } else {
                this.visible = false
            }
        },
        handleBodyClick() {
            if (this.closeOnBodyClick) {
                this.visible = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.drawer_footer{
    padding-bottom: 10px;
}
.drawer_handler{
    height: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    .handler_item{
        background: #888;
        height: 5px;
        width: 50px;
        border-radius: 5px;
        opacity: 0.5;
    }
}
.drawer_body{
    flex-grow: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding-top: 5px;
    padding-bottom: 10px;
}
</style>

<style lang="scss">
$fullscreen: calc(var(--vh, 1vh) * 100);
.activity_views{
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
    .ant-drawer-wrapper-body,
    .ant-drawer-content{
        overflow: hidden;
        height: 100%;
    }
    .ant-drawer-content-wrapper{
        max-height: calc(95% - constant(safe-area-inset-top) - constant(safe-area-inset-bottom));
        max-height: calc(95% - env(safe-area-inset-top) - env(safe-area-inset-bottom));
    }
    &.ant-drawer-bottom{
        &.ant-drawer-open{
            .ant-drawer-content-wrapper{
                box-shadow: none;
            }
        }
    }
    .ant-drawer-content{
        background: transparent;
        user-select: none;
    }
    .ant-drawer-header-no-title{
        display: none;
    }
    .ant-drawer-body{
        display: flex;
        flex-direction: column;
        max-height: calc($fullscreen - 40px) !important;
        padding-left: 0px;
        padding-right: 0px;
        padding-top: 0px;
        background: #fff;
        border-radius: 12px 12px 0px 0px;
        -webkit-user-select: none;
        -khtml-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        overflow: hidden;
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        padding-bottom: calc(10px + var(--safe-area-inset-bottom));
        li{
            list-style: none;
            &:not(.activity_item){
                &:not(:last-child){
                    margin-bottom: 10px;
                }
            }
        }
    }
}
</style>
