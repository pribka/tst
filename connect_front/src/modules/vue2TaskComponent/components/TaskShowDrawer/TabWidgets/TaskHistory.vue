<template>
    <History 
        :related_object="task.id" 
        injectContainer
        filterPrefix="task"
        modelLabel="tasks.TaskModel" />
</template>

<script>
export default {
    name: "TaskHistory",
    props: {
        task: {
            type: Object,
            required: true
        }
    },
    components: {
        History: () => import('@apps/History/index.vue')
    }
}
</script>