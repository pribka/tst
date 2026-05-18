<template>
    <div>
        <a-button
            size="large"
            shape="circle"
            type="primary"
            flaticon
            icon="fi-rr-align-justify"
            class="drawer_open_button"
            @click="openDrawer" />
        <a-drawer
            title="Категории"
            placement="bottom"
            class="product_categories_drawer"
            :visible="visible"
            :zIndex="1000"
            :destroyOnClose="false"
            @close="closeDrawer">
            <div class="drawer_wrapper">
                <div class="drawer_body">
                    <div 
                        v-if="loading" 
                        class="loading" >
                        <a-spin size="small" />
                    </div>
                    <div 
                        v-else
                        class="menu">
                        <AccordionMenu 
                            :selectMobileEl="selectMobileEl"
                            :onExpand="onExpand"
                            :menuItem="list"
                            :expandedKeys="expandedKeys"
                            :selectedKeys="selectedKeys"
                            :activeEl="activeEl"/>
                    </div>
                </div>
                <div class="drawer_footer">
                    <a-button
                        type="primary"
                        block
                        @click="closeDrawer">
                        {{$t('close')}}
                    </a-button>
                </div>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import AccordionMenu from "./AccordionMenu.vue" 
export default {
    props: {
        list: {
            type: [Array, Object],
            default: () => {}    
        },
        loading: {
            type: Boolean,
            default: false
        },
        expandedKeys: {
            type: Array,
            default: () => []

        },
        selectedKeys: {
            type: Array,
            default: () => []
        },
        activeEl: {
            type: Array,
            default: () => []
        },
        mainCategory: {
            type: Boolean,
            default: true
        },
        onExpand: {
            type: Function,
            default: () => {}
        },
        selectMobileEl: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visible: false
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    components: {
        AccordionMenu
    },
    methods: {
        openDrawer() {
            this.visible = true
        },
        closeDrawer() {
            this.visible = false
        }
    }
}
</script>

<style lang="scss" scoped>
    .loading {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 100%;
    }
    .drawer_open_button {
        display: flex;
        justify-content: center;
        align-items: center;
    
        line-height: 100%;
    }
    .drawer_wrapper{
        height: calc(100vh - 40px);
    }
    .drawer_body{
        height: calc(100vh - 90px);
        overflow-x: hidden;
        overflow-y: scroll;
    }
    .drawer_footer {
        height: 50px;
        padding: 8px 15px;

        border-top: 1px solid var(--borderColor);
    }
</style>

<style lang="scss">
.product_categories_drawer {
    .ant-drawer-content-wrapper {
        height: 100% !important;
    }
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        overflow-x: hidden;
    }

}    
</style>