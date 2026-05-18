<template>
    <SportsFacilities />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        SportsFacilities: () => import('@apps/SportsFacilities/index.vue')
    }
}
</script>