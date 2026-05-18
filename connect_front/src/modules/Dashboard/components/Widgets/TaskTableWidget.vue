<template>
    <WidgetWrapper :widget="widget">
        <template slot="actions">
            <SettingsButton 
                :pageName="pageName"
                shape="circle"
                size="default" />
            <a-button
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-plus"
                @click="addTask()" />
        </template>
        <div class="h-full table_widget">
            <UniversalTable 
                ref="taskTable"
                :model="model"
                :pageName="pageName"
                :tableType="tableType"
                autoHeight
                :openHandler="openTask"
                :endpoint="endpoint"
                main
                :params="queryParams"
                :taskType="task_type"
                :takeTask="takeTask"
                showChildren
                :hash="false" />
        </div>
    </WidgetWrapper>
</template>

<script>
import { mapActions } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskRow(data)
            }
        }
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton')
    },
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        endpoint() {
            return `/tasks/task/list/?task_type=${this.task_type}`
        },
        pageName() {
            return (this.widget.page_name || this.widget.id) || this.widget.widget.id
        }
    },
    data() {
        return {
            listLoading: false,
            taskList: [],
            page: 1,
            count: 0,
            task_type: 'task',
            model: 'tasks.TaskModel',
            tableType: 'tasks',
            queryParams: {
                /*filters: {parent: null}*/
            }
        }
    },
    methods: {
        ...mapActions({
            getTableInfo: 'table/getTableInfo'
        }),
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.pageName
            })
            this.$store.commit('task/SET_FORM_DEFAULT', {
                create_handler: this.widget.page_name || this.widget.id,
                task_type: 'task'
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal', {
                create_handler: this.widget.page_name || this.widget.id,
                task_type: 'task'
            })
        },
        async getTaskList() {
            try {
                this.listLoading = true
                const { data } = await this.$http.get('/tasks/task/list/', {
                    params: {
                        page_name: this.pageName,
                        task_type: this.task_type,
                        page: this.page,
                        page_size: 15
                    }
                })
                if(data) {
                    this.taskList = data.results
                    this.count = data.count
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.listLoading = false
            }
        },
        changePage(page) {
            this.page = page
            this.getTaskList()
        },
        openTask() {

        },
        takeTask() {

        },
        updateTaskRow(task) {
            const table = this.$refs.taskTable
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
        },
        reloadTask() {
            this.page = 1
            this.count = 0
            this.taskList = []
            this.getTaskList()
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.pageName}`, () => {
            this.reloadTask()
        })
        eventBus.$on(`TASK_CREATED_${this.task_type}_${this.pageName}`, () => {
            this.reloadTask()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.pageName}`)
        eventBus.$off(`TASK_CREATED_${this.task_type}_${this.pageName}`)
    }
}
</script>

<style lang="scss" scoped>
.table_widget{
    &::v-deep{
        .tableWrapper{
            height: 100%;
            overflow: hidden;
            .ag-theme-alpine{
                flex-grow: 1;
                overflow: auto;
            }
        }
    }
}
</style>
