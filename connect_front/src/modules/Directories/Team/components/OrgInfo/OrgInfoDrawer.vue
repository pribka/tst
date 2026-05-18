<template>
    <a-drawer
        title=""
        :visible="visible"
        class="org_m_info"
        @close="visible = false"
        destroyOnClose
        :width="drawerWidth"
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
            <template>
                <a-tabs 
                    default-active-key="employees" 
                    @change="0">
                    <a-tab-pane 
                        key="employees" 
                        :tab="$t('team.employees')" />
                    <a-tab-pane 
                        key="permissions" 
                        :tab="$t('team.access_rights')" />
                </a-tabs>
            </template>
            <div class="drawer_body">
                <OrgInfo 
                    :org="org" 
                    :isAdmin="isAdmin"
                    :parentId="parentId"
                    :isDepartment="isDepartment"
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
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
// import PageFilter from '@/components/PageFilter'
export default {
    components: {
        // PageFilter,
        OrgInfo: () => import('./index.vue')
    },
    props: {
        minusUserCount: {
            type: Function,
            default: () => {}
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        },
        page_name: {
            type: String,
            default:'orgInfoDrawer'
        }
    },
    data() {
        return {
            visible: false,
            org: null,
            isDepartment: false,
            parentId: null,
            isAdmin: false
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
        }),
        drawerWidth() {
            if(this.windowWidth > 900)
                return 900
            else if(this.windowWidth < 800 && this.windowWidth > 500)
                return this.windowWidth - 30
            else
                return this.windowWidth
        },
    },
    methods: {
        openDrawer(org) {
            this.org = org
            this.visible = true
        },
        closeDrawer() {
            this.visible = false
        },
    },
    mounted() {
        eventBus.$on('open_organization_drawer_view', ({ 
            organization, 
            isDepartment,
            parentId=null,
            isAdmin=false
        }) => {
            this.isDepartment = isDepartment
            this.parentId = parentId
            this.isAdmin = isAdmin

            this.openDrawer(organization)
        })
    },
    beforeDestroy() {
        eventBus.$off('open_organization_drawer_view')
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
        // .ant-tabs-bar {
        //     margin-bottom: 0;
        // }
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