<template>
    <div>
        <p v-if="title" class="mb-2 text-base">
            <span class="mr-1">
                {{ title }} 
            </span>
            <a-tag>
                {{ taskCount }}
            </a-tag>
        </p>
        <UniversalTable
            :class="taskCount > 0 ? 'h-[380px]' : 'h-[180px]'"
            ref="tableRef"
            :model="model"
            :pageName="pageName"
            :tableType="tableType"
            :endpoint="`/tasks/sprint/${sprint.id}/tasks_list/`"
            :params="params"
            :getDataHook="getDataHook"
            :openHandler="openTask"
            :storeKey="storeKey"
            :infoKey="infoKey"
            taskType="task"
            extendDrawer />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import TaskSocket from '../../../../mixins/TaskSocket'
import UniversalTable from '@/components/TableWidgets/UniversalTable'
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
        UniversalTable
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        infoKey: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            required: true
        },
        title: {
            type: String,
            default: null
        },
        tableType: {
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
                ...this.queryParams,
                task_type: 'task,stage'
            },
            taskCount: 0
        }
    },
    mounted() {
        eventBus.$on('sprint_update_table_reload', this.tableReload)
    },
    beforeDestroy() {
        eventBus.$off('sprint_update_table_reload')  
    },
    methods: {
        getDataHook(data) {
            if(data?.count) {
                this.taskCount = data.count
            }
        },
        openTask(item) {
            const query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== item.id || !query.task) {
                query.task = item.id
                this.$router.push({query})
            }
        },
        tableReload() {
            this.$nextTick(() => {
                this.$refs.tableRef.reloadTableData()
            })
        },
        updateTaskRow(task) {
            const table = this.$refs.tableRef
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
        }
    }
}
</script>
