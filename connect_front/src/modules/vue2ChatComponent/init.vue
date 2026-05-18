<template>
    <div>
        <component v-if="visible" :is="shareDrawer" />
        <component v-if="visibleCreate" :is="createModal" />
    </div>
</template>

<script>
import chat from './store/index'
import share from './store/share'
import ChatEventBus from './utils/ChatEventBus'
import eventBus from '@/utils/eventBus'
import soketsMessages from './soketsMessages'
import visibilityManager from '@/utils/visibilityManager.js'
import notificationChannel from '@/utils/notificationChannel.js'
import { mapActions, mapState } from 'vuex'
import { clearMessageHtml } from './utils/index.js'
import { errorHandler } from '@/utils/index.js'
import { isVoiceMessageFile } from '@/utils/voice'

export default {
    name: 'ChatInit',
    mixins: [soketsMessages],
    created() {
        if(!this.$store.hasModule('chat'))
            this.$store.registerModule('chat', chat)

        if(!this.$store.hasModule('share'))
            this.$store.registerModule('share', share)

        visibilityManager.init()
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            activeChat: state => state.chat.activeChat
        }),
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        visible() {
            return this.$store.state.share.visible
        },
        visibleCreate() {
            return this.$store.state.chat.createChat
        },
        shareDrawer() {
            if(this.visible)
                return () => import('./components/ShareDrawer')
            return null
        },
        createModal() {
            if(this.visibleCreate)
                return () => import('./components/ChatCreate')
            return null
        }
    },
    data() {
        return {
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ',
            chatListPrefetchTimer: null
        }
    },
    methods: {
        ...mapActions({
            getSidebarChat: 'chat/getSidebarChat'
        }),
        openStandaloneChatWindow(data, key, isMentions = false) {
            const query = {}
            if (isMentions) {
                query.message_id = data.message_uid
            }

            const routeData = this.$router.resolve({
                name: 'chat-window',
                params: { id: data.chat_uid },
                query
            })

            const features = [
                'popup=yes',
                'width=480',
                'height=820',
                'left=120',
                'top=80',
                'menubar=no',
                'toolbar=no',
                'location=no',
                'status=no',
                'resizable=yes',
                'scrollbars=no'
            ].join(',')

            const openedWindow = window.open(routeData.href, 'chat-window-standalone', features)
            if (openedWindow) {
                openedWindow.focus()
            }

            this.$notification.close(key)

            try {
                notificationChannel.broadcastClose(key)
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        hasChatRoute() {
            const routes = this.$store.state.navigation?.routerList || []
            return routes.some(route => route?.name === 'chat' && route?.isShow !== false)
        },
        shouldPrefetchChatList() {
            if (this.isStandaloneChatWindow) return false
            if (!this.hasChatRoute()) return false

            return !['chat', 'chat-contact', 'chat-body'].includes(this.$route.name)
        },
        async prefetchChatListIfNeeded() {
            if (!this.shouldPrefetchChatList()) return
            if (this.$store.state.chat.chatListPage > 0 || this.$store.state.chat.chatList.length > 0) return

            try {
                await this.getSidebarChat({ prefetch: true })
            } catch (error) {
                if (error?.__CANCEL__) return
                errorHandler({ error, show: false })
            }
        },
        openNoty(data, key, isMentions = false) {
            if (this.isStandaloneChatWindow) {
                const sameChat = this.$route.params.id === data.chat_uid

                if (sameChat) {
                    if (isMentions) {
                        const nextQuery = JSON.parse(JSON.stringify(this.$route.query || {}))
                        nextQuery.message_id = data.message_uid

                        this.$router.replace({
                            name: 'chat-window',
                            params: { id: data.chat_uid },
                            query: nextQuery
                        }).then(() => {
                            eventBus.$emit('CHAT_SEARCH_USER_TAGS')
                        }).catch(() => {})
                    } else {
                        ChatEventBus.$emit('arreaScrollDown')
                    }
                } else {
                    const query = {}
                    if (isMentions)
                        query.message_id = data.message_uid

                    this.$router.push({
                        name: 'chat-window',
                        params: { id: data.chat_uid },
                        query
                    }).catch(() => {})
                }

                this.$notification.close(key)
                this.$notification.destroy()
                return
            }

            if (this.isMobile) {
                const sameChat = this.$route.name === 'chat-body' && this.$route.params.id === data.chat_uid

                if (sameChat) {
                    if (isMentions) {
                        const nextQuery = JSON.parse(JSON.stringify(this.$route.query || {}))
                        nextQuery.message_id = data.message_uid

                        this.$router.replace({
                            name: 'chat-body',
                            params: { id: data.chat_uid },
                            query: nextQuery
                        }).then(() => {
                            eventBus.$emit('CHAT_SEARCH_USER_TAGS')
                        }).catch(e => {})
                    } else {
                        ChatEventBus.$emit('arreaScrollDown')
                    }
                } else {
                    const query = {}
                    if (isMentions)
                        query.message_id = data.message_uid

                    this.$router.push({
                        name: 'chat-body',
                        params: { id: data.chat_uid },
                        query
                    }).catch(e => {})
                }
            } else {
                const parseQuery = { chat_id: data.chat_uid }
                if (isMentions)
                    parseQuery.message_id = data.message_uid

                if (this.$route.name === 'chat') {
                    const currentChatId = this.$route.query?.chat_id || null
                    const sameChat = currentChatId === data.chat_uid

                    const nextQuery = JSON.parse(JSON.stringify(this.$route.query || {}))
                    nextQuery.chat_id = data.chat_uid

                    if (isMentions)
                        nextQuery.message_id = data.message_uid
                    else
                        delete nextQuery.message_id

                    this.$router.replace({ query: nextQuery })
                        .then(() => {
                            if (sameChat) {
                                if (isMentions)
                                    eventBus.$emit('CHAT_SEARCH_USER_TAGS')
                                else
                                    ChatEventBus.$emit('arreaScrollDown')
                            } else {
                                eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                            }
                        })
                } else {
                    this.$router.push({ name: 'chat', query: parseQuery })
                        .then(() => {
                            eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                        })
                        .catch(e => {})
                }
            }

            this.$notification.close(key)
            this.$notification.destroy()

            try {
                notificationChannel.broadcastCloseAll()
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        async getMessageCount() {
            try {
                await this.$store.dispatch('chat/getMessageCount')
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        getNotificationFallbackText(message) {
            const attachments = Array.isArray(message?.attachments) ? message.attachments : []

            if (attachments.length && attachments.every(item => isVoiceMessageFile(item))) {
                return this.$t('chat.voice_message')
            }

            return this.$t('chat.file_and_image')
        }
    },
    mounted() {
        this.getMessageCount()
        this.chatListPrefetchTimer = setTimeout(() => {
            this.prefetchChatListIfNeeded()
        }, 2000)

        this.notifyUnsubChannel = notificationChannel.subscribe(msg => {
            try {
                if (!msg) return
                if (msg.type === 'close' && msg.key) {
                    this.$notification.close(msg.key)
                    return
                }
                if (msg.type === 'close_all') {
                    try {
                        this.$notification.destroy()
                    } catch(e) {}
                }
            } catch(e) {}
        })

        ChatEventBus.$on('CHAT_SHOW_NEW_MESSAGE', data => {
            if(this.activeChat?.chat_uid === data?.chat_uid)
                return

            const key = data.message_uid
            let isMentions = false
            const previewMessage = data.message_forwarded || data
            const previewAttachments = Array.isArray(previewMessage.attachments) ? previewMessage.attachments : []

            let messageImages = []
            let messageFiles = []
            if(previewAttachments.length) {
                messageImages = previewAttachments.filter(f => f.is_image)
                messageFiles = previewAttachments.filter(f => f.obj_type === 'file' && !f.is_image)
            }
            const hasOnlyVoiceFiles = messageFiles.length > 0 && messageFiles.every(file => isVoiceMessageFile(file))

            let title = data.is_public ? data.chat_name : data.message_author?.full_name || this.$t('chat.notification_default_title')
            if(data.is_support) {
                if(!this.user.is_support)
                    title = this.$t('chat.support_name', { name: this.appName })
            }

            if(data.mentions?.length && this.user) {
                const find = data.mentions.find(f => f === this.user.id)
                if(find)
                    isMentions = true
            }

            const shouldShowQuickReplyButton = !this.isMobile && !this.isStandaloneChatWindow

            this.$notification.open({
                message: h => {
                    return h('div', { class: 'notify_head' }, [
                        h('div', { class: 'notify_title' }, title),
                        h('div', { class: 'notify_date' }, `${this.$moment(data.created).format('HH:mm')}`)
                    ])
                },
                description: h => {
                    const forwarded = data.message_forwarded
                    const forwardedAuthor = forwarded?.message_author

                    const authorName = forwardedAuthor
                        ? (forwardedAuthor.last_name || forwardedAuthor.first_name
                            ? `${forwardedAuthor.last_name || ''} ${forwardedAuthor.first_name || ''}`
                            : forwardedAuthor.full_name)
                        : ''

                    const authorAvatar = forwardedAuthor?.avatar?.path || null
                    return h(
                        'div',
                        { class: 'notify_message' },
                        [
                            forwarded && h(
                                'div',
                                { class: 'notify_forwarded flex items-center gap-1 mb-1' },
                                [
                                    h('i', {
                                        class: 'fi fi-rr-undo mr-1',
                                        attrs: { title: this.$t('chat.forwared_message') }
                                    }),
                                    h('span', { class: 'text-xs' }, this.$t('chat.forwared_from')),
                                    authorAvatar
                                        ? h('a-avatar', {
                                            attrs: {
                                                src: authorAvatar,
                                                size: 14
                                            }
                                        })
                                        : null,
                                    h('span', { class: 'text-xs font-medium' }, authorName)
                                ]
                            ),

                            data.message_reply && h(
                                'div',
                                {
                                    class: 'notify_reply',
                                    domProps: {
                                        innerHTML: this.$t('chat.notify_reply_prefix', {
                                            text: data.message_reply.text
                                                ? clearMessageHtml(data.message_reply.text)
                                                : this.getNotificationFallbackText(data.message_reply)
                                        })
                                    }
                                }
                            ),

                            data.is_public && data.message_author && h(
                                'div',
                                { class: 'notify_author flex items-center gap-1 mb-1' },
                                [
                                    data.message_author.avatar?.path
                                        ? h('a-avatar', { attrs: { src: data.message_author.avatar.path, size: 14 } })
                                        : null,
                                    h('span', { class: 'text-xs font-medium' }, (() => {
                                        const n = (data.message_author.full_name || '').split(' ')
                                        return `${n[0]}${n[1] ? ' ' + n[1].charAt(0).toUpperCase() + '.' : ''}:`
                                    })())
                                ]
                            ),

                            h(
                                'div',
                                {
                                    class: 'notify_message_text',
                                    domProps: {
                                        innerHTML: clearMessageHtml(
                                            previewMessage.text || this.getNotificationFallbackText(previewMessage)
                                        )
                                    }
                                }
                            ),

                            messageImages.length
                                ? h(
                                    'div',
                                    {
                                        class: `notify_gallery ${messageImages.length > 1 && 'mult_gal'} ${data.text && 'ty'}`
                                    },
                                    messageImages.map(image =>
                                        h(
                                            'div',
                                            {
                                                class: `notify_image_wrap ${messageImages.length > 1 ? 'mult' : 'one'} ${data.text && 'te'}`
                                            },
                                            [h('img', { attrs: { src: image.path } })]
                                        )
                                    )
                                )
                                : h('div'),

                            messageFiles.length && !hasOnlyVoiceFiles
                                ? h(
                                    'div',
                                    {
                                        class: `notify_files ${data.text && 'ty'} ${messageImages.length && 'image_gal'}`
                                    },
                                    messageFiles.map(file =>
                                        h(
                                            'div',
                                            { class: 'notify_file_wrap' },
                                            [
                                                h('i', { class: 'fi fi-rr-file' }),
                                                h('span', file.name)
                                            ]
                                        )
                                    )
                                )
                                : h('div'),

                            shouldShowQuickReplyButton
                                ? h(
                                    'div',
                                    { class: 'notify_actions' },
                                    [
                                        h(
                                            'a-button',
                                            {
                                                attrs: {
                                                    type: 'primary',
                                                    size: 'small'
                                                },
                                                on: {
                                                    click: event => {
                                                        event.stopPropagation()
                                                        this.openStandaloneChatWindow(data, key, isMentions)
                                                    }
                                                }
                                            },
                                            this.$t('chat.quick_reply')
                                        )
                                    ]
                                )
                                : h('div')
                        ]
                    )
                },
                duration: visibilityManager.getNotifyDuration(),
                top: '0px',
                key,
                closeIcon: h => {
                    if(this.isMobile) {
                        return h('div', { class: 'notify_close' }, this.$t('chat.notify_close'))
                    } else
                        return h('i', { class: 'fi fi-rr-cross' })
                },
                icon: h => {
                    return h('a-avatar', {
                        attrs: {
                            flaticon: true,
                            src: !data.is_public && data.message_author?.avatar?.path ? data.message_author.avatar.path : null,
                            icon: 'fi-rr-comment-dots'
                        }
                    })
                },
                class: 'cursor-pointer notify_popover chat_notify_popover',
                onClick: ()=> this.openNoty(data, key, isMentions),
                onClose: () => {
                    try {
                        this.$notification.close(key)
                    } catch(e) {}
                    try {
                        notificationChannel.broadcastClose(key)
                    } catch(e) {}
                }
            })
        })
    },
    beforeDestroy() {
        if (this.chatListPrefetchTimer) {
            clearTimeout(this.chatListPrefetchTimer)
            this.chatListPrefetchTimer = null
        }

        ChatEventBus.$off('CHAT_SHOW_NEW_MESSAGE')
        visibilityManager.destroy()
        if (this.notifyUnsubChannel)
            this.notifyUnsubChannel()
    }
}
</script>

<style lang="scss">
.chat_notify_popover {
    .ant-notification-notice-message {
        width: 100%;
        min-width: 0;
    }

    .notify_head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 12px;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        overflow: hidden;
    }

    .notify_title {
        width: 100%;
        min-width: 0;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }

    .notify_date {
        min-width: fit-content;
        white-space: nowrap;
    }

    .notify_message,
    .notify_message_text,
    .notify_reply {
        min-width: 0;
        overflow-wrap: anywhere;
        word-break: break-word;
    }

    .notify_message {
        a {
            overflow-wrap: anywhere;
            word-break: break-all;
        }
    }

    .notify_actions {
        margin-top: 12px;
        display: flex;
        justify-content: flex-end;
    }
}
</style>
