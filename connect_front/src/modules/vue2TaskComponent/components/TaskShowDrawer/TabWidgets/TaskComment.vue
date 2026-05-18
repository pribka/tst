<template>
    <vue2CommentsComponent
        bodySelector=".task_body_wrap"
        :related_object="task.id"
        model="tasks" />
</template>

<script>
export default {
    props: {
        task: {
            type: Object,
            required: true
        }
    },
    components: {
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    }
}
</script>