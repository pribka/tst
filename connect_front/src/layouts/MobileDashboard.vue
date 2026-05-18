<template>
    <div class="container m_wrap">
        <component
            :is="newsBannerComponent"
            v-if="newsBannerComponent" />
        <main class="main">
            <component 
                :is="showHeaderComp" 
                :config="config" 
                :user="user" />
            <router-view />
            <component :is="showFooterComp" />
        </main>
        <!--<component :is="snowComponent" />-->
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            user: state => state.user.user,
            config: state => state.config.config,
            bannerNews: state => state.config.bannerNews,
            showFooter: state => state.showFooter,
            showHeader: state => state.showHeader,
            showHeaderComp: state => state.showHeaderComp,
            showFooterComp: state => state.showFooterComp
        }),
        newsBannerComponent() {
            return this.bannerNews
                ? () => import('@/modules/Support/components/NewsDrawer/NewsBanner.vue')
                : null
        },
        /**snowComponent() {
            if(this.$store.state.showSnow)
                return () => import('./components/SnowCanvas.vue')
            return null
        } */
    }
}
</script>

<style lang="scss" scoped>
.main {
    padding-top: var(--headerHeight);
}
.is-ios{
    .main{
        padding-top: 0px;
    }
}
</style>
