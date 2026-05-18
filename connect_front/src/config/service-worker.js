workbox.core.clientsClaim()

const PUSH_VISIBILITY_CACHE = 'push-visibility-state'
const PUSH_VISIBILITY_KEY = '/__push_visibility__'

function getAppIconBase() {
    const scope = (self.registration && self.registration.scope) || self.location.origin || ''
    return scope.indexOf('/delo_cloud_connect') > -1 ? '/img/delo_cloud_connect/icons' : '/img/icons'
}

function parsePushPayload(event) {
    if (!event.data) return {}

    try {
        if (typeof event.data.json === 'function') {
            return event.data.json() || {}
        }
    } catch (error) {}

    try {
        if (typeof event.data.text === 'function') {
            const text = event.data.text()
            return text ? JSON.parse(text) : {}
        }
    } catch (error) {}

    return {}
}

async function hasVisibleClients() {
    const clientList = await clients.matchAll({ type: 'window', includeUncontrolled: true })

    return clientList.some(client => {
        return client.visibilityState === 'visible' || client.focused === true
    })
}

async function shouldSuppressPushForClientState() {
    const clientList = await clients.matchAll({ type: 'window', includeUncontrolled: true })
    if (!clientList.length) return false

    const requests = clientList.map(client => {
        return new Promise(resolve => {
            const channel = new MessageChannel()
            const timeout = setTimeout(() => resolve(false), 500)

            channel.port1.onmessage = event => {
                clearTimeout(timeout)
                resolve(!!(event.data && event.data.suppress))
            }

            try {
                client.postMessage({ type: 'GET_PUSH_SUPPRESSION_STATE' }, [channel.port2])
            } catch (error) {
                clearTimeout(timeout)
                resolve(false)
            }
        })
    })

    const results = await Promise.all(requests)
    return results.some(Boolean)
}

async function setPushVisibilityState(payload = {}) {
    try {
        const cache = await caches.open(PUSH_VISIBILITY_CACHE)
        const body = JSON.stringify({
            suppress: !!payload.suppress,
            visibleUntil: Number(payload.visibleUntil || 0),
            standalone: payload.standalone === true,
            updatedAt: Date.now()
        })

        await cache.put(PUSH_VISIBILITY_KEY, new Response(body, {
            headers: { 'Content-Type': 'application/json' }
        }))
    } catch (error) {}
}

async function getPushVisibilityState() {
    try {
        const cache = await caches.open(PUSH_VISIBILITY_CACHE)
        const response = await cache.match(PUSH_VISIBILITY_KEY)
        if (!response) return null

        return await response.json()
    } catch (error) {
        return null
    }
}

async function shouldSuppressPushByHeartbeat() {
    const state = await getPushVisibilityState()
    if (!state?.suppress) return false

    return Number(state.visibleUntil || 0) > Date.now()
}

function withPushNotificationId(url, notificationId) {
    if (!url || !notificationId) return url

    try {
        const nextUrl = new URL(url, self.location.origin)
        nextUrl.searchParams.set('push_notification_id', notificationId)
        return nextUrl.toString()
    } catch (error) {
        return url
    }
}

self.addEventListener('activate', event => {
    event.waitUntil((async () => {
        const names = await caches.keys()
        await Promise.all(names.map(n => caches.delete(n)))
        const clientsList = await self.clients.matchAll({ type: 'window' })
        clientsList.forEach(c => c.postMessage({ type: 'SW_ACTIVATED' }))
    })())
})

self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting()
    if (event.data && event.data.type === 'GET_VERSION') {
        event.waitUntil((async () => {
            try {
                const res = await fetch(`/version.json?v=${event.data.ts}`, { cache: 'no-store' })
                const data = await res.json()
                const clientList = await clients.matchAll({ type: 'window' })
                clientList.forEach(c => c.postMessage({ type: 'VERSION_RESPONSE', version: data }))
            } catch (e) {}
        })())
    }
    if (event.data && event.data.type === 'UPDATE_PUSH_VISIBILITY_STATE') {
        event.waitUntil(setPushVisibilityState(event.data))
    }
    if (event.data && event.data.type === 'CLOSE_PUSH_NOTIFICATION') {
        event.waitUntil((async () => {
            try {
                const notificationId = event.data.notificationId
                if (!notificationId) return

                const notifications = await self.registration.getNotifications()
                notifications.forEach(notification => {
                    const data = notification?.data || {}
                    const raw = data.raw || {}
                    const currentId = raw.notification_id || data.notification_id || null

                    if (currentId && String(currentId) === String(notificationId)) {
                        notification.close()
                    }
                })
            } catch (e) {}
        })())
    }
    if (event.data && event.data.type === 'CLOSE_ALL_PUSH_NOTIFICATIONS') {
        event.waitUntil((async () => {
            try {
                const notifications = await self.registration.getNotifications()
                notifications.forEach(notification => notification.close())
            } catch (e) {}
        })())
    }
})

