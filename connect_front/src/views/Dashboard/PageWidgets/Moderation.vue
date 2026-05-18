<template>
    <Moderation />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        Moderation: () => import('@apps/Moderation/index.vue')
    }
}
</script>