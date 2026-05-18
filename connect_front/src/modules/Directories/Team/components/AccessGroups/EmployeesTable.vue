<template>
    <div>
        <DrawerSelectUser
            ref="drawerSelectUser"
            v-model="usersToAdd"
            multiple
            buttonMode
            buttonSize="large"
            :buttonText="$t('Add employee')"
            :accessGroup="accessGroup"
            :fromOrganization="organization.id"
            showAddEmployeeButton
            :endpoint="getUserEndpoint"
            @userAdded="reloadList"
            class="mb-4"
            :title="$t('team.select_employee')" />

        <div class="mb-4">
            <a-input-search
                :placeholder="$t('team.search')"
                v-model="searchText"
                allowClear
                size="large"
                @change="search"/>
        </div>
        <a-table
            :columns="columns"
            :pagination="false"
            class="org_user_table flex flex-col"
            :loading="loading"
            :locale="{
                emptyText: $t('team.no_data')
            }"
            :row-key="record => record.id"
            :data-source="employees.results">
            <template slot="first_name" slot-scope="text, record">
                {{ record.id }}
            </template>
            <template
                slot="full_name"
                slot-scope="text, record">
                <div class="flex items-center">
                    <Profiler
                        :user="record"
                        initStatus
                        hideSupportTag
                        :avatarSize="28" />
                    <template v-if="record.is_org_admin || record.is_support || isAuthor(record.id)">
                        <div class="ml-2">
                            <a-tag 
                                v-if="record.is_org_admin" 
                                color="green" 
                                class="tag tag_custom_margin" >
                                {{ $t('team.admin') }}
                            </a-tag>
                            <a-tag 
                                v-if="record.is_support" 
                                color="green" 
                                class="tag tag_custom_margin" >
                                <i class="fi fi-rr-headset"></i>
                            </a-tag>
                            <a-tag 
                                v-if="isAuthor(record.id)" 
                                color="green" 
                                class="tag tag_custom_margin" >
                                <i class="fi fi-rr-crown"></i>
                            </a-tag>
                        </div>
                    </template>
                </div>
            </template>
            <template
                slot="email"
                slot-scope="text, record">
                <i class="fi fi-rr-envelope"></i>
                <a :href="`mailto:${record.email}`">
                    {{ record.email }}
                </a>
            </template>         
            <template
                slot="last_activity"
                slot-scope="text, record">
                <template v-if="record.last_activity">
                    <span></span>
                    {{ $moment(record.last_activity).format('DD.MM.YYYY HH:mm') }}
                </template>
            </template>
            <template
                slot="id"
                slot-scope="text, record">
                <a-button 
                    type="link" 
                    v-tippy="{ touch: false }" 
                    :content="$t('team.exclude_user')"
                    class="text_current ant-btn-icon-only" 
                    @click="removeUser(record)">
                    <i class="fi fi-rr-remove-user text_red"></i>
                </a-button>
            </template>
        </a-table>

        <div class="flex justify-end pt-1">
            <a-pagination
                :current="params.page"
                class="pager_wrapper"
                :show-size-changer="pageSizeOptions.length > 1"
                :page-size.sync="params.page_size"
                :defaultPageSize="Number(params.page_size)"
                :pageSizeOptions="pageSizeOptions"
                :total="employees.count"
                show-less-items
                @showSizeChange="sizeSwicth"
                @change="changePage">
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div>
    </div>
</template>

<script>
import debounce from '@/utils/lodash/debounce'
import eventBus from '@/utils/eventBus'
export default {
    components: {
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

            columns: [
                {
                    dataIndex: 'full_name',
                    title: this.$t('team.full_name_short'),
                    key: 'full_name',
                    scopedSlots: { customRender: 'full_name' }
                },
                {
                    dataIndex: 'email',
                    title: 'E-mail',
                    key: 'email',
                    scopedSlots: { customRender: 'email' }
                },
                {
                    dataIndex: 'job_title',
                    title: this.$t('team.position'),
                    key: 'job_title',
                    scopedSlots: { customRender: 'job_title' }
                },
                {
                    dataIndex: 'last_activity',
                    title: this.$t('team.last_activity'),
                    key: 'last_activity',
                    scopedSlots: { customRender: 'last_activity' }
                },
                {
                    dataIndex: 'id',
                    title: '',
                    key: 'id',

                    scopedSlots: { customRender: 'id' }
                },
            ],
            loading: false,
            searchText: '',
            searchStart: false,
            employees: {
                results: [],
                count: 0
            },
            params: {
                page_size: 15,
                page: 1,
            },
            form: {
                user: null
            }
        }
    },
    created() {
        this.getEmployeeList()
    },
    methods: {
        getEmployeeList() {
            const params = {
                ...this.params,
                text: this.searchText,
                contractor: this.organization.id
            }
            const url =`/contractor_permissions/access_groups/${this.accessGroup.id}/members/`
            this.loading = true
            return this.$http(url, { params })
                .then(({ data }) => {
                    this.employees = data
                })
                .catch(error => {
                    this.$message.error(this.$t('team.failed_to_get_employee_list'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },


        showLeaveButton(record) {
            return (this.user?.id === record.id) && !this.actions?.edit
        },
        showRemoveEmployeeButton(record) {
            return !this.isAuthor(record.id) && (this.actions?.edit) && (this.user?.id !== record.id)
        },
        search: debounce(async function() {
            if(this.searchText.length > 1) {
                this.getEmployeeList()
                    .finally(() => {
                        setTimeout(() => {
                            this.loading = false
                        }, 1000)

                    })
            } else{ 
                this.getEmployeeList()
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
                title: this.$t('team.exclude_user_from_access_group'),
                okText: this.$t('team.exclude'),
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
                                this.reloadList()
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
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getEmployeeList()
        },
        changePage(page) {
            this.page = page
            this.getEmployeeList()
        },
        reloadList() {
            this.page = 1
            this.getEmployeeList()
            this.reloadAccessGroupList()
        }
    }
}
</script>

<style lang="scss" scoped>
.org_user_table{
    &::v-deep{
        .ant-table-thead{
            background: #ffffff;
        }
    }
}
.tag{
    // font-size: 8px;
    // padding: 0 5px;
    line-height: 17px;
}
.tag_custom_margin {
    margin-left: 0.125rem;
}


.user_card{
    padding: 12px;
    zoom: 1;
    color: #505050;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: "tnum";
    background: #fff;
    border-radius: var(--borderRadius);
    border: 1px solid var(--border1);
    margin-bottom: 10px;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none;
    &__row{
        display: flex;
        align-items: center;
        &:not(:last-child){
            margin-bottom: 5px;
        }
        &--label{
            margin-right: 5px;
            color: var(--gray);
        }
    }
}
</style>