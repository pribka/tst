<template>
    <div class="sidebar_list">
        <div
            v-for="(item) in helpDeskList"
            :key="`helpdesk_${item.id}`"
            class="sidebar_item"
            @click="createChat(item)">
            <UserCard
                :select="true"
                :show_org_admin_name="true"
                :userItem="item"/>
        </div>

        <infinite-loading
            @infinite="getHelpDeskList"
            v-bind:distance="20">
            <div slot="spinner">
                <a-spin
                    size="small"
                    style="margin-top: 10px;" />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { mapState, mapActions, mapMutations } from 'vuex'

export default {
    name: 'ChatHelpDeskList',
    components: {
        UserCard: () => import('../UserCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    computed: {
        ...mapState({
            helpDeskList:   state => state.chat.helpDeskList,
            helpDeskNext:   state => state.chat.helpDeskNext,
            helpDeskPage:   state => state.chat.helpDeskPage,
            chatList:       state => state.chat.chatList,
            isMobile:       state => state.isMobile
        })
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        ...mapActions({
            getSidebarHelpDesk: 'chat/getSidebarHelpDesk',
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat',
            // при необходимости можно дергать очистку перед первой загрузкой:
            // clearHelpDeskList:   'chat/clearHelpDeskList'
        }),
        ...mapMutations({
            createVirtualChat:       'chat/CREATE_VIRTUAL_CHAT',
        }),

        async getHelpDeskList($state) {
            if (this.helpDeskNext) {
                try {
                    this.loading = true
                    const res = await this.getSidebarHelpDesk({ all: false })
                    if (res.next) {
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } catch (e) {
                    console.log(e)
                    $state.error && $state.error()
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },

        async createChat(item) {
            const privateChat = await this.getPrivateChat(item.id)
            const isStandaloneChatWindow = this.$route?.name === 'chat-window'

            if (!privateChat?.chat_uid) {
                item['chat_author'] = this.$store.state.user.user
                this.createVirtualChat(item)

                if (this.isMobile) {
                    if (isStandaloneChatWindow) {
                        this.$router.push({
                            name: 'chat-window',
                            params: { id: item.id }
                        })
                        return
                    }
                    this.$router.push({
                        name: 'chat-body',
                        params: { id: item.id }
                    })
                }
            } else {
                const chatUid = privateChat.chat_uid

                if (this.isMobile) {
                    if (isStandaloneChatWindow) {
                        this.$router.push({
                            name: 'chat-window',
                            params: { id: chatUid }
                        })
                        this.$store.commit('chat/setSidebarActiveTab', 1)
                        return
                    }
                    this.$router.push({
                        name: 'chat-body',
                        params: { id: chatUid }
                    })
                } else {
                    const chat = await this.getCurrentChat(chatUid)
                    if (!chat || chat.chat_uid !== chatUid) return

                    if (
                        this.$store.state.chat.activeChat &&
                        !this.$store.state.chat.activeChat.is_public &&
                        this.$store.state.chat.activeChat.recipient?.id
                    ) {
                        this.$socket.client.emit('chat_status_user', {
                            chat_uid: this.$store.state.chat.activeChat.chat_uid,
                            user_uid: this.$store.state.chat.activeChat.recipient.id
                        })
                    }

                    const query = JSON.parse(JSON.stringify(this.$route.query || {}))
                    if (query.chat_id !== chatUid) {
                        query.chat_id = chatUid
                        this.$router.push({ query })
                    }
                }
                this.$store.commit('chat/setSidebarActiveTab', 1)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sidebar_list{
    padding-left: 15px;
    padding-right: 15px;
}
</style>
