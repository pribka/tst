<template>
    <UniversalTable 
        ref="taskTable"
        :model="model"
        :pageName="page_name"
        tableType="tasks"
        autoHeight
        endpoint="/tasks/task/list/"
        :params="queryParams"
        :openHandler="openTask"
        :main="false"
        taskType="task"
        extendDrawer 
        :hash="false" />
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
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            queryParams: {
                filters: { reason: this.ticket.id }
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
