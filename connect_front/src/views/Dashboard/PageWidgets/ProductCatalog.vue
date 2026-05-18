<template>
    <Products />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Products: () => import('@apps/Products/index.vue')
    }
}
</script>