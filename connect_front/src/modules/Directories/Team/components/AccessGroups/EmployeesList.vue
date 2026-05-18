<template>
    <div>
        <DrawerSelectUser
            ref="drawerSelectUser"
            v-model="usersToAdd"
            multiple
            buttonMode
            buttonBlock
            buttonSize="large"
            :buttonText="$t('Add employee')"
            :endpoint="getUserEndpoint"
            :accessGroup="accessGroup"
            :fromOrganization="organization.id"
            showAddEmployeeButton
            @userAdded="reload"
            class="mb-4 w-full"
            :title="$t('team.select_employee')" />

        <div class="mb-4">
            <a-input-search
                :placeholder="$t('team.search')"
                v-model="searchText"
                allowClear
                @change="search"/>
        </div>

        <div    
            class="user-list__item"
            v-for="item in employeeList" :key="item.id">
            <div class="flex items-center">
                <Profiler
                    nameClass="text-sm"
                    initStatus                        
                    hideSupportTag
                    :user="item" />
                <template v-if="item.is_org_admin || item.is_support || isAuthor(item.id)">
                    <div class="ml-2">
                        <a-tag 
                            v-if="item.is_org_admin" 
                            color="green" 
                            class="tag tag_custom_margin" >
                            {{ $t('team.admin') }}
                        </a-tag>
                        <a-tag 
                            v-if="item.is_support" 
                            color="green" 
                            class="tag tag_custom_margin" >
                            <i class="fi fi-rr-headset"></i>
                        </a-tag>
                        <a-tag 
                            v-if="isAuthor(item.id)" 
                            color="green" 
                            class="tag tag_custom_margin" >
                            <i class="fi fi-rr-crown"></i>
                        </a-tag>
                    </div>
                </template>
            </div>

            <a-button 
                type="link" 
                v-tippy="{ touch: true }" 
                :content="$t('team.exclude_user')"
                class="text_current ant-btn-icon-only" 
                @click="removeUser(item)">
                <i class="fi fi-rr-remove-user text_red"></i>
            </a-button>
        </div>

        <infinite-loading
            @infinite="getData"
            :identifier="infinityId"
            v-bind:distance="10">
            <div slot="spinner"><a-spin /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import debounce from '@/utils/lodash/debounce'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        DrawerSelectUser: () => import('../Drawers/DrawerSelectUser')
    },
    props: {
        accessGroup: {
            type: Object,
            required: true
        },
        organization: {
            type: Object,
            required: true
        },
        reloadAccessGroupList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        getUserEndpoint() {
            return `users/my_organizations/${this.organization.id}/users/`
        }
    },
    data() {
        return {
            usersToAdd: [],
            pageSizeOptions: ['15', '30', '50'],
            infinityId: new Date(),
            employeeList: [],

            loading: false,
            searchText: '',
            searchStart: false,
            params: {
                page_size: 15,
                page: 1,
            },
            form: {
                user: null
            }
        }
    },
    methods: {
        getData($state) {
            const params = {
                ...this.params,
                text: this.searchText,
                contractor: this.organization.id
            }
            const url =`/contractor_permissions/access_groups/${this.accessGroup.id}/members/`
            this.$http(url, { params })
                .then(({ data }) => {
                    this.employeeList.push(...data.results)
                    if (data?.next) {
                        this.page++
                        $state.loaded();
                    } else {
                        $state.complete();
                    }
                })
                .catch(error => {
                    this.$message.error(this.$t('team.failed_to_get_employee_list'))
                    console.error(error)
                })
        },
        reload() {
            this.page = 1
            this.employeeList.splice(0)
            this.infinityId = new Date()
        },
        showLeaveButton(record) {
            return (this.user?.id === record.id) && !this.actions?.edit
        },
        showRemoveEmployeeButton(record) {
            return !this.isAuthor(record.id) && (this.actions?.edit) && (this.user?.id !== record.id)
        },
        search: debounce(async function() {
            if(this.searchText.length > 1) {
                this.reload()
                setTimeout(() => {
                    this.loading = false
                }, 1000)

            } else{ 
                this.reload()
            }
        }, 500),
        leaveOrg() {
            this.$confirm({
                title: this.$t('team.confirm_leave_organization'),
                okText: this.$t('team.leave'),
                okType: 'danger',
                cancelText: this.$t('team.cancel'),
                closable: true,
                maskClosable: true,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/users/my_organizations/${this.org.id}/leave/`)
                            .then(() => {
                                this.$message.info(this.$t('team.successfully_left_organization'))
                                eventBus.$emit('orgTableReload')
                                resolve(true)
                            })
                            .catch((error) => { 
                                this.$message.error(this.$t('team.error'))
                                reject(error)
                            })
                    })
                }
            })
        },
        removeUser(record) {
            this.$confirm({
                title: this.$t('team.confirm_remove_user_from_access_group'),
                okText: this.$t('team.remove'),
                okType: 'danger',
                cancelText: this.$t('team.cancel'),
                closable: true,
                maskClosable: true,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        const url = `contractor_permissions/access_groups/${this.accessGroup.id}/members/remove/`
                        const payload = {
                            contractor: this.organization.id,
                            members: [ record.id ]
                        }
                        this.$http.post(url, payload)
                            .then(() => {
                                this.reload()
                                resolve(true)
                            })
                            .catch((error) => { 
                                this.$message.error(this.$t('team.deletion_error'))
                                reject(error)
                            })
                    })
                }
            })
        },
        isAuthor(id) {
            return this.org?.director?.id === id
        },
    }
}
</script>


<style lang="scss" scoped>
.user-list__item {
    display: flex;
    padding: 10px 0;
    justify-content: space-between;
    align-items: center;
}
.user-list__item + .user-list__item {
    border-top: 1px solid #e5e5e5;
}
</style>