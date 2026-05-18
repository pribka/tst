<template>
    <component :is="drawerComp" />
</template>

<script>
import eventBus from '@/utils/eventBus';
import store from "./store/index"
import Socket from './socket'
import { mapActions, mapState } from 'vuex'
import {getColor, getBackground, getLastNotificationLink, linkifyNotificationHtml, openNotificationLink, getNotificationIconClass} from './utils'
import push from './mixins/push'
import visibilityManager from '@/utils/visibilityManager.js'
import notificationChannel from '@/utils/notificationChannel.js'
import notySyncChannel from '@/utils/notySyncChannel'
import { closeBrowserPushNotification } from '@/utils/browserPushNotifications'

const loadNotifyDrawer = () => import(
    /* webpackChunkName: "notify-show-drawer", webpackPrefetch: true */
    './views/NotifyDrawer.vue'
)

const COMMENT_NOTIFICATION_ICON_NAMES = [
    'комментарии',
    'comments'
]

const DEFAULT_COMMENT_TAB_BY_OBJECT_KEY = {
    task: {
        key: 'stab',
        value: 'task'
    },
    approvals: {
        key: 'stab',
        value: 'info'
    },
    requestView: {
        key: 'rtab',
        value: 'info'
    },
    ticketView: {
        key: 'ttab',
        value: 'info'
    },
    client: {
        key: 'ctab',
        value: 'info'
    },
    meeting: {
        key: 'meettab',
        value: 'info'
    }
}

const parseNotificationQueryString = query => {
    if (!query || typeof query !== 'string') return {}

    try {
        return JSON.parse(query)
    } catch (e) {
        try {
            const normalized = query.replace(/(\w+:)|(\w+ :)/g, m => `"${m.substring(0, m.length - 1)}":`)
            return normalized ? JSON.parse(normalized) : {}
        } catch (err) {
            return {}
        }
    }
}

const isTabLikeQueryKey = key => {
    if (!key) return false

    return key === 'tab' || key.endsWith('tab')
}

const getComparableObjectEntries = query => {
    if (!query || typeof query !== 'object') return []

    return Object.entries(query)
        .filter(([key, value]) => {
            if (!key) return false
            if (value === undefined || value === null || value === '') return false
            if (key === 'comment') return false
            if (key === 'notif_panel') return false
            if (isTabLikeQueryKey(key)) return false

            return true
        })
}

const getTabEntry = query => {
    if (!query || typeof query !== 'object') return null

    const entry = Object.entries(query).find(([key, value]) => {
        return isTabLikeQueryKey(key) && value !== undefined && value !== null && value !== ''
    })

    return entry || null
}

