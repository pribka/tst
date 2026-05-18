<template>
    <div>
        <template v-if="isSprint">
            <a-tooltip title="Новые" destroyTooltipOnHide> 
                <a-tag color="blue">
                    {{record.new_task_count}}
                </a-tag></a-tooltip>
            <a-tooltip title="В работе" destroyTooltipOnHide> 
                <a-tag color="purple">
                    {{record.in_work_task_count}}
                </a-tag>
            </a-tooltip>  
            <a-tooltip title="Завершены" destroyTooltipOnHide> 
                <a-tag color="#87d068">
                    {{ record.completed_task_count}}
                </a-tag>
            </a-tooltip>
        </template>
        <template v-else>
            <a-tag color="blue">
                {{ record.tasks }}
            </a-tag>
            <a-tag color="#87d068">
                {{ record.complete_tasks }}
            </a-tag>
        </template>
    </div>
</template>


<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        model: {
            type: String
        },
        column: {
            type: Object
        },
    },
    computed: {
        isSprint() {
            return this.model === 'tasks.TaskSprintModel'
        },
    }
}
</script>