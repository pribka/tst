<template>
    <WidgetWrapper :widget="widget">
        <Files
            isMyFiles
            widgetEmbed
            isFounder
            :showFilter="false"
            :fileDragCreate="false"
            isStudent />
    </WidgetWrapper>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        Files: () => import('@apps/vue2Files'),
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    }
}
</script>