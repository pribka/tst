<template>
    <HelpDesk />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        HelpDesk: () => import('@apps/HelpDesk')
    }
}
</script>