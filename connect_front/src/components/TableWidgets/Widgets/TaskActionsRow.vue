<template>
    <TaskAction :item="record" />
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    components: {
        TaskAction: () => import('@apps/vue2TaskComponent/components/TaskActions/List.vue')
    }
}
</script>