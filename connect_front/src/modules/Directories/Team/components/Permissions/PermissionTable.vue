<template>
    <div class="h-full flex flex-col">
        <div class="mb-4">
            <a-button 
                type="primary" 
                icon="plus"
                class="mr-2"
                size="large"
                @click="openCreateRoleDrawer">
                {{ $t('team.add_role') }}
            </a-button>
            <CreateRoleDrawer 
                ref="createRoleDrawer"
                :pageName="pageName"
                :organization="organization"/>
        </div>
        <UniversalTable 
            :endpoint="endpoint"
            :params="queryParams"
            :pageName="pageName"
            :model="model"
            tableType="roles"
            autoHeight
            :openHandler="openRoleDetailDrawer"
            :organization="organization" />
        
        <RoleDetailDrawer
            :organization="organization"
            ref="roleDetailDrawer" />
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex';

export default {
    name: 'ThePermissions',
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
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
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            sort: '',
            count: 0,
            pageName: 'role_list',
            columnDefs: [
                {
                    headerName: this.$t('team.column_name'),
                    field: 'name'
                },
            ],
            rowData: [],

            columns: [
                {
                    dataIndex: 'name',
                    title: this.$t('team.column_name'),
                    key: 'name',
                    scopedSlots: { customRender: 'name' }
                },
                {   
                    width: 100,
                    dataIndex: 'actions',
                    title: '',
                    key: 'actions',
                    scopedSlots: { customRender: 'actions' }
                },
            ],
            tableLoading: false,
            gridApi: null
        }
    },
    computed: {
        ...mapState({
            roles: state => state.organization.roles,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
            
        }),
        queryParams() {
            return {
                filters: {
                    contractor: this.organization.id
                }
            }
        },
        model() {
            return 'ContractorPermissionRoleModel'
        },
        roleList() {
            return this.roles?.[this.organization.id]?.results || []
        },

        roleCount() {
            return this.roles?.[this.organization.id]?.count
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        endpoint() {
            return `/contractor_permissions/roles/`
        }

        
    },
    created() {
        this.getRoleList()
    },    
    methods: {
        ...mapActions({
            getRoles: 'organization/getRoles',
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
        changePage(page) {
            this.page = page
            this.getRoleList()
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
        async getRoleList() {
            let params = {
                page: this.page,
                page_size: this.pageSize,
                page_name: this.pageName,
                filters: {
                    contractor: this.organization.id
                }
            }

            this.tableLoading = true
            try {

                this.getRoles({ 
                    params: params,
                    organizationId: this.organization.id,
                })
            } catch(error) {
                console.error(error)
                this.$message.error(this.$t('team.failed_to_get_data'))
            } finally {
                this.tableLoading = false
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
            // this.rowData.push({ name: 1234})
            this.$refs.createRoleDrawer.openDrawer()
            // const query = JSON.parse(JSON.stringify(this.$route.query))
            // query.tab = 'create_role'
            // await this.$router.replace({ query })
        }
    }
}
</script>

<style>
</style>