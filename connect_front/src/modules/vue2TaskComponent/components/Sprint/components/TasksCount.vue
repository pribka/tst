<template >
    <div class="flex cursor-pointer">
        <a-tooltip :title="$t('task.new')" destroyTooltipOnHide> 
            <a-tag color="blue">
                {{record.new_task_count}}
            </a-tag></a-tooltip>
        <a-tooltip :title="$t('task.in_work')" destroyTooltipOnHide> 
            <a-tag color="purple">
                {{record.in_work_task_count}}
            </a-tag>
        </a-tooltip>  
        <a-tooltip :title="$t('task.completed')" destroyTooltipOnHide> 
            <a-tag color="#87d068">
                {{ record.completed_task_count}}
            </a-tag>
        </a-tooltip>
     
    </div>
</template>

<script>

export default {
    props: {
        record: Object
    }
}
</script>

<style>

</style>