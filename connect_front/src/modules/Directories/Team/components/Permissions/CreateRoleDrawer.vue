<template>

    <DrawerTemplate
        :width="drawerWidth"
        destroyOnClose
        :title="drawerTitle"
        @close="closeDrawer"
        v-model="drawerVisible">
        <template>
            <a-form-model
                class="mb-4"
                ref="createForm"
                :rules="rules"
                :model="form">
                <a-form-model-item
                    :label="$t('team.role_name')"
                    prop="name">
                    <a-input
                        v-model="form.name"
                        size="large"
                        :placeholder="$t('team.role_name')" />
                </a-form-model-item>
                <a-form-model-item
                    :label="$t('team.users')"
                    prop="users">
                    <DrawerSelectUser
                        v-model="form.users"
                        size="large"
                        multiple
                        :fromOrganization="organization.id"
    
                        :buttonText="$t('team.select')"
                        :placeholder="$t('team.users')" />
                </a-form-model-item>
                <div 
                    v-for="(item, index) in form.contractor_permissions" 
                    :key="index"
                    class="flex items-center permission_types">
                    <div 
                        class="flex-grow grid md:grid-cols-2 gap-2 md:gap-4">
                        <a-form-model-item
                            :label="$t('team.permission_type')"
                            :prop="'contractor_permissions.' + index + '.permission_type'">
                            <SelectPermissionType
                                v-model="form.contractor_permissions[index].permission_type"
                                size="large"
                                :usedPermissionTypes="usedPermissionTypes"
                                :buttonText="$t('team.select')"
                                :title="$t('team.select_permission_type')"
                                :oldSelected="false"
                                endpoint="contractor_permissions/permission_types/"
                                :placeholder="$t('team.permission_type')" />
                        </a-form-model-item>
                        <a-form-model-item
                            :label="$t('team.additional_conditions')"
                            :prop="'contractor_permissions.' + index + '.aux_conditions'">
                            <SelectAuxConditions
                                v-model="form.contractor_permissions[index].aux_conditions"
                                size="large"
                                multiple
                                :buttonText="$t('team.select')"
                                :title="$t('team.select_additional_conditions')"
                                :oldSelected="false"

                                :disabled="!form.contractor_permissions[index].permission_type"
                                :endpoint="auxConditionsEndpoint(index)"
                                :placeholder="$t('team.additional_conditions')" />
                        </a-form-model-item>
                    </div>
                    <a-button 
                        v-if="form.contractor_permissions.length > 1" 
                        type="ui"
                        ghost
                        icon="minus" 
                        size="large" 
                        class="ml-1" 
                        @click="removeFormPermission(index)" />
                </div>
                <div>
                    <a-button 
                        icon="plus" 
                        type="link" 
                        class="p-0"
                        @click="addPermission">
                        {{ $t('team.add_permission') }}
                    </a-button>
                </div>
            </a-form-model>            
        </template>
        <template #footer>
            <a-button
                size="large"
                @click="submitClickHandler"
                :loading="createLoading"
                type="primary">
                {{ submitButtonText }}
            </a-button>
        </template>
    </DrawerTemplate>

</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'

