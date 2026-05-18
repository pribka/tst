<template>
    <div :key="user.language" class="layout">
        <component 
            v-if="miniMenu" 
            :is="'style'">
            :root {
            --wrapperLeftPadding: 60px
            }
        </component>
        <component 
            v-if="!miniMenu" 
            :is="'style'">
            :root {
            --wrapperLeftPadding: 250px
            }
        </component>
        <component 
            :is="'style'">
            :root {
            --asideWidth: {{ asideWidth }}px
            }
        </component>

        <component
            :is="newsBannerComponent"
            v-if="newsBannerComponent" />

        <!-- Main wrapper template -->
        <main 
            class="main_wrapper flex overflow-hidden relative" 
            style="flex-grow: 1;">
            <!-- Sidebar template -->
            <template v-if="asideType !== 'header'">
                <component 
                    :is="sidebarTemplate" 
                    :config="config" />
            </template>
            
            <div class="flex flex-col w-full">
                <!-- Header template -->
                <Header />

                <!-- Content template -->
                <div 
                    class="content_wrapper" 
                    style="flex-grow: 1;">
                    <router-view />
                </div>
            </div>
        </main>
        <!--<component :is="snowComponent" />-->
        <component :is="remoteAccessComponent" />
    </div>
</template>

<script>
import {mapState} from 'vuex'
import theme from './mixins/theme'
export default {
    mixins: [
        theme
    ],
    components: {
        Header: () => import('./components/Header'),
        RemoteAccess: () => import('@/components/RemoteAccess.vue')
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            menu: state => state.navigation.menu,
            isMobile: state => state.isMobile,
            eyeVersion: state => state.eyeVersion,
            config: state => state.config.config,
            bannerNews: state => state.config.bannerNews,
            serverType: state => state.serverType,
            asideType: state => state.asideType,
            showLangMessage: state => state.showLangMessage,
            browserLang: state => state.browserLang
        }),
        newsBannerComponent() {
            return this.bannerNews
                ? () => import('@/modules/Support/components/NewsDrawer/NewsBanner.vue')
                : null
        },
        remoteAccessComponent() {
            return this.isMobile
                ? null
                : () => import('@/components/RemoteAccess.vue')
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
.layout {
    display: flex;
    flex-direction: column;
    .main_wrapper{
        width: 100vw;
        padding-left: var(--wrapperLeftPadding);
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
}
.content_wrapper {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
}
</style>
