<template>
    <a-drawer
        :title="$t('team.join_organization')"
        :visible="visible"
        class="org_enter_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        placement="right">
        <div class="drawer_body">
            
        </div>
        <div class="drawer_footer">
            <a-button 
                type="primary">
                {{ $t('team.enter') }}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "OrganizationEnterDrawer",
    props: {
        zIndex: {
            type: Number,
            default: 1010
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 600)
                return 600
            else {
                return '100%'
            }
        }
    },
    created() {
        eventBus.$on('enter_organization', () => {
            this.visible = true
        })
    },
    data() {
        return {
            visible: false,
        }
    },
    methods: {
        
    },
    beforeDestroy() {
        eventBus.$off('enter_organization')
    }
}
</script>

<style lang="scss" scoped>
.org_enter_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .drawer_body{
            height: calc(100% - 40px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
}
</style>