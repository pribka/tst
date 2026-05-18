<template>
    <div class="h-full flex flex-col">
        <!-- <div class="mb-4">
            <a-button 
                type="primary" 
                icon="plus"
                class="mr-2"
                size="large"
                @click="openCreateRoleDrawer">
                Добавить роль
            </a-button>
        </div> -->
        <CreateRoleDrawer 
            ref="createRoleDrawer"
            :organization="organization"/>
        <RoleCard 
            v-for="item in roleList"
            :key="item.id"
            class="custom_card_margin"
            :organization="organization"
            :role="item"/>
        <infinite-loading 
            ref="org_user_infinity"
            @infinite="getRoleList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <template v-if="!roleNext && roleList && !roleList.length">
            <a-empty :description="$t('team.no_data')" />
        </template>
        <RoleDetailDrawer
            :organization="organization"
            ref="roleDetailDrawer" />
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex';

export default {
    name: 'RoleList',
    components: {
        RoleCard: () => import("./RoleCard"),
        InfiniteLoading: () => import('vue-infinite-loading'),
        RoleDetailDrawer: () => import("./RoleDetailDrawer"),
        CreateRoleDrawer: () => import("./CreateRoleDrawer")
    },
    props: {
        organization: {
            type: Object,
            required: true
        },
    },
    data() {
        return { 
            page: 0,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            sort: '',
            count: 0,
            infiniteId: 'org_users_list',

            pageName: 'role_list',
            
            loading: false,
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
            infiniteRoles: state => state.organization.infiniteRoles
        }),
        roleList() {
            return this.infiniteRoles?.[this.organization.id]?.results || []
        },
        roleNext() {
            return this.infiniteRoles?.[this.organization.id]?.next !== null
        },
        // roleCount() {
        //     return this.roles?.[this.organization.id]?.count
        // },
    },
    methods: {
        ...mapActions({
            getInfiniteRoles: 'organization/getInfiniteRoles',
            deleteRole: 'organization/deleteRole',
        }),
        openRoleDetailDrawer(role) {
            this.$refs.roleDetailDrawer.openDrawer({
                role: role
            })
        },
        openEditRoleDrawer(role) {
            this.$refs.createRoleDrawer.openDrawer({
                edit: true,
                role: role,
            })
        },
        confirmDeleteRole(role) {
            const self = this
            this.$confirm({
                title: this.$t('team.confirm_delete_role'),
                content: '',
                okText: this.$t('team.yes'),
                cancelText: this.$t('team.no'),
                onOk() {
                    self.deleteRole({
                        roleId: role.id,
                        organizationId: self.organization.id
                    })
                },
                onCancel() {},
            })
        },
        async getRoleList($state) {
            if(!this.roleNext) {
                return $state.complete()
            }
            let params = {
                page: this.page + 1,
                page_size: this.pageSize,
                page_name: this.pageName,
                filters: {
                    contractor: this.organization.id
                }
            }
            if(!this.loading && this.roleNext) {
                this.loading = true
                try {
                    const data = await this.getInfiniteRoles({ 
                        params: params,
                        organizationId: this.organization.id,
                    })
                    if(data.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    console.error(error)
                    this.$message.error(this.$t('team.failed_to_get_data'))
                } finally {
                    this.loading = false
                }
            }
        },
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getRoleList()
        },
        onGridReady(params) {
            this.gridApi = params.api;
            this.gridApi.sizeColumnsToFit()
        },
        async getDetailRole() {
            const roleId = ''
            const url = `/contractor_permissions/roles/${roleId}/`
            
            await this.$http.get(url)
                .then(({ data }) => {
                    this.roles = data.results
                })
        },
        async openCreateRoleDrawer() {
            this.$refs.createRoleDrawer.openDrawer()
        }
    }
}
</script>

<style lang="scss" scoped>
.custom_card_border {
    border-radius: var(--borderRadius);
    border: 1px solid var(--border1);
}
.custom_card_margin:not(:last-child) {
    margin-bottom: 0.625rem;
}
</style>