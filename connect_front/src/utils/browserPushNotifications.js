async function getServiceWorkerRegistration() {
    if (typeof window === 'undefined') return null
    if (!('serviceWorker' in navigator)) return null

    try {
        if (window.__swRegistration__) return window.__swRegistration__
        return await navigator.serviceWorker.ready
    } catch (error) {
        return null
    }
}

async function postToServiceWorker(message) {
    const registration = await getServiceWorkerRegistration()
    if (!registration || !message?.type) return

    const activeWorker = registration.active || navigator.serviceWorker.controller
    if (!activeWorker || typeof activeWorker.postMessage !== 'function') return

    try {
        activeWorker.postMessage(message)
    } catch (error) {}
}

export async function closeBrowserPushNotification(notificationId) {
    if (!notificationId) return

    await postToServiceWorker({
        type: 'CLOSE_PUSH_NOTIFICATION',
        notificationId
    })
}

export async function closeBrowserPushNotifications(notificationIds = []) {
    const ids = Array.isArray(notificationIds)
        ? notificationIds.filter(Boolean)
        : []

    await Promise.all(ids.map(notificationId => closeBrowserPushNotification(notificationId)))
}

export async function closeAllBrowserPushNotifications() {
    await postToServiceWorker({
        type: 'CLOSE_ALL_PUSH_NOTIFICATIONS'
    })
}
