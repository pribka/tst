<template>
    <Pulse />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Pulse: () => import('@apps/WorkPlan/Page.vue')
    }
}
</script>