self.addEventListener('notificationclick', event => {
    event.notification.close()
    event.waitUntil(clients.matchAll({ type: 'window' }).then(clientList => {
        const notificationData = event.notification && event.notification.data ? event.notification.data : {}
        const rawData = notificationData.raw || {}
        const notificationId = rawData.notification_id || notificationData.notification_id || null
        const targetUrl = notificationData.url || '/'
        const targetUrlWithId = withPushNotificationId(targetUrl, notificationId)

        let targetClient = null
        for (let i = 0; i < clientList.length; i++) {
            const client = clientList[i]
            if (targetUrl && client.url && client.url.indexOf(targetUrl) === 0) {
                targetClient = client
                break
            }
        }

        if (!targetClient && clientList.length) {
            targetClient = clientList[0]
        }

        if (targetClient) {
            return Promise.resolve(
                typeof targetClient.navigate === 'function'
                    ? targetClient.navigate(targetUrlWithId || '/').catch(() => targetClient)
                    : targetClient
            )
                .then(client => (typeof client.focus === 'function' ? client.focus() : client))
                .then(client => {
                    try {
                        client.postMessage({
                            type: 'PUSH_NOTIFICATION_CLICK',
                            payload: {
                                notification_id: notificationId,
                                click_action: targetUrlWithId,
                                raw: rawData
                            }
                        })
                    } catch (error) {}
                    return client
                })
        }

        if (clients.openWindow) return clients.openWindow(targetUrlWithId || '/')
    }))
})

self.addEventListener('notificationclose', event => {
    event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
        const notificationData = event.notification && event.notification.data ? event.notification.data : {}
        const rawData = notificationData.raw || {}
        const notificationId = rawData.notification_id || notificationData.notification_id || null

        if (!notificationId) return null

        clientList.forEach(client => {
            try {
                client.postMessage({
                    type: 'PUSH_NOTIFICATION_CLOSED',
                    payload: {
                        notification_id: notificationId
                    }
                })
            } catch (error) {}
        })

        return null
    }))
})

self.addEventListener('push', event => {
    const iconBase = getAppIconBase()
    const data = parsePushPayload(event)
    const title = typeof data.title === 'string' && data.title.trim() ? data.title.trim() : 'Уведомление'
    const body = typeof data.body === 'string' ? data.body : ''
    const clickUrl = typeof data.click_action === 'string' && data.click_action ? data.click_action : '/'
    const notify = {
        body,
        icon: data.icon || `${iconBase}/web-app-manifest-192x192.png`,
        badge: data.badge || `${iconBase}/web-app-manifest-192x192.png`,
        image: data.image || undefined,
        tag: data.tag || `push-${Date.now()}`,
        requireInteraction: data.requireInteraction !== undefined ? !!data.requireInteraction : true,
        renotify: true,
        silent: false,
        data: {
            url: clickUrl,
            notification_id: data.notification_id || null,
            raw: data
        }
    }

    event.waitUntil(
        hasVisibleClients().then(visible => {
            if (visible) return true

            return shouldSuppressPushForClientState()
        }).then(suppress => {
            if (suppress) return true

            return shouldSuppressPushByHeartbeat()
        }).then(suppress => {
            if (suppress) return null

            return self.registration.showNotification(title, notify).catch(() => {
                return self.registration.showNotification('Уведомление', {
                    body: body || 'Откройте приложение, чтобы посмотреть детали.',
                    icon: `${iconBase}/web-app-manifest-192x192.png`,
                    badge: `${iconBase}/web-app-manifest-192x192.png`,
                    data: { url: clickUrl }
                })
            })
        })
    )
})
