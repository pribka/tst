import { mapActions, mapMutations, mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import SoundMaster from '@/utils/soundMaster'
import TitleBlinker from '@/utils/titleBlinker'
import VisibilityHub from '@/utils/visibilityHub'
import { getNotificationSoundEnabled } from '@/modules/Notifications/soundSettings'

let lastReadNotificationsKey = ''
let lastReadNotificationsAt = 0

const normalizeNotificationIds = value => {
    if (!Array.isArray(value)) return []

    const ids = []

    const walk = item => {
        if (Array.isArray(item)) {
            item.forEach(walk)
            return
        }

        if (item && typeof item === 'object') {
            if (item.id !== undefined && item.id !== null) {
                ids.push(String(item.id))
            }
            return
        }

        if (item !== undefined && item !== null && item !== '') {
            ids.push(String(item))
        }
    }

    value.forEach(walk)

    return Array.from(new Set(ids))
}

export default {
    computed: {
        ...mapState({
            config: state => state.config.config,
            isMobile: state => state.isMobile,
            user: state => state.user.user,
            notifyDrawerVisible: state => state.notifications?.visible || false
        })
    },
    methods: {
        ...mapActions({
            getUnreadCount: 'notifications/getUnreadCount'
        }),
        ...mapMutations({
            addNotyFromSocket: 'notifications/addNotyFromSocket',
            readNotificationsFromSocket: 'notifications/READ_NOTIFICATIONS_FROM_SOCKET'
        }),
        async playAudioNotify() {
            if(!this.isMobile) {
                const soundEnabled = await getNotificationSoundEnabled(this.user?.id)
                if(soundEnabled) {
                    await SoundMaster.emit('notify_new')
                }
                if (SoundMaster.isLeader() && !VisibilityHub.anyVisible()) {
                    TitleBlinker.bump(1, [this.$t('tab_notify1'), this.$t('tab_notify2'), this.$t('tab_notify3')])
                }
            }
        }
    },
    sockets: {
        notify({ data }) {
            if (data.event_type === 'new_notification') {
                const res = data.obj
                res.message = res[`message_${this.$i18n.locale}`] ? res[`message_${this.$i18n.locale}`] : res.message
                res.icon_name = res[`icon_name_${this.$i18n.locale}`] ? res[`icon_name_${this.$i18n.locale}`] : res.icon_name
                const suppressFeedback = typeof this.isCurrentRouteAlreadyOpenForNotification === 'function'
                    ? this.isCurrentRouteAlreadyOpenForNotification(res)
                    : false

                if (!suppressFeedback) {
                    this.playAudioNotify()
                }
                eventBus.$emit('NOTIFICATION_NEW_MESSAGE', res)
                this.addNotyFromSocket(res)
                return
            }

            if (data.event_type === 'read_notifications') {
                const ids = normalizeNotificationIds(data.notifications)
                if (!ids.length) return

                const eventKey = ids.slice().sort().join(',')
                const now = Date.now()
                if (eventKey && eventKey === lastReadNotificationsKey && now - lastReadNotificationsAt < 1500) {
                    return
                }

                lastReadNotificationsKey = eventKey
                lastReadNotificationsAt = now

                if (this.notifyDrawerVisible) {
                    this.readNotificationsFromSocket(ids)
                }

                this.getUnreadCount().catch(() => {})
            }
        }
    }
}
