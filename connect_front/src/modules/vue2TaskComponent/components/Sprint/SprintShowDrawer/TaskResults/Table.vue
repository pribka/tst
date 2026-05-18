<template>
    <div class="h-full flex flex-col min-h-0">
        <UniversalTable 
            class="min-h-0"
            :model="model"
            :pageName="pageName"
            tableType="sprint_expected_results"
            :endpoint="endpoint"
            :params="params"
            :openHandler="openTask"
            :main="false"
            taskType="task"
            extendDrawer
            :hash="false" />
    </div>
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
            return `/tasks/sprint/${this.sprint.id}/expected_results/`
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
        }
    }
}
</script>