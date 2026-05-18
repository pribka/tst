<template>
    <a-drawer
        :title="null"
        :width="drawerWidth"
        class="create_role_drawer"
        destroyOnClose
        @close="closeDrawer"
        :zIndex="1000"
        :visible="drawerVisible">
        <div class="drawer_header">
            <span class="font-semibold truncate">
                <template v-if="roleDetail">
                    {{ roleDetail.name }}
                </template>
                <template v-else>
                    {{ $t('team.role') }}
                </template>
            </span>
            <a-button 
                type="ui"
                shape="circle"
                ghost
                icon="fi-rr-cross"
                flaticon
                @click="closeDrawer" />
        </div>
        <div class="drawer_body">
            <template v-if="roleDetail">
                <div class="">
                    <div class="grid sm:grid-cols-2 sm:gap-2 mb-2 mr-8 flex-grow">
                        <div class="mb-2 font-semibold">
                            {{ $t('team.right') }}
                        </div>
                        <div>
                            <div 
                                class="mb-4"
                                v-for="permission in roleDetail.contractor_permissions"
                                :key="permission.id">
                                {{ permission.permission_type.name }}
                                <template v-if="permission.aux_conditions.length">
                                    <div class="mt-2 font-semibold">
                                        {{ $t('team.additional_conditions_label') }}
                                    </div>
                                    <div 
                                        v-for="condition in permission.aux_conditions"
                                        :key="condition.id">
                                        - {{ condition.name }}
                                    </div>
                                </template>
                            </div>
                        </div>
                        <div class="mb-2 font-semibold">
                            {{ $t('team.users_label') }}
                        </div>
                        <div class="sm:mt-4">
                            <div   
                                class="mb-2"
                                v-for="user in roleDetail.users"
                                :key="user.id">
                                <Profiler
                                    :avatarSize="32"
                                    nameClass="text-sm"
                                    :user="user" />
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            <template v-else>
                <a-skeleton rows="4" />
            </template>
            <CreateRoleDrawer 
                ref="createRoleDrawer"
                :organization="organization"/>

        </div>
        <div class="drawer_footer">
            <a-button
                class="mr-4"
                type="primary"
                @click="openEditRoleDrawer">
                {{ $t('team.edit') }}
            </a-button>
            <a-button
                type="danger"
                @click="confirmDeleteRole">
                {{ $t('team.delete') }}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'

export default {
    name: 'DetailRoleDrawer',
    components: {
        CreateRoleDrawer: () => import('./CreateRoleDrawer.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true
        },
    },
    data() {
        return { 
            drawerVisible: false,
            roleDetail: null,
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        drawerWidth() {
            return this.windowWidth > 500 ? 500 : this.windowWidth
        },
        organizationLogo() {
            return this.organization?.logo
        },
    },
    beforeDestroy() {
        if(this.roleDetail) {
            eventBus.$off(`update_role_with_id_${this.roleDetail.id}`)
        }
    },
    methods: {
        ...mapActions({
            deleteRole: 'organization/deleteRole',
        }),

        openEditRoleDrawer() {
            this.$refs.createRoleDrawer.openDrawer({
                edit: true,
                role: this.roleDetail,
            })
        },
        confirmDeleteRole() {
            const role = this.roleDetail
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
                    self.closeDrawer()
                },
                onCancel() {},
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
        async openDrawer({ role } = {}) {
            this.drawerVisible = true
            if(role) {
                const detailRole = await this.getDetailRole(role.id)
                this.roleDetail = detailRole

                eventBus.$on(`update_role_with_id_${this.roleDetail.id}`, ({ updatedRole }) => {
                    this.roleDetail = updatedRole
                })
            }
        },  
        closeDrawer() {
            this.isEdit = false
            this.drawerVisible = false
        },  
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