export default {
    name: "NotificationInit",
    mixins: [
        Socket, 
        push
    ],
    watch: {
        '$route.query.notif_panel': {
            handler() {
                this.openNotyFromQuery()
            }
        },
        notifyDrawer(val, oldVal) {
            if (oldVal && !val) {
                this.removeNotyPanelQuery()
            }
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            notifyDrawer: state => state.notifications?.visible || false
        }),
        groupNotificationsEnabled() {
            return !!this.$store.state.user.user?.group_notifications
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        drawerComp() {
            if(this.notifyDrawer)
                return loadNotifyDrawer
            return null
        }
    },
    methods: {
        ...mapActions({
            getUnreadCount: 'notifications/getUnreadCount',
            readNoty: 'notifications/readNoty'
        }),
        prefetchDrawer() {
            loadNotifyDrawer().catch(() => {})
        },
        isNotyPanelQueryActive(route = this.$route) {
            const queryValue = route?.query?.notif_panel
            return queryValue === true || queryValue === 'true'
        },
        openNotyFromQuery() {
            if (this.isStandaloneChatWindow) return
            if (!this.isNotyPanelQueryActive() || this.notifyDrawer) return

            this.openNoty()
        },
        removeNotyPanelQuery() {
            if (!this.isNotyPanelQueryActive()) return

            const query = { ...(this.$route?.query || {}) }
            delete query.notif_panel

            this.$router.replace({
                path: this.$route.path,
                query,
                hash: this.$route.hash
            }).catch(() => {})
        },
        renderNotificationAvatar(h, data) {
            if (data?.is_mention) {
                return h('a-avatar', {
                    class: 'notify_popover_avatar notify_popover_mention_avatar'
                }, '@')
            }

            const iconClass = getNotificationIconClass(data?.icon)

            return h('a-avatar', {
                class: 'notify_popover_avatar',
                attrs: {
                    style: `color: ${getColor(data?.color)};backgroundColor: ${getBackground(data?.color)}`,
                    icon: iconClass ? null : data?.icon
                }
            }, iconClass ? [
                h('i', { class: iconClass })
            ] : [])
        },
        closeNotificationToast(key) {
            try {
                this.$notification.close(key)
            } catch(e) {}
            try {
                notificationChannel.broadcastClose(key)
            } catch(e) {}
        },
        async markNotificationAsRead(data) {
            if (!data?.id || data?.is_read) return

            await this.readNoty({
                id: data.id,
                isMention: !!data.is_mention,
                categoryCode: data?.category?.code || null
            }).catch(() => {})
        },
        async openNotificationTarget(data) {
            const lastLink = getLastNotificationLink(data?.message || '')
            if (lastLink) {
                return openNotificationLink(lastLink, {
                    router: this.$router,
                    route: this.$route
                })
            }

            return false
        },
        async handleNotificationClick(data) {
            if (this.isStandaloneChatWindow) return
            this.closeNotificationToast(data?.id)
            await this.markNotificationAsRead(data)
            const openedLink = await this.openNotificationTarget(data)
            if (!openedLink) {
                this.openNoty(!!data.is_mention)
            }
        },
        getNotificationToastTitle(data) {
            if (data?.is_mention)
                return this.$t('noty.mentionNotificationTitle')

            if (this.groupNotificationsEnabled) {
                const objectType = typeof data?.group_info?.object_type === 'string'
                    ? data.group_info.object_type.trim()
                    : ''
                const groupTitle = typeof data?.group_info?.title === 'string'
                    ? data.group_info.title.trim()
                    : ''

                if (objectType && groupTitle)
                    return `${objectType}: ${groupTitle}`
                if (groupTitle)
                    return groupTitle
            }

            return data?.icon_name
        },
        isCommentNotification(data) {
            const iconName = typeof data?.icon_name === 'string'
                ? data.icon_name.trim().toLowerCase()
                : ''

            return data?.icon === 'ellipsis'
                || COMMENT_NOTIFICATION_ICON_NAMES.includes(iconName)
        },
        getCommentNotificationRouteState(data) {
            if (!this.isCommentNotification(data)) return null
            const lastLink = getLastNotificationLink(data?.message || '')
            if (!lastLink?.query) return null

            const targetQuery = parseNotificationQueryString(lastLink.query)
            const objectEntries = getComparableObjectEntries(targetQuery)
            if (!objectEntries.length) return null

            const [objectKey, objectId] = objectEntries[0]
            const targetTabEntry = getTabEntry(targetQuery)

            return {
                targetQuery,
                objectEntries,
                objectKey,
                objectId,
                targetTabEntry
            }
        },
        isCurrentCommentBlockVisible(relatedObject) {
            if (relatedObject === undefined || relatedObject === null || relatedObject === '') return false

            const visibilityEntry = this.$store.state.comments?.visibilityByObject?.[String(relatedObject)]
            if (!visibilityEntry?.instances) return false

            return Object.values(visibilityEntry.instances).some(Boolean)
        },
        isCurrentRouteAlreadyOpenForNotification(data) {
            const routeState = this.getCommentNotificationRouteState(data)
            if (!routeState) return false

            const currentQuery = this.$route?.query || {}
            const { objectEntries, objectKey, objectId, targetTabEntry } = routeState

            const isSameObjectOpen = objectEntries.every(([key, value]) => String(currentQuery?.[key]) === String(value))
            if (!isSameObjectOpen) return false

            if (!targetTabEntry) {
                return !Object.keys(currentQuery).some(isTabLikeQueryKey)
                    && this.isCurrentCommentBlockVisible(objectId)
            }

            const [targetTabKey, targetTabValue] = targetTabEntry
            const currentTabValue = currentQuery?.[targetTabKey]

            if (currentTabValue !== undefined && currentTabValue !== null && currentTabValue !== '') {
                return String(currentTabValue) === String(targetTabValue)
                    && this.isCurrentCommentBlockVisible(objectId)
            }

            const defaultCommentTab = DEFAULT_COMMENT_TAB_BY_OBJECT_KEY[objectKey]
            if (!defaultCommentTab) return false

            return defaultCommentTab.key === targetTabKey
                && String(defaultCommentTab.value) === String(targetTabValue)
                && this.isCurrentCommentBlockVisible(objectId)
        },
        openNoty(isMention = false) {
            if (this.isStandaloneChatWindow) {
                this.$notification.destroy()
                return
            }
            this.$store.commit('notifications/SET_ACTIVE_TAB', isMention ? 'mentions' : 'notifications')
            if(!this.notifyDrawer)
                this.$store.commit('notifications/SET_DRAWER_VISIBLE', true)
            else {
                this.$store.commit('notifications/SET_DRAWER_VISIBLE', false)
                setTimeout(() => {
                    this.$store.commit('notifications/SET_DRAWER_VISIBLE', true)
                }, 700)
            }
            this.$notification.destroy()
            try {
                notificationChannel.broadcastCloseAll()
            } catch(e) {}
        }
    },
    created() {
        visibilityManager.init()

        if(!this.$store.hasModule('notifications'))
            this.$store.registerModule("notifications", store)
        
        this.getUnreadCount()
    },
    mounted() {
        if (this.isStandaloneChatWindow) {
            this.$notification.destroy()
        }

        this.notyUnsubSync = notySyncChannel.subscribe(msg => {
            try {
                if (!msg || !msg.type) return

                if (msg.type === 'set_count') {
                    this.$store.commit('notifications/SET_UNREAD_COUNTS', {
                        unreadCount: msg.unread_count ?? msg.count,
                        unreadMentionsCount: msg.unread_mentions_count,
                        unreadByCategory: msg.unread_by_category
                    })
                    const totalUnread = (Number(msg.unread_count ?? msg.count) || 0) + (Number(msg.unread_mentions_count) || 0)
                    this.$store.commit("SET_PWA_COUNTER", { name: 'noty', value: totalUnread }, { root: true })
                    return
                }

                if (msg.type === 'read_all') {
                    this.$notification.destroy()
                    this.$store.commit('notifications/READ_NOTY', { id: 'all' })
                    return
                }

                if (msg.type === 'read_group' && msg.objectId) {
                    this.$notification.destroy()
                    if (Array.isArray(msg.notificationIds) && msg.notificationIds.length) {
                        msg.notificationIds.forEach(id => {
                            this.$store.commit('notifications/READ_NOTY', { id })
                        })
                    }
                    return
                }

                if (msg.type === 'read_by_categories' && Array.isArray(msg.category_codes)) {
                    this.$notification.destroy()
                    this.$store.commit('notifications/READ_NOTY_BY_CATEGORIES', { categoryCodes: msg.category_codes })
                    return
                }

                if (msg.type === 'read_mentions') {
                    this.$notification.destroy()
                    this.$store.commit('notifications/READ_MENTION_NOTY')
                    return
                }

                if (msg.type === 'read_one' && msg.id) {
                    this.$notification.destroy()
                    this.$store.commit('notifications/READ_NOTY', {
                        id: msg.id,
                        isMention: msg.isMention,
                        categoryCode: msg.categoryCode
                    })
                    return
                }

                if (msg.type === 'new_noty' && msg.data) {
                    this.$store.commit('notifications/addNotyFromSocket', msg.data)
                    return
                }
            } catch (e) {}
        })
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

        if(typeof window !== 'undefined') {
            if(typeof window.requestIdleCallback === 'function') {
                this.prefetchDrawerIdleId = window.requestIdleCallback(() => {
                    this.prefetchDrawer()
                })
            } else {
                this.prefetchDrawerTimeoutId = window.setTimeout(() => {
                    this.prefetchDrawer()
                }, 1500)
            }
        }

        this.openNotyFromQuery()

        eventBus.$on('NOTIFICATION_NEW_MESSAGE', data => {
            if (this.isStandaloneChatWindow) {
                return
            }

            const hasRouteQuery = this.$route && this.$route.query && Object.keys(this.$route.query).length > 0
            if(hasRouteQuery || !this.notifyDrawer) {
                if(this.isMobile)
                    this.$notification.destroy()

                if (this.isCurrentRouteAlreadyOpenForNotification(data))
                    return

                const key = data.id,
                    title = this.getNotificationToastTitle(data)

                this.$notification.open({
                    message: (h) => {
                        return h('div', { class: 'notify_head' }, [
                            h('div', {
                                class: {
                                    notify_title: true,
                                    notify_title_grouped: this.groupNotificationsEnabled && !data?.is_mention
                                }
                            }, title),
                            h('div', { class: 'notify_date' }, `${this.$moment(data.created_at).format('HH:mm')}`)
                        ])
                    },
                    description: (h) => {
                        return h('div', { class: 'notify_message', domProps: { innerHTML: linkifyNotificationHtml(data.message) } })
                    },
                    duration: visibilityManager.getNotifyDuration(),
                    top: this.isMobile ? '50px' : '60px',
                    key,
                    class: `cursor-pointer notify_popover ${data.is_mention ? 'notify_popover_mention' : ''}`,
                    closeIcon: (h) => {
                        if(this.isMobile) {
                            return h('div', { class: 'notify_close' }, this.$t('close'))
                        } else
                            return h('i', { class: 'fi fi-rr-cross' })
                    },
                    icon: (h) => {
                        return this.renderNotificationAvatar(h, data)
                    }, 
                    onClick: ()=> this.handleNotificationClick(data),
                    onClose: (closeMeta) => {
                        try {
                            this.$notification.close(key)
                        } catch(e) {}
                        try {
                            notificationChannel.broadcastClose(key)
                        } catch(e) {}
                        if (closeMeta?.manual) {
                            closeBrowserPushNotification(key)
                        }
                    }
                })
            }
        })
    },
    beforeDestroy() {
        if(typeof window !== 'undefined') {
            if(this.prefetchDrawerIdleId && typeof window.cancelIdleCallback === 'function')
                window.cancelIdleCallback(this.prefetchDrawerIdleId)
            if(this.prefetchDrawerTimeoutId)
                window.clearTimeout(this.prefetchDrawerTimeoutId)
        }
        if (this.notyUnsubSync) this.notyUnsubSync()
        eventBus.$off('NOTIFICATION_NEW_MESSAGE')
        visibilityManager.destroy()
        if (this.notifyUnsubChannel)
            this.notifyUnsubChannel()
    }
}
</script>

<style lang="scss">
.notify_popover {
    .notify_head{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        column-gap: 8px;
        width: 100%;
    }
    .notify_title{
        min-width: 0;
    }
    .notify_title_grouped{
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .notify_date{
        white-space: nowrap;
    }
    .notify_popover_avatar{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        .ant-avatar-string{
            position: static;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            line-height: 1!important;
            transform: none!important;
        }
        .fi{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            line-height: 1;
        }
    }
    .notify_message {
        a,
        .n_link {
            pointer-events: none;
        }
    }
}
.notify_popover_mention {
    background-color: rgb(106 87 44 / 80%)!important;
    box-shadow: 0 0 0 1px rgb(86 70 36 / 80%)!important;
}
.notify_popover_mention_avatar{
    color: #8a7a52!important;
    background: #ffffff!important;
    font-weight: 600;
}
</style>
