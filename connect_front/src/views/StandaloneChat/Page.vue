<template>
    <ChatComponentMobile v-if="isReady" />
</template>

<script>
import chatStore from '@/modules/vue2ChatComponent/store/index'
import shareStore from '@/modules/vue2ChatComponent/store/share'

const CHAT_WINDOW_CACHE_KEY = 'chat-window-cache'

export default {
    name: 'StandaloneChatPage',
    components: {
        ChatComponentMobile: () => import('@/modules/vue2ChatComponent/components/MobileChat/Chat.vue')
    },
    metaInfo() {
        return {
            title: 'Чат | Gos24.Коннект'
        }
    },
    data() {
        return {
            isReady: false
        }
    },
    beforeCreate() {
        if (!this.$store.hasModule('chat')) {
            this.$store.registerModule('chat', chatStore)
        }

        if (!this.$store.hasModule('share')) {
            this.$store.registerModule('share', shareStore)
        }

        if (this.$store.state.isMobile !== true) {
            this._previousIsMobile = this.$store.state.isMobile
            this.$store.commit('SET_IS_MOBILE', true)
        }

        this.hydrateChatWindowCache()
    },
    created() {
        this.isReady = true
    },
    methods: {
        hydrateChatWindowCache() {
            if (typeof window === 'undefined') return

            try {
                const raw = window.localStorage.getItem(CHAT_WINDOW_CACHE_KEY)
                if (!raw) return

                const payload = JSON.parse(raw)
                if (!payload || typeof payload !== 'object') return

                this.$store.commit('chat/HYDRATE_CHAT_WINDOW_CACHE', payload)
                window.localStorage.removeItem(CHAT_WINDOW_CACHE_KEY)
            } catch (e) {
                // noop
            }
        }
    },
    beforeDestroy() {
        if (typeof this._previousIsMobile === 'boolean') {
            this.$store.commit('SET_IS_MOBILE', this._previousIsMobile)
        }
    }
}
</script>

<style lang="scss">
@import "@/modules/vue2ChatComponent/assets/css/style_mobile.scss";
</style>
