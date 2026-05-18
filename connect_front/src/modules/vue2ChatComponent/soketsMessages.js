import { mapMutations, mapState, mapActions } from 'vuex'
import ChatEventBus from './utils/ChatEventBus'
import SoundMaster from '@/utils/soundMaster'
import TitleBlinker from '@/utils/titleBlinker'
import VisibilityHub from '@/utils/visibilityHub'
import notificationChannel from '@/utils/notificationChannel.js'
import { getNotificationSoundEnabled } from '@/modules/Notifications/soundSettings'

let userTimer;

function unwrapSocketPayload(payload) {
    if (payload && typeof payload === 'object' && payload.data && typeof payload.data === 'object') {
        return payload.data
    }

    return payload
}

function toBoolean(value) {
    if (typeof value === 'boolean') return value
    if (typeof value === 'string') {
        const normalized = value.trim().toLowerCase()
        if (normalized === 'true') return true
        if (normalized === 'false') return false
    }

    return Boolean(value)
}

function normalizeMembers(data) {
    if (!data || !Array.isArray(data.members)) return data

    return {
        ...data,
        members: data.members.map(member => ({
            ...member,
            is_moderator: toBoolean(member.is_moderator)
        }))
    }
}

function isSameUserId(left, right) {
    if (left == null || right == null) return false
    return String(left) === String(right)
}

