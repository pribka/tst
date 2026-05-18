<template>
    <UniversalTable 
        ref="tableRef"
        :model="model"
        :pageName="pageName"
        tableType="task_labor_costs"
        class="h-[380px]"
        :endpoint="endpoint"
        :params="queryParams"
        :openHandler="openTask"
        :main="false"
        taskType="task"
        extendDrawer
        :hash="false" />
</template>

<script>
import UniversalTable from '@/components/TableWidgets/UniversalTable'
export default {
    components: {
        UniversalTable
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        title: {
            type: String,
            default: null
        },
        queryParams: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            loading: false,
            params: {
                // ...this.queryParams,
                // task_type: 'task,stage'
            }
        }
    },
    computed: {
        endpoint() {
            return `/tasks/sprint/${this.sprint.id}/report/tasks/`

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
        reload() {
            this.$nextTick(() => {
                this.$refs.tableRef.reloadTableData()
            })
        }
    }
}
</script>