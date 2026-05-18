<template>
    <div class="sidebar_list">
        <div
            v-for="(item) in contactList"
            :key="`contact_${item.id}`"
            class="sidebar_item"
            @click="createChat(item)">
            <UserCard
                :select="true"
                :userItem="item"/>
        </div>
        <infinite-loading
            v-if="!hasSeededStandaloneContactList"
            @infinite="getContactsList"
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
    name: "ChatContactList",
    components: {
        UserCard: () => import('../UserCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    computed: {
        ...mapState({
            contactList: state => state.chat.contactList,
            chatList: state => state.chat.chatList,
            contactListNext: state => state.chat.contactListNext,
            contactListPage: state => state.chat.contactListPage,
            isMobile: state => state.isMobile
        }),
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        hasSeededStandaloneContactList() {
            return this.isStandaloneChatWindow
                && this.contactListPage > 0
                && this.contactList.length > 0
        }
    },
    data() {
        return {
            loading: false,
            page: 1
        }
    },
    methods: {
        ...mapActions({
            getSidebarContact: 'chat/getSidebarContact',
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat'
        }),
        ...mapMutations({
            createVirtualChat: 'chat/CREATE_VIRTUAL_CHAT',
        }),
        async getContactsList($state) {
            if (this.hasSeededStandaloneContactList) {
                $state.complete()
                return
            }

            if(this.contactListNext) {
                try {
                    this.loading = true

                    const res = await this.getSidebarContact({all: false})
                    if(res.next) {
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else
                $state.complete()
        },

        async createChat(item){
            const privateChat = await this.getPrivateChat(item.id)

            if(!privateChat?.chat_uid) {
                item['chat_author'] = this.$store.state.user.user
                this.createVirtualChat(item)

                if(this.isMobile) {
                    this.$router.push({
                        name: this.isStandaloneChatWindow ? 'chat-window' : 'chat-body',
                        params: {
                            id: item.id
                        }
                    })
                }
            } else {
                const chatUid = privateChat.chat_uid

                if(this.isMobile) {
                    this.$router.push({
                        name: this.isStandaloneChatWindow ? 'chat-window' : 'chat-body',
                        params: {
                            id: chatUid
                        }
                    })
                } else {
                    const chat = await this.getCurrentChat(chatUid)
                    if (!chat || chat.chat_uid !== chatUid) return

                    if(
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
                    if(query.chat_id !== chatUid) {
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
