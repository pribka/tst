<template>
    <Planner />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Planner: () => import('@apps/Planner/Page.vue')
    }
}
</script>