<template>
    <div class="chat_wrapper hfl flx">
        <Sidebar v-if="!dealerChat" />
        <ChatBody :dealerChat="dealerChat" ref="ChatBody" />
        <ImagePopup />
    </div>
</template>

<script>
import { mapMutations, mapActions, mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
import { pauseAllVoicePlayback } from '@/utils/voicePlayback'
import 'lazysizes'
export default {
    name: "ChatIndex",
    props: {
        task: {
            type: Boolean,
            default: false
        },
        meetings: {
            type: Boolean,
            default: false
        },
        dealerChat: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Sidebar: () => import('./components/Sidebar'),
        ChatBody: () => import('./components/ChatBody'),
        ImagePopup: () => import('./components/ImagePopup')
    },
    beforeRouteLeave(to, from, next) {
        Promise.resolve(this.persistActiveDraft())
            .catch(() => {})
            .finally(() => next())
    },
    created() {
        this.getOpenChat()
    },
    computed: {
        ...mapState({
            activeChat: state=> state.chat.activeChat,
            chatList: state => state.chat.chatList
        })
    },
    methods: {
        ...mapActions({
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat',
        }),
        ...mapMutations({
            SET_ACTIVE_CHAT: 'chat/SET_ACTIVE_CHAT',
            SET_ACTIVE_CHAT_FROM_UID: 'chat/SET_ACTIVE_CHAT_FROM_UID',
            createVirtualChat: 'chat/CREATE_VIRTUAL_CHAT',
            setValueState: 'chat/setValueState'
        }),
        persistActiveDraft() {
            return this.$refs.ChatBody?.$refs.ChatFooter?.persistDraftByChat?.()
        },
        async getOpenChat() {
            const query = this.$route.query
         
            if(query && query.chat_id) {
                try {
                    const chat = await this.getCurrentChat(query.chat_id)
                    if (!chat || chat.chat_uid !== query.chat_id) return
                    await this.getPinMessages()
                    if (!this.activeChat.is_public)
                        this.$socket.client.emit('chat_status_user', { chat_uid: this.activeChat.chat_uid, user_uid: this.activeChat.recipient.id })
                } catch(error) {
                    if(!this.dealerChat)
                        this.$router.push({name: 'chat'})
                    errorHandler({error})
                }
            } else if(query && query.user) {
                this.setValueState({name: 'dialogLoading', value: true})
                const res = await this.getPrivateChat(query.user)
                setTimeout(async() => {
                    const find = this.chatList.findIndex(el => el.chat_uid === res.chat_uid)
                    if(find !== -1){
                        const chat = await this.getCurrentChat(res.chat_uid)
                        if (!chat || chat.chat_uid !== res.chat_uid) return
                        //this.SET_ACTIVE_CHAT_FROM_UID(res.chat_uid)
                        this.$router.replace({query: {chat_id: res.chat_uid}})
                    } else {
                        if(res.chat_uid) {
                            this.$router.replace({query: {chat_id: res.chat_uid}})
                            const chat = await this.getCurrentChat(res.chat_uid)
                            if (!chat || chat.chat_uid !== res.chat_uid) return
                            await this.getPinMessages()
                            if (!res.is_public)
                                this.$socket.client.emit('chat_status_user', { chat_uid: res.chat_uid, user_uid: res.recipient.id })
                        } else {
                            res['chat_author'] = this.$store.state.user.user
                            this.createVirtualChat(res)
                        }
                    }
                    this.setValueState({name: 'dialogLoading', value: false})
                }, 1000);
            }
        },
        async getPinMessages() {
            try {
                await this.$store.dispatch('chat/getPinMessage', {
                    page_size: 10
                })
            } catch(e) {
                console.log(e)
            }
        }
    },
    mounted() {
        eventBus.$on('RELOAD_ACTIVE_CHAT', () => {
            this.SET_ACTIVE_CHAT(null)
            setTimeout(() => {
                this.getOpenChat()
            }, 200)
        })
    },
    beforeDestroy() {
        this.persistActiveDraft()
        pauseAllVoicePlayback({ reason: 'chat-component-destroy', broadcast: false })
        eventBus.$off('RELOAD_ACTIVE_CHAT')
        this.SET_ACTIVE_CHAT(null)
    }
}
</script>

<style lang="scss">
@import "./assets/css/style.scss";
</style>
