<template>
    <div
        class="chat_contact flx wfl"
        :class="[active && 'active', chat.is_support && 'support_chat']"
        @click="selectChat()">
        <div class="awatar_wrapper">
            <template v-if="chat.is_public">
                <a-avatar
                    v-if="chat.is_support"
                    class="chat_contact__avatar chat_contact__avatar--group"
                    :size="38"
                    :key="chat.id"
                    src="/img/support_avatar.jpg" />
                <a-avatar
                    v-else
                    class="chat_contact__avatar chat_contact__avatar--group"
                    :size="38"
                    :style="chat.color ? `backgroundColor:${chat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                    {{ avatarText }}
                </a-avatar>
            </template>
            <template v-else>
                <a-badge :color="statusColor">
                    <a-avatar
                        v-if="chat.avatar"
                        :key="chat.id"
                        :size="38"
                        :style="chat.color ? `backgroundColor:${chat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'"
                        :src="chat.avatar.path ? chat.avatar.path : null" />
                    <a-avatar
                        v-else
                        :size="38"
                        :src="getAvatar"
                        :style="chat.color ? `backgroundColor:${chat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                        {{ avatarText }}
                    </a-avatar>
                </a-badge>
            </template>
        </div>
        <div class="user_item__body pl-2 truncate" style="width: 100%">
            <div class="name flex justify-between items-center" :title="chat.name">
                <div class="truncate font-semibold flex items-center">
                    <i v-if="chat.is_public && !chat.is_support" class="fi fi-rr-users text-xs mr-1"></i>
                    <template v-if="chat.recipient && chat.recipient.is_support && !chat.is_support">
                        <span 
                            class="text-xs mr-1"
                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                            :content="$t('chat.support')">
                            <i class="fi fi-rr-headset"></i>
                        </span>
                    </template>
                    <span class="truncate text-sm chat_name"> {{ contactName }} </span>
                </div>
                <span v-if="chat.last_message || hasDraftPreview" class="text-xs pl-1 gray flex items-center">
                    <i
                        v-if="showLastMessageReadStatus"
                        class="chat_contact__read_status fi mr-1"
                        :class="isLastMessageReaded ? 'fi-rr-check-double' : 'fi-rr-check'"></i>
                    {{ lastSend }}
                </span>
            </div>

            <div class="flex justify-between align-center">
                <ChatContactLastMessage 
                    v-if="chat.last_message || hasDraftPreview" 
                    :selectChat="selectChat"
                    :draft="chatDraft"
                    :chat="chat" />
                <template v-else>
                    <div v-if="chat.is_support" class="message_desc">
                        {{ $t('chat.support_message') }}
                    </div>
                </template>
                <div class="ml-1 flex items-center gap-1">
                    <a-badge
                        v-if="chat.new_message_count > 0"
                        :count="chat.new_message_count"
                        :number-style="{ backgroundColor: primaryColor }" />
                    <div
                        v-if="chat.new_mention_count > 0"
                        class="mention_count">
                        @ <span>{{ chat.new_mention_count }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapMutations, mapState } from 'vuex'
