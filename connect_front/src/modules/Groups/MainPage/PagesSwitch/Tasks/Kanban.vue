<template>
    <Kanban 
        :showAddButton="false"
        :extendDrawer="true"
        :useScrollDummy="false"
        :taskType="task_type"
        :page_name="page_name"
        :queryParams="queryParams"
        implementType="project" />
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Kanban: () => import('@apps/vue2TaskComponent/components/Kanban')
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
        return {
            task_type: 'task',
            queryParams: {
                filters: {workgroup: this.id},
                task_type: 'task',
                page_name: this.page_name
            }
        }
    },
    methods: {
        tableReload() {
            this.$nextTick(() => {
                this.$refs.taskTable.reloadTableData()
            })
        },
        updateData() {
            eventBus.$emit(`update_filter_data_${this.page_name}`)
        }
    }
}
</script>