<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'">
        <TextViewer 
            v-if="widgetText"
            class="body_text"
            :body="widgetText" />
    </WidgetWrapper>
</template>

<script>
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        widgetText() {
            return this.widget.widget.random_html || null
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss" scoped>
.body_text{
    height: 100%;
    overflow: auto;
}
.mobile_widget{
    .body_text{
        max-height: 300px;
    }
}
</style>