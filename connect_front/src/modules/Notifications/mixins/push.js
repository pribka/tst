import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { generateDeviceUUID } from '@/utils/utils.js'

const urlBase64ToUint8Array = s => {
    const p = '='.repeat((4 - s.length % 4) % 4)
    const b = (s + p).replace(/-/g, '+').replace(/_/g, '/')
    const r = window.atob(b)
    const a = new Uint8Array(r.length)
    for (let i = 0; i < r.length; i++) a[i] = r.charCodeAt(i)
    return a
}

export default {
    data() {
        return {
            askKey: 'push_ask_dismissed',
            asking: false
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        user() {
            return this.$store.state.user.user
        }
    },
    methods: {
        shouldAsk() {
            const supported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
            if (!supported) return false
            if (!this.user) return false
            if (Notification.permission !== 'default') return false
            if (localStorage.getItem(this.askKey) === '1') return false
            return true
        },
        askPushPermission() {
            if (this.asking) return
            if (!this.shouldAsk()) return
            this.asking = true
            this.$confirm({
                title: 'Включить уведомления?',
                content: 'Хотите получать push-уведомления от сайта?',
                okText: 'Да',
                cancelText: 'Позже',
                onOk: async () => {
                    try {
                        await this.checkNotify()
                    } finally {
                        this.asking = false
                    }
                },
                onCancel: () => {
                    localStorage.setItem(this.askKey, '1')
                    this.asking = false
                }
            })
        },
        async checkNotify() {
            try {
                const supported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
                if (!supported) return
                if (!this.user) {
                    await this.userUnregisterSubscribe()
                    return
                }
                if (Notification.permission === 'default') {
                    const status = await Notification.requestPermission()
                    if (status !== 'granted') return
                }
                if (Notification.permission !== 'granted') return
                const reg = window.__swRegistration__ || await navigator.serviceWorker.ready
                const current = await reg.pushManager.getSubscription()
                if (current) {
                    await this.userUpdateSubscribe(current)
                } else {
                    await this.userSubscribe(reg)
                }
            } catch (e) {
                console.error('Error enabling push notification', e)
            }
        },
        async userUnregisterSubscribe() {
            try {
                const reg = window.__swRegistration__ || await navigator.serviceWorker.ready
                const sub = await reg.pushManager.getSubscription()
                if (sub) {
                    await this.$http2.post('/subscribe/unsubscribe/', { endpoint: sub.endpoint, buid: generateDeviceUUID() })
                    await sub.unsubscribe()
                }
                this.$store.commit('SET_PUSH_AUTH', null)
            } catch (e) {
                console.error(e, 'userUnregisterSubscribe')
            }
        },
        async userUpdateSubscribe(subscription) {
            try {
                const payload = {
                    subscription,
                    uid: this.user.id,
                    buid: generateDeviceUUID()
                }
                const { data } = await this.$http2.post('/subscribe/update/', payload)
                if (data && data.data && data.data.auth) this.$store.commit('SET_PUSH_AUTH', data.data.auth)
                console.log('%c Notification subscription updated 🔔', 'color: #883ae8')
            } catch (e) {
                if (e && e.response && (e.response.status === 404 || e.response.status === 410)) {
                    await this.userUnregisterSubscribe()
                    return
                }
                console.error(e, 'userUpdateSubscribe')
            }
        },
        async userSubscribe(reg) {
            try {
                const key = this.config && this.config.site_setting && this.config.site_setting.push_key
                if (!key) {
                    console.log('%c There is no push key in the site settings', 'color: #bf1432')
                    return
                }
                const appKey = typeof key === 'string' ? urlBase64ToUint8Array(key) : key
                const subscription = await reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: appKey
                })
                const payload = {
                    subscription,
                    uid: this.user.id,
                    buid: generateDeviceUUID()
                }
                const { data } = await this.$http2.post('/subscribe/subscribe/', payload)
                if (data && data.data && data.data.auth) this.$store.commit('SET_PUSH_AUTH', data.data.auth)
                localStorage.setItem(this.askKey, '1')
                this.$message.success('Уведомления включены')
                console.log('%c User subscribed to notifications 🔔', 'color: #883ae8')
            } catch (e) {
                if (e && e.statusCode && (e.statusCode === 404 || e.statusCode === 410)) {
                    await this.userUnregisterSubscribe()
                    return
                }
                console.error(e, 'userSubscribe')
                this.$message.error('Ошибка подписки')
            }
        }
    },
    mounted() {
        if(this.user) {
            //this.askPushPermission()
        }
        eventBus.$on('user_logged', () => {
            //this.askPushPermission()
        })
        eventBus.$on('user_logged_out', () => {
            //this.userUnregisterSubscribe()
        })
    },
    beforeDestroy() {
        eventBus.$off('user_logged')
        eventBus.$off('user_logged_out')
    }
}
