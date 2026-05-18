<template>
    <div class="support_page_base h-full">
        <InitPage v-if="isInitPage" />
        <ContentPage v-else />
    </div>
</template>

<script>
export default {
    components: {
        InitPage: () => import('./Init.vue'),
        ContentPage: () => import('./Content.vue')
    },
    computed: {
        isInitPage() {
            return !this.$route.params?.wikiType || !this.$route.params?.wikiId
        }
    }
}
</script>

<style lang="scss" scoped>
.support_page_base{
    height: 100%;
}
</style>
