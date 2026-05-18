<template>
    <Calendar />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Calendar: () => import('@apps/Calendar')
    }
}
</script>