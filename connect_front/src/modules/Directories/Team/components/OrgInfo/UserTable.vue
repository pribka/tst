<template>
    <div>
        <div class="mb-4">
            <a-input-search
                :placeholder="$t('team.search')"
                v-model="searchText"
                allowClear
                size="large"
                @change="search"/>
        </div>
        <a-table
            :columns="tableColumns"
            :pagination="false"
            class="org_user_table flex flex-col"
            :loading="loading"
            :locale="{
                emptyText: this.$t('team.no_data')
            }"
            :scroll="{ x: 1000 }"
            :size="tableSize"
            :row-key="record => record.id"
            :data-source="employeeList">
            <template slot="first_name" slot-scope="text, record">
                <a-tooltip>
                    <template slot="title">
                        {{ record.id }}
                    </template>
                    <a-button 
                        @click="copyUserId(record)"
                        flaticon
                        shape="circle"
                        ghost
                        type="ui"
                        icon="fi-rr-copy-alt" />
                </a-tooltip>
            </template>
            <template
                slot="full_name"
                slot-scope="text, record">
                <div>
                    <div>
                        <Profiler
                            :user="record"
                            initStatus
                            hideSupportTag
                            :avatarSize="28" />
                    </div>
                    <div v-if="record.is_org_admin || record.is_support || isAuthor(record.id)" class="mt-1">
                        <div class="flex items-center">
                            <a-tag 
                                v-if="record.is_org_admin" 
                                color="green" 
                                class="tag tag_custom_margin" 
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                :content="$t('team.administrator')">
                                {{ $t('team.admin') }}
                            </a-tag>
                            <a-tag 
                                v-if="record.is_support" 
                                color="green" 
                                class="tag tag_custom_margin" 
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                :content="$t('team.support')">
                                <i class="fi fi-rr-headset" />
                            </a-tag>
                            <a-tag 
                                v-if="isAuthor(record.id)" 
                                color="green" 
                                class="tag tag_custom_margin" 
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                :content="$t('team.director')">
                                <i class="fi fi-rr-crown" />
                            </a-tag>
                        </div>
                    </div>
                </div>
            </template>
            <template
                slot="email"
                slot-scope="text, record">
                <a :href="`mailto:${record.email}`">
                    {{ record.email }}
                </a>
            </template>
            <template
                slot="access_group"
                slot-scope="text, record">
                <AccessGroupSelect 
                    :user="record"
                    :organization="org" />
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
                    v-if="showRemoveEmployeeButton(record)" 
                    type="link" 
                    v-tippy="{ touch: false }" 
                    :content="$t('team.exclude_user')"
                    class="text_current ant-btn-icon-only" 
                    @click="deleteUser(record)">
                    <i class="fi fi-rr-remove-user text_red"></i>
                </a-button>
                <a-button 
                    v-if="showLeaveButton(record)" 
                    type="danger" 
                    ghost
                    @click="leaveOrg()">
                    {{ $t('team.leave_organization') }}
                </a-button>
            </template>
            <template
                slot="actions"
                slot-scope="text, record">
                <a-dropdown
                    v-if="canManageEmployee(record)"
                    :trigger="['click']"
                    :getPopupContainer="getActionPopupContainer">
                    <a-button
                        type="ui"
                        ghost
                        flaticon
                        shape="circle"
                        size="small"
                        icon="fi-rr-menu-dots-vertical" />
                    <a-menu slot="overlay">
                        <a-menu-item
                            key="fire"
                            class="flex items-center text_red"
                            @click="openFireEmployeeModal(record)">
                            <i class="fi fi-rr-user-minus mr-2" />
                            Уволить
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
            </template>
        </a-table>

        <div class="flex justify-end mt-2">
            <a-pagination
                :current="page"
                class="pager_wrapper"
                :show-size-changer="pageSizeOptions.length > 1"
                :page-size.sync="pageSize"
                :defaultPageSize="Number(pageSize)"
                :pageSizeOptions="pageSizeOptions"
                :total="employeeCount"
                show-less-items
                @showSizeChange="sizeSwicth"
                @change="changePage">
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div>

        <FireEmployeeModal
            ref="fireEmployeeModal"
            :org="org"
            @success="handleEmployeeFired" />
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import debounce from '@/utils/lodash/debounce'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        AccessGroupSelect: () => import('../AccessGroups/AccessGroupSelect.vue'),
        FireEmployeeModal: () => import('./FireEmployeeModal.vue')
    },
    props: {
        org: {
            type: Object,
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
        actions: {
            type: Object,
            default: () => null
        },
        page_name: {
            type: String,
            default: 'orgInfoDrawer'
        },
        model: {
            type: String,
            default: 'users.ProfileModel'
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
        parentId: {
            type: String,
            default: null
        },
        isAdmin: {
            type: Boolean,
            default: false
        },
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
            isMobile: state => state.isMobile,
            user: state => state.user.user,
            employees: state => state.organization.employees
        }),
        employeeList() {
            return this.employees?.[this.org.id]?.results
        },
        employeeCount() {
            return this.employees?.[this.org.id]?.count
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        canEditOrganization() {
            return Boolean(this.actions?.edit?.availability)
        },
        tableColumns() {
            if (!this.canEditOrganization) {
                return this.columns
            }

            return [
                ...this.columns,
                {
                    dataIndex: 'actions',
                    title: '',
                    key: 'actions',
                    width: 60,
                    fixed: 'right',
                    scopedSlots: { customRender: 'actions' }
                }
            ]
        }
    },
    created() {
        this.getList()
    },
    data() {
        return {
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            sort: '',
            count: 0,
            columns: [
                {
                    dataIndex: 'full_name',
                    title: this.$t('team.full_name_short'),
                    key: 'full_name',
                    width: 300,
                    scopedSlots: { customRender: 'full_name' }
                },
                {
                    dataIndex: 'first_name',
                    title: 'ID',
                    key: 'first_name',
                    width: 80,
                    scopedSlots: { customRender: 'first_name' }
                },
                {
                    dataIndex: 'email',
                    title: 'E-mail',
                    key: 'email',
                    width: 250,
                    scopedSlots: { customRender: 'email' }
                },
                {
                    dataIndex: 'job_title',
                    title: this.$t('team.position'),
                    key: 'job_title',
                    width: 150,
                    scopedSlots: { customRender: 'job_title' }
                },
                // УБРАЛ ПЕРЕД ПРОДОМ
                // { 
                //     dataIndex: 'access_group',
                //     title: 'Группа доступа',
                //     key: 'access_group',
                //     width: 250,
                //     scopedSlots: { customRender: 'access_group' }
                // },
                {
                    dataIndex: 'last_activity',
                    title: this.$t('team.last_activity'),
                    key: 'last_activity',
                    scopedSlots: { customRender: 'last_activity' }
                },
            ],
            list: [],
            loading: false,
            searchText: '',
            searchStart: false
        }
    },
    mounted () {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () =>{
            this.$nextTick(() => {
                this.getList()
            })
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
    },
    methods: {
        ...mapActions({
            getEmployeeList: 'organization/getEmployeeList'
        }),
        copyUserId(record) {
            try {
                navigator.clipboard.writeText(record.id)
                this.$message.success(this.$t('team.id_copied'))
            } catch(error) {
                console.log(error)
            }
        },
        canManageEmployee(record) {
            return this.canEditOrganization
        },
        getActionPopupContainer(trigger) {
            return trigger?.closest('.drawer_body') || document.body
        },
        openFireEmployeeModal(record) {
            this.$refs.fireEmployeeModal.open(record)
        },
        async handleEmployeeFired() {
            if ((this.employeeList?.length || 0) === 1 && this.page > 1) {
                this.page -= 1
            }

            await this.getList()
            this.minusUserCount(this.org)
            this.updateTableRowsHeight()
        },
        showLeaveButton(record) {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return (this.user?.id === record.id) && !this.actions?.edit
        },
        showRemoveEmployeeButton(record) {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return !this.isAuthor(record.id) && (this.actions?.edit) && (this.user?.id !== record.id)
        },
        search: debounce(async function() {
            if(this.searchText.length > 1) {
                try {
                    await this.getList()
                } catch(e) {

                } finally {
                    setTimeout(() => {
                        this.loading = false
                    }, 1000)
                }
                
            } else{ 
                await this.getList()
            }
        },500),
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
                        return // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
                        // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
                        
                        // this.$http.post(`/users/my_organizations/${this.org.id}/leave/`)
                        //     .then(() => {
                        //         this.$message.info(this.$t('team.successfully_left_organization'))
                        //         eventBus.$emit('orgTableReload')
                        //         resolve(true)
                        //     })
                        //     .catch((error) => { 
                        //         this.$message.error(this.$t('team.error'))
                        //         reject(error)
                        //     })
                    })
                }
            })
        },
        deleteUser(record) {
            this.$confirm({
                title: this.$t('team.confirm_remove_user_from_access_group'),
                okText: this.$t('team.remove'),
                okType: 'danger',
                cancelText: this.$t('team.cancel'),
                closable: true,
                maskClosable: true,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
                        // когда пользователь не принадлежит ни к какой организации. (Задача 10819)

                        // const url = this.isDepartment ? `/users/my_organizations/departments/${this.org.id}/users/delete/`
                        //     : `/users/my_organizations/${this.org.id}/users/delete/`

                        // this.$http.post(url, { id: record.id })
                        //     .then(() => {
                        //         this.$message.info(this.$t('team.user_excluded_from_organization'))

                        //         // 
                        //         this.org.id
                        //         this.$store.commit('organization/DELETE_EMPLOYEE', {
                        //             organizationId: this.org.id,
                        //             employeeId: record.id,
                        //             parentId: this.parentId,
                        //             isDepartment: this.isDepartment
                        //         })
                        //         // 

                        //         const index = this.list.findIndex(f => f.id === record.id)
                        //         if(index !== -1) {
                        //             this.list.splice(index, 1)
                        //             this.count = this.count - 1
                        //             this.minusUserCount(this.org)
                        //         }

                        //         resolve(true)
                        //     })
                        //     .catch((error) => { 
                        //         this.$message.error(this.$t('team.deletion_error'))
                        //         reject(error)
                        //     })
                    })
                }
            })
        },
        isAuthor(id) {
            return this.org?.director?.id === id
        },
        async getList() {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name,
                    text: this.searchText
                }
                await this.getEmployeeList({ 
                    params: params, 
                    key: this.org.id,
                    isDepartment: this.isDepartment
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getList()
        },
        changePage(page) {
            this.page = page
            this.getList()
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
    line-height: 22px;
}
.tag_custom_margin {
    margin-left: 0px;
    margin-right: 5px;
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
