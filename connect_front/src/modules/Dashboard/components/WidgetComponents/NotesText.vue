<template>
    <TextViewer 
        :body="text" 
        :class="isMobile && 'mobile_text'"
        class="text_view" />
</template>

<script>
export default {
    props: {
        text: {
            type: String,
            default: ''
        }
    },
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss" scoped>
.text_view{
    cursor: pointer;
    height: 100%;
    overflow: auto;
    &.mobile_text{
        min-height: 300px;
        max-height: 300px;
    }
}
</style>