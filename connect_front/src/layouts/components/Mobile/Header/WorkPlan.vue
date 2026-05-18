<template>
    <WorkPlan />
</template>

<script>
export default {
    components: {
        WorkPlan: () => import('@apps/WorkPlan/index.vue')
    }
}
</script>