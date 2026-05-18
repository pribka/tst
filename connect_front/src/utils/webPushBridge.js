import notification from '@apps/UIModules/antDesign/notification'
import store from '@/store'
import notificationChannel from '@/utils/notificationChannel'
import notificationsStoreModule from '@/modules/Notifications/store'

function ensureNotificationsModule() {
    if (!store.hasModule('notifications')) {
        store.registerModule('notifications', notificationsStoreModule)
    }
}

function closeSiteNotification(notificationId) {
    if (!notificationId) return

    try {
        notification.close(notificationId)
    } catch (error) {}

    try {
        notificationChannel.broadcastClose(notificationId)
    } catch (error) {}
}

function openPushTarget(router, targetUrl) {
    if (!targetUrl) return

    try {
        const target = new URL(targetUrl, window.location.origin)

        if (target.origin === window.location.origin && router) {
            router.push(`${target.pathname}${target.search}${target.hash}`).catch(() => {})
            window.focus()
            return
        }

        window.location.href = target.toString()
    } catch (error) {
        window.location.href = targetUrl
    }
}

async function handlePushNotificationClick(router, payload = {}) {
    try {
        ensureNotificationsModule()

        const notificationId = payload.notification_id || null
        const targetUrl = payload.click_action || ''

        if (notificationId) {
            closeSiteNotification(notificationId)
            await store.dispatch('notifications/readNoty', { id: notificationId }).catch(() => {})
        }

        if (targetUrl) {
            openPushTarget(router, targetUrl)
        }
    } catch (error) {
        console.log(error, 'handlePushNotificationClick')
    }
}

function handlePushNotificationClose(payload = {}) {
    try {
        const notificationId = payload.notification_id || null
        if (!notificationId) return

        closeSiteNotification(notificationId)
    } catch (error) {
        console.log(error, 'handlePushNotificationClose')
    }
}

async function consumePushNotificationIdFromUrl(router) {
    if (typeof window === 'undefined') return

    try {
        const currentUrl = new URL(window.location.href)
        const notificationId = currentUrl.searchParams.get('push_notification_id')

        if (!notificationId) return

        ensureNotificationsModule()
        closeSiteNotification(notificationId)
        await store.dispatch('notifications/readNoty', { id: notificationId }).catch(() => {})

        currentUrl.searchParams.delete('push_notification_id')

        if (router) {
            router.replace(`${currentUrl.pathname}${currentUrl.search}${currentUrl.hash}`).catch(() => {})
        } else {
            window.history.replaceState({}, '', `${currentUrl.pathname}${currentUrl.search}${currentUrl.hash}`)
        }
    } catch (error) {
        console.log(error, 'consumePushNotificationIdFromUrl')
    }
}

function setupPushNotificationBridge(router) {
    if (typeof window === 'undefined') return
    if (!navigator.serviceWorker) return
    if (window.__pushNotificationBridgeInited) return

    window.__pushNotificationBridgeInited = true

    navigator.serviceWorker.addEventListener('message', (event) => {
        if (event?.data?.type === 'PUSH_NOTIFICATION_CLICK') {
            handlePushNotificationClick(router, event.data.payload || {})
            return
        }

        if (event?.data?.type === 'PUSH_NOTIFICATION_CLOSED') {
            handlePushNotificationClose(event.data.payload || {})
        }
    })
}

export function initWebPushBridge(router) {
    setupPushNotificationBridge(router)
    consumePushNotificationIdFromUrl(router)
}
