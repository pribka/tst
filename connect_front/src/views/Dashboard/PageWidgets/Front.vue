<template>
    <Dashboard />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Dashboard: () => import('@apps/Dashboard')
    }
}
</script>