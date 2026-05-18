<template>
    <InvestProject />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        InvestProject: () => import('@apps/InvestProject/index.vue')
    }
}
</script>