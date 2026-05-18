<template>
    <RequestApprovals />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        RequestApprovals: () => import('@apps/RequestApprovals/index.vue')
    }
}
</script>