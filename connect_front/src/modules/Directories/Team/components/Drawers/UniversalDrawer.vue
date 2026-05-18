<template>
    <DrawerTemplate
        v-model="drawerVisible"
        :title="null"
        :width="drawerWidth"
        class="statistics_drawer"
        :class="showNavigation && 'navigation_active'"
        destroyOnClose
        @close="closeDrawer">
        <template #rightHeader>
            <a-button
                v-if="canEditOrganization"
                type="ui"
                ghost
                v-tippy
                :content="$t('edit')"
                icon="fi-rr-edit"
                shape="circle"
                flaticon
                @click="openEditOrganization" />
        </template>
        <template #title>
            <template v-if="isHeaderReady">
                <div class="flex items-center truncate">
                    <div 
                        :key="organizationLogo" 
                        class="mr-2">
                        <a-avatar 
                            :size="30"
                            :src="organizationLogo"
                            icon="fi-rr-users-alt" 
                            flaticon />
                    </div>
                    <span class="font-semibold truncate">{{ drawerTitle }}</span>
                </div>
            </template>
            <template v-else>
                <div class="flex items-center flex-grow">
                    <div class="mr-2">
                        <a-avatar 
                            class="custom_avatart_skeleton"
                            :size="30" />
                    </div>
                    <div class="custom_header_skeleton"></div>
                </div>
            </template>
        </template>
        <template #tabs>
            <div class="drawer_navigation">
                <template v-if="isDetailPage">
                    <a-tabs 
                        default-active-key="" 
                        v-model="activeTab"
                        @change="changeActiveTab">
                        <a-tab-pane 
                            key="employees" 
                            :tab="$t('team.employees')" />
                        <!-- <a-tab-pane 
                            key="permissions" 
                            tab="Роли" /> -->
                        <template v-if="canEditOrganization">
                            <a-tab-pane 
                                key="access_groups" 
                                :tab="$t('Access groups')" />
                        </template>
                    </a-tabs>
                </template>
            </div>
        </template>
        <div>
            <template v-if="isBodyReady">
                <component 
                    :is="widget"
                    :organization="organization"
                    :org="organization" 
                    :isAdmin="isAdmin"
                    :parentId="parentId"
                    :isDepartment="isDepartment"/>
            </template>
            <template v-else>
                <div class="w-full flex justify-center pt-8">
                    <a-spin />
                </div>
            </template>
        </div>
        <template #footer v-if="activeTab === 'permissions' && isMobile">
            <a-button 
                type="primary" 
                icon="plus"
                block
                class="mr-2"
                size="large"
                @click="openCreateRoleDrawer">
                {{ $t('team.add_role') }}
            </a-button>
            <CreateRoleDrawer 
                ref="createRoleDrawer"
                :organization="organization"/>
        </template>
    </DrawerTemplate>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        CreateRoleDrawer: () => import('../Permissions/CreateRoleDrawer.vue'), 
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    data() {
        return {
            drawerVisible: false,
            component: null,
            organization: null,
            organizationId: null,
            parentId: null,
            isDepartment: false,
            organizationLoading: false,
            actions: null,
            isAdmin: false,
            activeTab: 'employees'
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile,
        }),
        drawerTitle() {
            return this.organization?.name || this.$t('team.organization')
        },
        drawerWidth() {
            return this.windowWidth > 1024 ? 1024 : this.windowWidth
        },
        organizationLogo() {
            return this.organization?.logo
        },
        isDetailPage() {
            return this.component === 'detail'
        },
        canEditOrganization() {
            return this.actions?.edit?.availability
        },
        showNavigation() {
            return this.с && this.actions?.edit
        },
        widget() {
            if(this.component === 'statistics')
                return () => import('../Statistics/TheStatistics.vue')
            if(this.isDetailPage) {
                const components = {
                    employees: () => import('../OrgInfo/index.vue'),
                    permissions: () => import('../Permissions/index.vue'),
                    access_groups: () => import('../AccessGroups/index.vue')
                }
                return components[this.activeTab]
            }
            return null
        },
        isBodyReady() {
            return this.widget && this.organization && !this.organizationLoading
        },
        isHeaderReady() {
            return this.organization && !this.organizationLoading
        }
    },
    watch: {
        '$route.query': {
            immediate: true,
            async handler(query, prevQuery = {}) {
                const components = [
                    'statistics',
                    'detail'
                ]
                if(components.includes(query.organization_drawer) && query.organization_id) {
                    this.activeTab = query.tab || 'employees'
                    this.openDrawer()

                    const nextOrganizationId = query.organization_id
                    const nextParentId = query.parent_id || null
                    const nextIsDepartment = query.is_department === 'true'
                    const nextComponent = query.organization_drawer

                    const shouldRefetch =
                        String(prevQuery.organization_id || '') !== String(nextOrganizationId || '') ||
                        String(prevQuery.parent_id || '') !== String(nextParentId || '') ||
                        String(prevQuery.is_department || '') !== String(query.is_department || '') ||
                        String(prevQuery.organization_drawer || '') !== String(nextComponent || '') ||
                        !this.organization

                    this.organizationId = nextOrganizationId
                    this.parentId = nextParentId
                    this.isDepartment = nextIsDepartment
                    this.component = nextComponent

                    if (shouldRefetch) {
                        this.organizationLoading = true
                        this.getOrganizationDetail(nextOrganizationId)
                        this.getActions(nextOrganizationId)
                    }
                } else {
                    this.closeDrawer()
                }
            }
        }
    },
    methods: {
        openEditOrganization() {
            if(!this.canEditOrganization || !this.organization) return

            eventBus.$emit('edit_organization', {
                organization: this.organization,
                organizationParent: this.parentId,
                organizationType: this.parentId && !this.isDepartment ? 'subdivision' : null,
                isDepartment: this.isDepartment
            })
        },
        handleOrganizationUpdated(data) {
            if(!this.drawerVisible || !this.organizationId) return
            if(data?.id && String(data.id) !== String(this.organizationId)) return

            this.organizationLoading = true
            this.getOrganizationDetail(this.organizationId)
            this.getActions(this.organizationId)
        },
        async openCreateRoleDrawer() {
            this.$refs.createRoleDrawer.openDrawer()
        },
        async changeActiveTab(tab) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.tab = tab
            await this.$router.replace({ query })
        },  
        getOrganizationDetail(organizatonId) {
            const url = this.isDepartment ? `/users/my_organizations/departments/${organizatonId}/detail/` 
                : `/users/my_organizations/${organizatonId}/detail/`
            this.$http(url)
                .then(({ data }) => {
                    this.organization = data 
                })
                .catch(error => {
                    if(error?.status === 403) {
                        this.closeDrawer()
                    }
                    errorHandler({error})
                })
                .finally(() => {
                    this.organizationLoading = false
                })
        },
        async getActions(organizationId) {
            try {
                this.actionLoading = true
                const organization = this.isDepartment ? this.parentId : organizationId
                const { data } = await this.$http.get(`/users/my_organizations/${organization}/action_info/`)
                if(data?.actions)
                    this.actions = data.actions
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.actionLoading = false
            }
        },
        closeDrawer() {
            this.drawerVisible = false
            this.organizationId = null
            this.clearQuery()
        },
        openDrawer() {
            this.drawerVisible = true
        },
        async clearQuery() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            delete query.organization_id
            delete query.parent_id
            delete query.is_department
            delete query.organization_drawer
            await this.$router.replace({ query })
        },
    },
    created() {
        eventBus.$on('updateTableOrg', this.handleOrganizationUpdated)
    },
    beforeDestroy() {
        eventBus.$off('updateTableOrg', this.handleOrganizationUpdated)
    }
}
</script>

<style lang="scss" scoped>
$footer-height: 48px;
$header-height: 40px;
$navigation-height: 44px;

.custom_header_skeleton {
    height: 1rem;
    background-color: #f2f2f2;
    width: 38%;
}
.custom_avatart_skeleton {
    flex-shrink: 0;
}
.statistics_drawer.navigation_active {
    &::v-deep{
        .drawer_body {
            $body-height: calc(100% - $footer-height - $header-height - $navigation-height);
            height: $body-height;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px;
        }
    }
}
</style>