export default {
    name: "ChatContact",
    components: {
        ChatContactLastMessage: () => import('./ChatContactLastMessage.vue')
    },
    props: {
        chat: {
            type: Object,
            required: true
        }
    },
    data() {
        return{
            listUsers:[],
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ'
        }

    },
    sockets:{
        chat_online_user(data) {
            const userId = data.user
            const foundUserIndex = this.listUsers.findIndex(user => user.user_uid === userId)

            if (foundUserIndex > -1) {
                this.listUsers[foundUserIndex].online = true
            }
        },
        chat_offline_user(data) {

            const userId = data.user
            const foundUser = this.listUsers.find(user => user.user_uid === userId)
            if (foundUser) {
                foundUser.online = false
                foundUser.last_activity = data.last_activity
            }
        },
        chat_status_user(data) {
            const socketUser = data?.members

            if (!socketUser?.user_uid) {
                return
            }

            const foundUser = this.listUsers.find(user => user.user_uid === socketUser.user_uid)
            if (foundUser) {

                foundUser.user_uid = socketUser.user_uid
                foundUser.last_activity = socketUser.last_activity
                foundUser.online = socketUser.online
            } else
                this.listUsers.push(socketUser)
        },
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            chatDrafts: state => state.chat.chatDrafts,
            user: state => state.user.user,
            isMobile: state => state.isMobile,
            primaryColor: state => state.config.primaryColor
        }),
        chatDraft() {
            return this.chatDrafts?.[this.chat.chat_uid] || null
        },
        hasDraftPreview() {
            return !!this.chatDraft
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        contactName() {
            if(this.user.is_support) {
                return this.chat.name
            } else {
                if(this.chat.is_support)
                    return this.$t('chat.support_name', { name: this.appName })
            }
            return this.chat.name
        },
        avatarText() {
            if(this.chat.is_public) {
                return this.chat.name.charAt(0).toUpperCase()
            } else {
                const n = this.chat.name.split(' ')
                return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}${n[2] ? n[2].charAt(0).toUpperCase() : ''}`
            }
        },
        statusColor() {
            if(this.chat.recipient?.last_activity) {
                if(this.isOnline)
                    return '#52c41a'
                else
                    return '#f5222d'
            } else
                return '#808080'
        },
        firstCheck() {
            if(this.chat?.recipient?.id)
                return this.$store.getters['user/getUserFirstCheck'](this.chat.recipient.id)
            else
                return null
        },
        isOnline() {
            if(this.chat?.recipient?.id)
                return this.$store.getters['user/getUserStatus'](this.chat.recipient.id)
            else
                return null
        },
        isLastMessageOwn() {
            return !!(this.user?.id && this.chat?.last_message?.message_author?.id === this.user.id)
        },
        showLastMessageReadStatus() {
            return !this.hasDraftPreview && this.isLastMessageOwn
        },
        isLastMessageReaded() {
            const readedAtDate = this.$moment(this.chat?.readed_at)
            const messageSentDate = this.$moment(this.chat?.last_message?.created)

            if (!readedAtDate.isValid() || !messageSentDate.isValid()) {
                return false
            }

            return !readedAtDate.isBefore(messageSentDate)
        },
        lastSend() {
            const lastSent = this.hasDraftPreview ? this.chatDraft.updatedAt : this.chat.last_sent
            const moment = this.$moment(lastSent)

            if (!moment.isValid()) {
                return ''
            }

            if(moment.isBefore(this.$moment(), 'days')) {
                if(moment.isBefore(this.$moment(), 'week'))
                    return moment.format('DD.MM.YY')
                else
                    return moment.format('dd')
            } else
                return moment.format('HH:mm')
        },
        getAvatar() {
            if (this.chat?.chat_author || this.chat?.recipient) {
                if (this.chat?.chat_author?.id && this.chat?.chat_author?.id !== this.user?.id) {
                    this.$socket.client.emit('chat_status_user', {chat_uid: "0", user_uid: this.chat.chat_author.id})
                    return this.chat.chat_author.avatar?.path || null
                } else {
                    if (this.chat?.recipient) {
                        this.$socket.client.emit('chat_status_user', {chat_uid: "0", user_uid: this.chat.recipient.id})
                        return this.chat.recipient.avatar?.path || null
                    }
                }
            }
            return ''
        },
        active() {
            if(this.activeChat?.chat_uid === this.chat.chat_uid)
                return true
            else
                return false
        }
    },
    created() {
        if(!this.firstCheck && this.chat.recipient?.last_activity) {
            this.$store.commit('user/SET_ONLINE_USER_EVENT', this.chat.recipient)
        }
    },
    methods: {
        ...mapMutations({
            SET_ACTIVE_CHAT: 'chat/SET_ACTIVE_CHAT',
            SET_CHAT_MESSAGE: 'chat/SET_CHAT_MESSAGE',
            SET_CHAT_MESSAGE_MODAL: 'chat/SET_CHAT_MESSAGE_MODAL'
        }),
        async selectChat() {
            /*if(this.chat.new_mention_count || this.chat.new_message_count) {
                this.$store.commit('navigation/CHANGE_MENU_COUNT', {
                    name: 'chat',
                    count: this.chat.new_message_count,
                    mentions: this.chat.new_mention_count
                })
            }*/
            if(this.isMobile) {
                if (this.isStandaloneChatWindow) {
                    this.$router.push({
                        name: 'chat-window',
                        params: {
                            id: this.chat.chat_uid
                        }
                    })
                    return
                }
                this.$router.push({
                    name: 'chat-body',
                    params: {
                        id: this.chat.chat_uid
                    }})
            } else {
                const chat = await this.$store.dispatch('chat/getCurrentChat', this.chat.chat_uid)
                if (!chat || chat.chat_uid !== this.chat.chat_uid) return

                if(this.activeChat && !this.activeChat.is_public)
                    this.$socket.client.emit('chat_status_user', {chat_uid: this.activeChat.chat_uid, user_uid: this.activeChat.recipient.id})

                const query = JSON.parse(JSON.stringify(this.$route.query))
                if(query?.chat_id !== this.chat.chat_uid) {
                    query.chat_id = this.chat.chat_uid
                    this.$router.push({query})
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.mention_count{
    min-width: 20px;
    height: 20px;
    min-height: 20px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    color: var(--blue);
    background-color: #e8ecfa;
    padding: 0 5px;
    font-size: 12px;
}
.chat_contact{
    &.support_chat{
        .chat_name{
            color: #4776fe;
        }
    }
    &__avatar{
        &--group{
            border-radius: 12px;
        }
    }
    &__read_status{
        color: var(--blue);
        font-size: 10px;
        line-height: 1;
    }
}
</style>

<style lang="scss">
.chat_contact{
    padding: 10px;
    cursor: pointer;
    align-items: center;
    .message_desc{
        font-size: 13px;
        color: #747679;
    }
    &.active{
        background: var(--primaryHover);
    }
    .user_item__body{
        .name{
            font-size: 15px;
            .team_icon{
                font-size: 12px;
                margin-left: 5px;
            }
        }
    }
}


    /*.user_list_wrap {*/
        /*max-height: 300px;*/
        /*padding: 15px;*/
        /*padding-top: 0;*/
        /*overflow-y: scroll;*/
    /*}*/

    .ant-badge-dot {
        top: 5px;
        right: 3px;

        width: 8px !important;
        height: 8px !important;
    }

</style>
