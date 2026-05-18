<template>
    <div class="task_table_wrapper flex-grow">
        <UniversalTable 
            ref="taskTable"
            :model="model"
            :pageName="page_name"
            tableType="tasks_to_sprint"
            useSelect
            endpoint="/tasks/sprint/task/list/"
            :params="queryParams"
            :openHandler="openTask"
            :main="false"
            taskType="task"
            :selectedIds="selectedIds"
            showChildren
            extendDrawer
            :hash="false"
            @rowSelected="rowSelected" />
    </div>
</template>

<script>
import TaskSocket from '../../../mixins/TaskSocket'
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
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        queryParams: {
            type: Object,
            default: () => {}
        },
        rowSelected: {
            type: Function,
            default: () => {}
        },
        selectedIds: {
            type: Array,
            default: () => []
        }
    },
    methods: {
        openTask(item) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(query.task && Number(query.task) !== item.id || !query.task) {
                query.task = item.id
                this.$router.push({query})
            }
        },
        updateTaskRow(task) {
            const table = this.$refs.taskTable
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
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
