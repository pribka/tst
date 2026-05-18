<template>
    <Directories />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    name: 'PageWidgetsFiles',
    components: {
        Directories: () => import('@apps/Directories/index.vue'),
    },
    
}
</script>