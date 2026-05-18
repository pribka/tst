<template>
    <div>
        <TaskList
            class="border_gray_top"
            :hash="false"
            :showHeader="false"
            :showChildren="false"
            :showAddButton="false"
            :showPager="false"
            :queryParams="{filters: { organization: organization.id}}"
            :scrollWrapper="{x: 1000, y: 300}"
            size="small"
            :showFilter="false"
            name="organizatoin_tasks"
            :pageName="`page_list_task_organizatoin_tasks.TaskModel`"
            :endpoint="endpoint"

            :showActionButton="false" >
            <template v-slot:header>
                <h4 class="mb-3 text-lg font-semibold">
                    {{$t('task.subtask')}}
                </h4>
            </template>
        </TaskList>

    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import debounce from '@/utils/lodash/debounce'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        TaskList: () => import('@apps/vue2TaskComponent/components/TaskList/TaskList')
    },
    props: {
        organization: {
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
        endpoint() {
            return `/users/my_organizations/${this.organization.id}/tasks/`
        },
        taskList() {
            return this.tasks.results || []
        },
        taskCount() {
            return this.tasks.count || 0
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
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
                    dataIndex: 'name',
                    title: this.$t('team.name'),
                    key: 'name',
                    scopedSlots: { customRender: 'name' }
                },
                {
                    dataIndex: 'email',
                    title: this.$t('team.email'),
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
            tasks: {}
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
        }),
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
                    filters: {
                        organization: this.organization.id
                    }
                    // text: this.searchText
                }
                const { data } = await this.$http(`/tasks/task/list/`, params)
                this.tasks = data
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
.crown{
    font-size: 8px;
    padding: 0 5px;
    line-height: 17px;
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