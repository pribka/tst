<template>
    <div>
        <TaskTable
            v-for="table in tableList"
            :key="table.key"
            :sprint="sprint"
            :model="model"
            :actions="actions"
            tableType="sprint_tasks"
            :title="table.title"
            :queryParams="{ display: table.key }"
            :pageName="pageName"
            :storeKey="pageName + '_' + table.key" />
        <template v-if="sprint.status === 'completed'">
            <TaskTable
                key="moved_to_sprint"
                :sprint="sprint"
                :model="model"
                :actions="actions"
                tableType="sprint_tasks_moved"
                :title="$t('sprint.moved_to_sprint')"
                :queryParams="{ display: 'moved_to_sprint' }"
                :pageName="pageName"
                infoKey="tasks_moved_to_sprint"
                :storeKey="pageName + '_moved_to_sprint'" />
        </template>
    </div>
</template>

<script>
import TaskTable from './TaskTable.vue'

export default {
    components: {
        TaskTable
    },
    data() {
        return {
            tableList: [
                { 
                    key: 'opened', 
                    title: this.$t('sprint.opened') 
                },
                { 
                    key: 'completed', 
                    title: this.$t('sprint.completed') 
                },
                { 
                    key: 'after_start', 
                    title: this.$t('sprint.after_start') 
                },
                { 
                    key: 'moved_to_backlog', 
                    title: this.$t('sprint.moved_to_backlog') 
                },
            ]
        }
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
        model: {
            type: String,
            required: true
        }
    }
}
</script>