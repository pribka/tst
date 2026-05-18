<template>
    <div class="task_table_wrapper">
        <UniversalTable 
            ref="taskTable"
            :model="model"
            :pageName="page_name"
            tableType="project-tasks"
            class="min-h-0"
            endpoint="/tasks/task/list/"
            :params="queryParams"
            :openHandler="openTask"
            :main="false"
            taskType="task"
            :childParams="{
                task_type: 'task,milestone,stage',
                ordering: 'dead_line'
            }"
            extendDrawer 
            showChildren
            :hash="false" />
    </div>
</template>

<script>
import TaskSocket from '@apps/vue2TaskComponent/mixins/TaskSocket'
export default {
    mixins: [TaskSocket],
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskRow(data)
            }
        }
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        isStudent: Boolean,
        isFounder: Boolean,
        actions: {
            type: Object,
            default: () => null
        },
        model: {
            type: String,
            default: "tasks.TaskModel"
        },
        page_name: {
            type: String,
            required: true
        }
    },
    data() {
        return{
            queryParams: {
                filters: {project: this.id, parent: null},
                task_type: 'task,stage,milestone'
            }
        }
    },
    methods: {
        openTask(item) {
            const query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== item.id || !query.task) {
                query.task = item.id
                this.$router.push({query})
            }
        },
        tableReload() {
            this.$nextTick(() => {
                this.$refs.taskTable.reloadTableData()
            })
        },
        updateTaskRow(task) {
            const table = this.$refs.taskTable
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
        },
        updateData() {
            this.tableReload()
        }
    }
}
</script>

<style lang="scss" scoped>
.task_table_wrapper{
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
}
</style>