export default {
    name: 'CreateRoleDrawer',
    components: {
        SelectPermissionType: () => import('./SelectPermissionType'),
        SelectAuxConditions: () => import('./SelectAuxConditions'),
        DrawerSelectUser: () => import('../Drawers/DrawerSelectUser'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    data() {
        return { 
            createLoading: false,
            drawerVisible: false,
            form: {
                name: '',
                users: [],
                contractor_permissions: [
                    {
                        permission_type: null,
                        aux_conditions: []
                    }
                ]
            },
            isEdit: false,
            roleDetail: null,
            roles: [],
            permissionTypes: [],
            columnDefs: [
                {
                    headerName: this.$t('team.column_name'),
                    field: 'name'
                },
            ],
            gridApi: null,
            deleteList: [],
            addList: [],
            editList: []
            
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        drawerTitle() {
            return this.isEdit ? this.$t('team.edit_role') : this.$t('team.create_role')
        },
        drawerWidth() {
            return this.windowWidth > 1024 ? 1024 : this.windowWidth
        },
        organizationLogo() {
            return this.organization?.logo
        },
        usedPermissionTypes() {
            return this.form.contractor_permissions.map(permission => permission.permission_type?.id || null)
        },
        submitButtonText() {
            return this.isEdit ? this.$t('team.save_changes') : this.$t('team.add_role') 
        },
        submitClickHandler() {
            return this.isEdit ? this.editRole : this.createRole
        },  
        rules() {
            const rules = {
                name: [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ],
                users: [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ],
                "contractor_permissions.0.permission_type": [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ],
            }
            return rules
        }
    },
    created() {
        this.getPremissionTypes()
        this.getRoles()
    },
    methods: {
        ...mapActions({
            createRoleAction: 'organization/createRole',
            editRoleAction: 'organization/editRole',
        }),
        onGridReady(params) {
            this.gridApi = params.api;
            this.gridApi.sizeColumnsToFit()
        },
        removeFormPermission(index) {
            // const permissionId = this.form.contractor_permissions?.[index]?.id
            // if(permissionId) {
            //     this.deleteList.push(permissionId)
            // }

            this.form.contractor_permissions.splice(index, 1)
        },
        auxConditionsEndpoint(index) {
            const auxConditionModel = this.form?.contractor_permissions?.[index]
                ?.permission_type?.aux_condition_model
            if(auxConditionModel) {
                return `/app_info/select_list/?model=${auxConditionModel}`
            } 
            return null
        },
        addPermission() {
            this.form.contractor_permissions.push({
                permission_type: null,
                aux_conditions: []
            })
        },
        async getRoles() {
            const params = {
                filters: {
                    contractor: this.organization.id
                }
            }
            const url = `/contractor_permissions/roles/`
            this.$http.get(url, params)
                .then(({ data }) => {
                    this.roles = data.results
                })
        },
        async getDetailRole(roleId) {
            const url = `/contractor_permissions/roles/${roleId}/`
            try {
                const { data } = await this.$http.get(url)
                return data
            } catch(error) {
                console.error(error) 
            }
            return null
        },
        async getPremissionTypes() {
            const url = `contractor_permissions/permission_types/`
            this.$http.get(url)
                .then(({ data }) => {
                    this.permissionTypes = data.results
                })

        },
        async openDrawer({ edit=false, role=null } = {}) {
            this.isEdit = edit
            this.drawerVisible = true
            if(role) {
                const detailRole = await this.getDetailRole(role.id)
                this.roleDetail = detailRole
                this.form = JSON.parse(JSON.stringify(detailRole))
            }
        },  
        closeDrawer() {
            this.isEdit = false
            this.drawerVisible = false

            this.form = {
                name: '',
                users: [],
                contractor_permissions: [
                    {
                        permission_type: null,
                        aux_conditions: []
                    }
                ]
            }
        }, 
        async createRole() {
            const isValid = await this.$refs['createForm'].validate()
            if(isValid) {
                const contractorPermissions = this.form.contractor_permissions.reduce(
                    (permissionList, permissions) => {
                        if(permissions.permission_type) {
                            permissionList.push({
                                permission_type: permissions.permission_type.code,
                                aux_conditions: permissions.aux_conditions.map(item => item.id)
                            })
                        }
                        return permissionList
                    }, [])
                const payload = {
                    name: this.form.name,
                    contractor: this.organization.id,
                    users: this.form.users.map(user => user.id),
                    contractor_permissions: contractorPermissions
                }
                this.createLoading = true
                try {
                    const data = await this.createRoleAction({ 
                        organizationId: this.organization.id,
                        payload: payload
                    })

                    data.permission_types = data.contractor_permissions.map(permission => permission.permission_type.name) || []
                    
                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'create',
                        row: data
                    })
                    this.createLoading = false
                    this.$message.success(this.$t('team.role_created_successfully'))
                    this.closeDrawer()
                } catch(error) {
                    console.error(error)
                    this.$message.error(this.$t('team.failed_to_create_role'))
                } finally {
                    this.createLoading = false
                }
            }
        },
        async editRole() {
            const isValid = await this.$refs['createForm'].validate()
            if(isValid) {
                const oldPermissionIdList = this.roleDetail.contractor_permissions.map(permission => permission.id)
                const permissionIdList = this.form.contractor_permissions.map(permission => permission.id)

                const permissionChanges = {
                    delete: oldPermissionIdList.filter(id => !permissionIdList.includes(id)),
                    edit: [],
                    add: []
                }
                this.form.contractor_permissions.forEach(permission => {
                    if(permission?.id) {
                        permissionChanges.edit.push({
                            id: permission.id,
                            permission_type: permission.permission_type.code,
                            aux_conditions: permission.aux_conditions.map(item => item.id)
                        })
                    } else {
                        permissionChanges.add.push({
                            permission_type: permission.permission_type.code,
                            aux_conditions: permission.aux_conditions.map(item => item.id)
                        })
                    }
                })
                const payload = {
                    name: this.form.name,
                    users: this.form.users.map(user => user.id),
                    contractor_permissions: permissionChanges,
                }
                this.createLoading = true
                try {
                    const data = await this.editRoleAction({ 
                        organizationId: this.organization.id,
                        roleId: this.roleDetail.id,
                        payload: payload
                    })
                    data.permission_types = data.contractor_permissions.map(permission => permission.permission_type.name) || []


                    this.createLoading = false
                    eventBus.$emit(`update_role_with_id_${this.roleDetail.id}`, { updatedRole: data })

                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'update',
                        row: data
                    })
                    this.$message.success(this.$t('team.role_updated_successfully'))
                    this.closeDrawer()
                } catch(error) {
                    console.error(error)
                    this.$message.error(this.$t('team.failed_to_update_role'))
                } finally {
                    this.createLoading = false
                }

                
            }
        }
    }
}
</script>

<style lang="scss" scoped>
$footer-height: 40px;
$header-height: 40px;
$navigation-height: 44px;

.create_role_drawer {
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content {
            overflow: hidden;
            padding: 0px;
        }
        .permission_types {
            .ant-row.ant-form-item {
                @media(max-width: 768px) {
                    margin: 0;
                }
            }
        }
        .permission_types + .permission_types {
            margin-top: 1.5rem;
        }
        .ant-drawer-header-no-title {
            display: none;
        }
        .ant-drawer-body {
            height: 100%;
            padding: 0px;
        }
        .drawer_body {
            $body-height: calc(100% - $footer-height - $header-height);
            height: $body-height;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px;
        }
        .drawer_footer {
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 15px;
            padding-right: 15px;
        }
        .drawer_header {
            height: 40px;
            border-bottom: 1px solid #e8e8e8;
            padding: 5px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    }
}
</style>