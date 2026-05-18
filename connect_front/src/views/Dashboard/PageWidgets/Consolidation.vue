<template>
    <Consolidation />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Consolidation: () => import('@apps/Consolidation')
    }
}
</script>