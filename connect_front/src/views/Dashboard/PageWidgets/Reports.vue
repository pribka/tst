<template>
    <Reports />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Reports: () => import('@apps/Reports')
    }
}
</script>