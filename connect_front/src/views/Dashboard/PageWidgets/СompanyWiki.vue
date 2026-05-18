<template>
    <Wiki />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Wiki: () => import('@apps/Support/Page.vue')
    }
}
</script>