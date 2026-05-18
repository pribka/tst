<template>
    <div id="app">
        <router-view/>
        <template v-if="checkDrawerShow">
            <template v-if="config && config.injectInit && config.injectInit.length">
                <initSwitch
                    v-for="(folder, index) in config.injectInit"
                    :key="index"
                    :folder="folder" />
            </template>
            <component :is="eventDrawerAsync" v-if="user && $route.query.my_profile" />
            <component :is="setPassword" />
        </template>
        <OnlyofficePreviewModal />
        <NetworkStatus v-if="!online" />
        <vue-progress-bar></vue-progress-bar>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import launchQueue from '@/mixins/launchQueue'
import { yandexMetrikaHead } from '@/utils/yandex-metrika'
import NetworkStatus from '@/components/NetworkStatus'
export default {
    mixins: [launchQueue],
    sockets: {
        connect() {
            console.log('%c Socket connected 🤝', 'color: #1d65c0')
        },
        chat_online_user(data) {
            this.$store.commit('user/SET_ONLINE_USER', data)
        },
        chat_offline_user(data) {
            this.$store.commit('user/SET_OFFLINE_USER', data)
        }
    },
    metaInfo() {
        return {
            ...(process.env.NODE_ENV === 'production' ? yandexMetrikaHead : {}),
            title: this.siteName
        }
    },
    components: {
        initSwitch: () => import('@/components/initSwitch'),
        NetworkStatus,
        OnlyofficePreviewModal: () => import('@/components/OnlyofficePreview/Modal.vue')
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            online: state => state.online,
            user: state => state.user.user,
            serverType: state => state.serverType,
            isMobile: state => state.isMobile
        }),
        checkDrawerShow() {
            if(this.$route.name !== 'page_404'
            && this.$route.name !== 'login'
            && this.$route.name !== 'forgotPassword'
            && this.$route.name !== 'resetPassword'
            && this.$route.name !== 'joinUser'
            && this.$route.name !== 'forgotPasswordEmail'
            && this.$route.name !== 'forgotPasswordPhone'
            && this.$route.name !== 'registration') {
                return true
            } else
                return false
        },
        siteName() {
            if(this.config?.site_setting?.site_name)
                return this.config.site_setting.site_name
            else
                return 'Gos24.КОННЕКТ'
        },
        setPassword() {
            if(this.user?.password_generated)
                return () => import(/* webpackMode: "lazy" */'@/components/PasswordSet.vue')
            else
                return null
        }
    },
    watch: {
        '$route.query.my_profile': {
            immediate: true,
            handler(v) {
                if (v && !this.eventDrawerAsync)
                    this.eventDrawerAsync = () => import('@/components/UserSettings')
            }
        }
    },
    data() {
        return {
            styleLoaded: false,
            eventDrawerAsync: null
        }
    },
    async created() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault()
            this.$store.commit('SET_PWA_POPUP', e)
        })
        await this.lazyLoadModeStyles()
    },
    methods: {
        async lazyLoadModeStyles() {
            if (this.styleLoaded) return
            if (this.isMobile) {
                await import(/* webpackChunkName: "app-mobile" */ '@/assets/css/app.mobile.scss')
            } else {
                await import(/* webpackChunkName: "app-desktop" */ '@/assets/css/app.desktop.scss')
            }
            this.styleLoaded = true
        }
    },
    mounted() {
        const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.userAgent.includes('Mac') && 'ontouchend' in document)
        if(isiOS)
            document.documentElement.classList.toggle('is-ios', isiOS)

        this.$store.commit('UPDATE_WINDOW_WIDTH', window.innerWidth)
        this.$store.commit('UPDATE_WINDOW_HEIGHT', window.innerHeight)

        document.addEventListener("visibilitychange", () => {
            if (document.hidden)
                this.$store.commit('TOGGLE_VISIBILITY_STATE', false)
            else
                this.$store.commit('TOGGLE_VISIBILITY_STATE', true)
        })

        window.addEventListener('online', () => this.$store.commit('TOGGLE_ONLINE', true))
        window.addEventListener('offline', () => this.$store.commit('TOGGLE_ONLINE', false))

        let resizeId;
        window.addEventListener('resize', () => {
            clearTimeout(resizeId)
            resizeId = setTimeout(() => {
                this.$store.commit('UPDATE_WINDOW_WIDTH', window.innerWidth)
                this.$store.commit('UPDATE_WINDOW_HEIGHT', window.innerHeight)
            }, 150)
        })
    }
}
</script>
