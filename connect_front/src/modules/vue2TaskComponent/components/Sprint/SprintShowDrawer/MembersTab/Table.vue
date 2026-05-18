<template>
    <UniversalTable 
        ref="tableRef"
        :model="model"
        :pageName="pageName"
        tableType="sprint_members"
        :onRowClicked="onRowClicked"
        :getDataHook="getDataHook"
        class="h-[380px]"
        :endpoint="endpoint"
        storeKey="sprint_members"
        :params="params"
        :openHandler="openTask"
        extendDrawer />
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
        },
        onRowClicked: {
            type: Function,
            default: () => {}
        },
        getDataHook: {
            type: Function,
            default: () => {}
        },
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
            return `tasks/sprint/${this.sprint.id}/members/`

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