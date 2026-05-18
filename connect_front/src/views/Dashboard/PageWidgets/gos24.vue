<template>
    <GOS24 />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        GOS24: () => import('@apps/GOS24/index.vue')
    }
}
</script>