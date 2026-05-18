<template>
    <OKR />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        OKR: () => import('@apps/OKR')
    }
}
</script>