<template>
    <div class="sidebar_list">
        <div>
            <div
                v-for="(group, index) in sortedList"
                :key="`group_${index}`"
                class="sidebar_item">
                <!-- для закреплённой группы key === '' метка не нужна -->
                <GroupLabel v-if="group.key" :group="group" />

                <div
                    v-for="item in group.data"
                    :key="`chat_${item.id}`"
                    class="ch_item">
                    <ChatContact :chat="item" />
                </div>
            </div>

            <infinite-loading
                @infinite="getChatList"
                ref="chat_list_inf"
                v-bind:distance="20">
                <div slot="spinner">
                    <a-spin
                        v-if="!hasSeededStandaloneChatList || skipInitialPrefetchedLoad"
                        size="small"
                        style="margin-top: 10px;" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>

            <a-empty
                v-if="!loading && chatList.length === 0"
                class="mt-4"
                :description="$t('chat.list_empty')"/>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import ChatEventBus from '../../utils/ChatEventBus'
import { getChatDraftsByUser } from '../../utils/chatDraftsDb'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'ChatList',
    components: {
        ChatContact: () => import('../ChatContact.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        GroupLabel: () => import('./GroupLabel.vue')
    },
    computed: {
        ...mapState({
            chatList: state => state.chat.chatList,
            chatListNext: state => state.chat.chatListNext,
            chatListPage: state => state.chat.chatListPage,
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        sortedList() {
            const isSupport = !!(this.user && this.user.is_support)

            const toMs = v => {
                const m = this.$moment(v)
                return m.isValid() ? +m : 0
            }

            const sortByLastSentDesc = (a, b) => toMs(b.last_sent) - toMs(a.last_sent)

            const groupByDate = items =>
                items.reduce((acc, curr) => {
                    const m = this.$moment(curr.last_sent)
                    const key = m.isValid() ? m.format('YYYY-MM-DD') : ''
                    const idx = acc.findIndex(g => g.key === key)
                    if (idx >= 0) acc[idx].data.push(curr)
                    else acc.push({ key, data: [curr] })
                    return acc
                }, [])

            if (isSupport) {
                const base = [...this.chatList].sort(sortByLastSentDesc)
                const dateGroups = groupByDate(base)
                dateGroups.sort((a, b) => (a.key < b.key ? 1 : -1))
                dateGroups.forEach(g => g.data.sort(sortByLastSentDesc))
                return dateGroups
            }

            const pinned = []
            const others = []
            for (const item of this.chatList) {
                if (item.is_pinned) pinned.push(item)
                else others.push(item)
            }

            pinned.sort(sortByLastSentDesc)

            const base = others.sort(sortByLastSentDesc)
            const dateGroups = groupByDate(base)
            dateGroups.sort((a, b) => (a.key < b.key ? 1 : -1))
            dateGroups.forEach(g => g.data.sort(sortByLastSentDesc))

            if (pinned.length) {
                dateGroups.unshift({
                    key: '',
                    is_pinned: true,
                    data: pinned
                })
            }

            return dateGroups
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        hasSeededStandaloneChatList() {
            return this.isStandaloneChatWindow && this.chatListPage > 0 && this.chatList.length > 0
        }
    },
    data() {
        return {
            loading: false,
            skipInitialPrefetchedLoad: false
        }
    },
    methods: {
        ...mapActions({
            getSidebarChat: 'chat/getSidebarChat',
            cancelSidebarChatPrefetch: 'chat/cancelSidebarChatPrefetch'
        }),
        async getMessageCount() {
            try {
                await this.$store.dispatch('chat/getMessageCount')
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async loadDrafts() {
            const userId = this.user?.id

            if (!userId) {
                this.$store.commit('chat/SET_CHAT_DRAFTS', {})
                return
            }

            try {
                const drafts = await getChatDraftsByUser(userId)
                this.$store.commit('chat/SET_CHAT_DRAFTS', drafts)
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        async getChatList($state) {
            if (!this.skipInitialPrefetchedLoad && this.chatListPage > 0 && this.chatList.length > 0) {
                this.skipInitialPrefetchedLoad = true

                if (this.chatListNext) $state.loaded()
                else $state.complete()

                return
            }

            if (this.chatListNext) {
                try {
                    this.loading = true
                    await this.cancelSidebarChatPrefetch()
                    const res = await this.getSidebarChat()
                    if (res.next) {
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } catch (e) {
                    if (e?.__CANCEL__) return
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        reload() {
            if (this.$refs['chat_list_inf']?.stateChanger) {
                this.$refs['chat_list_inf'].stateChanger.reset()
            }
            this.$store.commit('chat/CLEAR_CHAT_LIST')
            this.getMessageCount()
        }
    },
    mounted() {
        this.loadDrafts()
        ChatEventBus.$on('updateChatList', payload => {
            if (payload?.reason === 'chat_rename') return
            this.reload()
        })
        if (this.isMobile && !this.isStandaloneChatWindow) {
            window.onfocus = () => {
                this.reload()
            }
        }
    },
    beforeDestroy() {
        ChatEventBus.$off('updateChatList')
        if (this.isMobile && !this.isStandaloneChatWindow && typeof window !== 'undefined') {
            window.onfocus = null
        }
    },
    watch: {
        'user.id': {
            immediate: false,
            handler() {
                this.loadDrafts()
            }
        }
    }
}
</script>
