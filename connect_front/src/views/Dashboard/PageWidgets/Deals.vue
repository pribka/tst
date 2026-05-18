<template>
    <Deals />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'

export default {
    mixins: [pageMeta],
    components: {
        Deals: () => import('@apps/Deals')
    }
}
</script>
