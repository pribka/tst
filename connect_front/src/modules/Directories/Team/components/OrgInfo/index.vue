<template>
    <div>
        <template v-if="loading">
            <div class="flex justify-center">
                <a-spin size="small" />
            </div>
        </template>
        <template v-else>
            <div 
                v-if="actions && actions.invite" 
                :class="[!isMobile && 'flex items-center']"
                class="mb-4">
                <div class="w-full flex justify-between items-start flex-col-reverse sm:flex-row">
                    <div>
                        <template v-if="!isDepartment">
                            <div class="mb-2">
                                <i class="fi fi-rr-user-add mr-1"></i>
                                <span>
                                    {{ $t('team.invite_new_users_by') }} 
                                </span>
                                <span 
                                    class="blue_color cursor-pointer"
                                    @click="openInvite('email')">
                                    E-mail
                                </span>
                                <span>
                                    {{ $t('team.or_by') }} 
                                </span>
                                <span 
                                    class="blue_color cursor-pointer"
                                    @click="openInvite('link')">
                                    {{ $t('team.link') }}
                                </span>
                            </div>
                        </template>
                        <div>
                            <span class="blue_color cursor-pointer">
                                <i class="fi fi-rr-user-add mr-1"></i>
                                <span @click="openAddEmployeesDrawer()">
                                    {{ $t('team.add_existing_users') }}
                                </span>
                            </span>
                        </div>
                    </div>
                    <template v-if="!isDepartment">
                        <div class="mb-2 sm:mb-0">
                            <span
                                class="blue_color cursor-pointer"
                                @click="openInviteList()">
                                <i class="fi fi-rr-comment-alt-check mr-1"></i>
                                <span>{{ $t('team.invitation_list') }}</span>
                            </span>
                        </div>
                    </template>
                </div>
            </div>
        </template>
        <div>
            <component 
                :is="userComponent" 
                :parentId="parentId"
                :isAdmin="isAdmin"
                :org="org" 
                :actions="actions"
                :isDepartment="isDepartment"
                :closeDrawer="closeDrawer"
                :page_name="page_name"
                :model="model"
                :reloadMainList="reloadMainList"
                :minusUserCount="minusUserCount" 
                :updateTableRowsHeight="updateTableRowsHeight" />
        </div>
        <!-- <a-tabs :type="isMobile ? 'line' : 'card'">
                <a-tab-pane key="1" tab="Сотрудники">
                    <component 
                        :is="userComponent" 
                        :org="org" 
                        :actions="actions"
                        :closeDrawer="closeDrawer"
                        :reloadMainList="reloadMainList"
                        :minusUserCount="minusUserCount" 
                        :updateTableRowsHeight="updateTableRowsHeight" />
                </a-tab-pane>
                <a-tab-pane key="2" tab="Организации">
                    <component 
                        :is="orgComponent" 
                        :actions="actions"
                        :reloadMainList="reloadMainList"
                        :org="org"  />
                </a-tab-pane>
            </a-tabs> -->
        <InvitationList :org="org" />

        <DrawerSelectUser
            ref="drawerSelectUser"
            v-model="usersToAdd"
            multiple
            hide
            :endpoint="getUserEndpoint"
            :isDepartment="isDepartment"
            showAddEmployeeButton
            :parentId="parentId"
            :organizationId="org.id"
            :title="$t('team.select_employee')" />
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        InvitationList: () => import('../InvitationList'),
        DrawerSelectUser: () => import('../Drawers/DrawerSelectUser')
    },
    props: {
        org: {
            type: [Object],
            required: true
        },
        minusUserCount: {
            type: Function,
            default: () => {}
        },
        updateTableRowsHeight: {
            type: Function,
            default: () => {}
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
        isAdmin: {
            type: Boolean,
            default: false
        },
        parentId: {
            type: String,
            default: null
        }
        
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        userComponent() {
            if(this.isMobile) 
                return () => import('./UserList.vue')
            else
                return () => import('./UserTable.vue')
        },
        orgComponent() {
            if(this.isMobile) 
                return () => import('./OrgList/ListMobile.vue')
            else
                return () => import('./OrgList')
        },
        getUserEndpoint() {
            return '/user/list/'
        }
    },
    created() {
        this.getActions()
    },
    data() {
        return {
            sort: '',
            actions: null,
            loading: false,
            model: 'users.ProfileModel',
            page_name: 'orgInfoDrawer',
            usersToAdd: []
        }
    },
    methods: {
        openAddEmployeesDrawer() {
            this.$refs.drawerSelectUser.open()
        },
        orgCopyId() {
            try {
                navigator.clipboard.writeText(this.org.id)
                this.$message.success(this.$t('team.organization_id_copied'))
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('team.error'))
            }
        },
        openOrgInvite() {
            eventBus.$emit('invite_organization', this.org)
        },
        openOrgEnter() {
            eventBus.$emit('enter_organization')
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    const organization = this.isDepartment ? this.parentId : this.org.id
                    const { data } = await this.$http.get(`/users/my_organizations/${organization}/action_info/`)
                    if(data?.actions) {
                        this.actions = data.actions
                    } 
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        openInvite(inviteType) {
            eventBus.$emit('open_invite', { 
                organizationId: this.org.id,
                inviteType: inviteType
            })
        },
        openInviteList() {
            eventBus.$emit(`open_inv_list_${this.org.id}`, this.org.id)
        },
    }
}
</script>