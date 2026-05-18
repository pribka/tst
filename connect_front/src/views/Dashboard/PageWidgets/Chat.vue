<template>
    <vue2ChatComponent />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        vue2ChatComponent: () => import('@apps/vue2ChatComponent')
    }
}
</script>