export default {
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            user: state => state.user.user,
            chatList: state => state.chat.chatList,
            chatMessage: state => state.chat.chatMessage,
            config: state => state.config.config,
            isMobile: state => state.isMobile
        })
    },
    methods: {
        ...mapActions({
            getChatMembers: 'chat/getChatMembers',
            getMessageCount: 'chat/getMessageCount'
        }),
        ...mapMutations({
            setNewCreatedChat: 'chat/SET_NEW_CREATED_CHAT',
            addMessage: 'chat/ADD_MESSAGE',
            ADD_CHAT_SPLICE: 'chat/ADD_CHAT_SPLICE',
            getMessages: 'chat/getMessage',
            setPin: 'chat/PIN_MESSAGE',
            setUnpin: 'chat/UNPIN_MESSAGE',
            unpinAll: 'chat/UNPIN_ALL',
            renameChat: 'chat/RENAME_CHAT',
            deleteMember: 'chat/DELETE_MEMBER',
            initMembersList: 'chat/INIT_MEMBERS_LIST',
            CHAT_PLUS_MEMBERS: 'chat/CHAT_PLUS_MEMBERS',
            leaveChat: 'chat/LEAVE_CHAT',
            addLastMessage: 'chat/addLastMessage',
            removeMessage: 'chat/removeMessage',
            setStatusUser: 'chat/setStatusUser',
            setOnline: 'chat/setOnlineUser',
            setOffline: 'chat/setOfflineUser',
            incrimentMessageCount: 'chat/incrimentMessageCount',
            applyChatReadProgress: 'chat/APPLY_CHAT_READ_PROGRESS',
            setChatReadedAtByChatId: 'chat/SET_CHAT_READED_AT_BY_CHAT_ID',
            incrementMenuCounter: 'navigation/INCREMENT_MENU_COUNTER',
            CHANGE_SOCKET_MODER: 'chat/CHANGE_SOCKET_MODER',
            CHANGE_CHAT_AUTHOR: 'chat/CHANGE_CHAT_AUTHOR'
        }),
        async playAudioChat() {
            if(!this.isMobile) {
                const soundEnabled = await getNotificationSoundEnabled(this.user?.id)
                if(soundEnabled) {
                    await SoundMaster.emit('chat_new_message')
                }
                if (SoundMaster.isLeader() && !VisibilityHub.anyVisible()) {
                    TitleBlinker.bump(1, [this.$t('tab_notify1'), this.$t('tab_notify2'), this.$t('tab_notify3')])
                }
            }
        },

        setDataFromChat(data) {
            const myAuthor = this.user.id
            let name =
        myAuthor !== data.chat_author.id
            ? data.chat_author.full_name
            : data.recipient !== undefined
                ? data.recipient?.full_name
                : data.name
            let value = {
                ...data,
                name: data.name ? data.name : name,
                last_sent: new Date(data.last_sent),
                no_create: false
            }
            this.setNewCreatedChat({ value, user: this.user })
            if (this.user.id !== data.chat_author.id) {
                this.playAudioChat()
            }
        }
    },
    sockets: {
        join_chat({ data }) {
            if (this.$route.name !== 'chat' && this.chatList.length === 0) {
            } else this.setDataFromChat(data)
        },
        message_reaction({ data }) {
            if(data?.author !== this.user?.id)
                this.$store.commit('chat/MESSAGE_SOCKET_REACT', { data })
        },
        message_update({ data }) {
            this.$store.commit('chat/UPDATE_MESSAGE_FROM_SOCKET', { data })
        },
        task_update(payload) {
            const task = unwrapSocketPayload(payload)
            if (!task?.id) return

            this.$store.commit('chat/UPDATE_TASK_SHARE_FROM_SOCKET', { task })
        },
        message({ data }) {
            try {
                const isIncoming = !isSameUserId(this.user?.id, data.message_author?.id)
                const activeChatUid = this.activeChat?.chat_uid || null
                const isSameActiveChat = activeChatUid === data?.chat_uid

                if (isIncoming && !isSameActiveChat) {
                    this.$store.commit('chat/REGISTER_LOCAL_UNREAD_MESSAGE', {
                        chat_uid: data.chat_uid,
                        message: data
                    })
                }

                this.addMessage(data)
                this.addLastMessage(data)

                if (isSameActiveChat && !isIncoming) {
                    // Свое сообщение в открытом чате не должно поднимать unread.
                    // Сразу локально считаем, что для текущей вкладки unread = 0.
                    this.applyChatReadProgress({
                        chat_uid: data.chat_uid,
                        data: {
                            chat: data.chat_uid,
                            my_readed_at: this.activeChat?.my_readed_at || null,
                            unread_count: 0,
                            unread_mention_count: 0
                        }
                    })
                    this.getMessageCount()
                    return
                }

                if ((!activeChatUid && isIncoming) ||
          (isSameActiveChat && isIncoming && this.activeChat.scrolled) ||
          ((activeChatUid !== data.chat_uid) && isIncoming)) {
                    ChatEventBus.$emit('CHAT_SHOW_NEW_MESSAGE', data)

                    if(activeChatUid !== data?.chat_uid) {
                        this.incrimentMessageCount({chat_uid: data.chat_uid, data})
                        this.incrementMenuCounter({
                            name: 'chat',
                            data
                        })
                        this.playAudioChat()
                    } else {
                        this.incrimentMessageCount({chat_uid: data.chat_uid, data})
                    }

                } else if (isSameActiveChat && isIncoming) {
                    ChatEventBus.$emit('CHAT_SHOW_NEW_MESSAGE', data)
                }
            } catch (e) {
                console.log(e)
            }
        },
        chat_pin_message({ data }) {
            this.setPin(data)
            ChatEventBus.$emit('PINNED_MESSAGE', data)
        },
        chat_unpin_message({ data }) {
            this.setUnpin(data)
        },
        chat_unpin_all_message({ data }) {
            this.unpinAll(data)
        },
        chat_rename({ data }) {
            this.renameChat(data)
        },
        chat_add_user({ data }) {
            this.$nextTick(() => {
                clearTimeout(userTimer)
                userTimer = setTimeout(() => {
                    this.$store.commit('chat/SET_LOADING_INFOCHAT', true)
                    this.initMembersList(data)
                    this.CHAT_PLUS_MEMBERS(data)
                    this.getChatMembers({ chat: data.chat_uid })
                    this.$store.commit('chat/SET_LOADING_INFOCHAT', false)
                }, 1000)
            })
        },
        chat_delete_user({ data }) {
            if (data?.members?.[0]?.user) {
                this.deleteMember({ chat: data.chat_uid, user: data.members[0].user })
            } else {
                console.error(this.$t('chat.failed_to_remove_user'))
            }
        },
        chat_change_rights({ data }) {
            const normalizedData = normalizeMembers(unwrapSocketPayload(data))
            if (!normalizedData) return

            this.CHANGE_SOCKET_MODER({
                data: normalizedData,
                user: this.user
            })
        },
        change_chat_author(payload) {
            const normalizedData = unwrapSocketPayload(payload)
            if (!normalizedData) return

            this.CHANGE_CHAT_AUTHOR({
                data: normalizedData,
                user: this.user
            })
        },
        leave_room({ data }) {
            this.leaveChat({ chat: data.chat_uid })
        },
        chat_delete_message({ data }) {
            if (data?.message_uid) {
                try {
                    this.$notification.close(data.message_uid)
                } catch (e) {}

                try {
                    notificationChannel.broadcastClose(data.message_uid)
                } catch (e) {}
            }

            if (data?.chat_uid) {
                this.$store.dispatch('chat/getUnreadMessageCountByChatId', data.chat_uid)
                this.$store.dispatch('chat/getLastMessageByChatId', data.chat_uid)
            }

            this.$store.dispatch('chat/getMessageCount')
            this.removeMessage(data)
        },
        chat_status_user(data) {
            this.setStatusUser(data)
        },
        chat_online_user(data) {
            this.setOnline({ user: data.user })
        },
        chat_offline_user(data) {
            this.setOffline({ user: data.user, last_activity: data.last_activity })
        },
        chat_member_update_last_message(data) {
            const chatUid = data?.chat
            const currentUserId = this.user?.id
            const eventUserId = data?.user_id

            if (chatUid && currentUserId != null && eventUserId != null && String(currentUserId) === String(eventUserId)) {
                // Это синк между разными сессиями одного и того же пользователя.
                // Принимаем не просто факт "прочитано", а точный остаток unread с бэка.
                this.applyChatReadProgress({
                    chat_uid: chatUid,
                    data
                })
                this.getMessageCount()
                return
            }

            this.setChatReadedAtByChatId({
                chatUid,
                readedAt: data.created
            })
        }
    },
    mounted() {
        ChatEventBus.$on('chat_member_update_last_message', data => {
            // После успешного read_progress фронт досылает событие в socket,
            // чтобы другие вкладки того же пользователя получили тот же остаток unread.
            this.$socket.client.emit('chat_member_update_last_message', {
                ...(data || {}),
                user_id: this.user?.id || null
            })
        })
    },
    beforeDestroy() {
        ChatEventBus.$off('chat_member_update_last_message')
    }
}
