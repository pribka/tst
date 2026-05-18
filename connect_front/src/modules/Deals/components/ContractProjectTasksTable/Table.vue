<template>
    <div class="contract_project_tasks_table" ref="wrapRef">
        <UniversalTable
            ref="taskTable"
            :model="model"
            :pageName="normalizedPageName"
            tableType="tasks"
            class="min-h-0"
            endpoint="/tasks/task/list/"
            :params="queryParams"
            :openHandler="openTask"
            :main="false"
            taskType="task"
            :childParams="childParams"
            extendDrawer
            showChildren
            :hash="false" />
    </div>
</template>

<script>
import TaskSocket from '@apps/vue2TaskComponent/mixins/TaskSocket'

export default {
    name: 'ContractProjectTasksTableDesktop',
    mixins: [TaskSocket],
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskRow(data)
            }
        },
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
    },
    props: {
        projectId: {
            type: [String, Number],
            required: true,
        },
        contractId: {
            type: String,
            required: true,
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    data() {
        return {
            model: 'tasks.TaskModel',
            childParams: {
                task_type: 'task,milestone,stage',
                ordering: 'dead_line',
            },
        }
    },
    computed: {
        normalizedPageName() {
            return this.pageName || `deals.contract_project_tasks_${this.contractId}_${this.projectId}`
        },
        queryParams() {
            return {
                filters: {
                    project: this.projectId,
                    parent: null,
                    contract: this.contractId,
                },
                task_type: 'task,stage,milestone',
            }
        },
    },
    methods: {
        openTask(item) {
            this.$emit('open', item?.id)
        },
        updateTaskRow(task) {
            const table = this.$refs.taskTable
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
        },
        loadData() {
            this.$nextTick(() => {
                this.$refs.taskTable?.reloadTableData?.()
            })
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_project_tasks_table {
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 460px;
    height: 100%;
}
</style>
