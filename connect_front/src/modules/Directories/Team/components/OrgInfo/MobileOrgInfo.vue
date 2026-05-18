<template>
    <a-drawer
        title=""
        :visible="visible"
        class="org_m_info"
        @close="visible = false"
        destroyOnClose
        width="100%"
        placement="right">
        <template v-if="org">
            <div class="drawer_header">
                <div class="flex items-center truncate">
                    <div :key="org.logo" class="pr-2">
                        <a-avatar 
                            :size="30"
                            :src="org.logo"
                            icon="fi-rr-users-alt" 
                            flaticon />
                    </div>
                    <span class="font-semibold truncate">{{ org.name }}</span>
                </div>
                <a-button 
                    type="ui"
                    shape="circle"
                    ghost
                    icon="fi-rr-cross"
                    flaticon
                    @click="visible = false" />
            </div>
            <div class="drawer_body">
                <OrgInfo 
                    :org="org" 
                    :reloadMainList="reloadMainList"
                    :closeDrawer="closeDrawer" 
                    :minusUserCount="minusUserCount" />
            </div>
            <div class="drawer_footer">
                <a-button block type="ui" ghost @click="visible = false">
                    {{ $t('team.close') }}
                </a-button>
            </div>
        </template>
    </a-drawer>
</template>

<script>
import OrgInfo from './index.vue'
export default {
    components: {
        OrgInfo
    },
    props: {
        minusUserCount: {
            type: Function,
            default: () => {}
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visible: false,
            org: null
        }
    },
    methods: {
        openDrawer(org) {
            this.org = org
            this.visible = true
        },
        closeDrawer() {
            this.visible = false
        }
    },
}
</script>

<style lang="scss" scoped>
.org_m_info{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-body{
            height: 100%;
            padding: 0px;
        }
        .drawer_body{
            height: calc(100% - 83px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 15px;
            padding-right: 15px;
        }
        .drawer_header{
            border-bottom: 1px solid #e8e8e8;
            padding: 5px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    }
}
</style>