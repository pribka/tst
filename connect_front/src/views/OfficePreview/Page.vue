<template>
    <OnlyofficePreviewViewer :query="$route.query" />
</template>

<script>
export default {
    components: {
        OnlyofficePreviewViewer: () => import('@/components/OnlyofficePreview/Viewer.vue')
    }
}
</script>
