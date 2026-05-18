import axios from '@/config/axios'
import store from '@/store'
import pkg from '../../package'
import { REMOTE_ACCESS_AGENT_STATUSES } from '@/utils/remoteAccess'

const REGISTER_ENDPOINT = '/notifications/webpush/register/'
const STATUS_ENDPOINT = '/notifications/webpush/status/'
const UNREGISTER_ENDPOINT = '/notifications/webpush/unregister/'
const PUSH_VISIBILITY_HEARTBEAT_MS = 10000
const PUSH_VISIBILITY_TTL_MS = 15000

let promptListenersBound = false
let syncListenersBound = false
let pushSuppressionListenerBound = false
let syncInFlight = null
let backendStatusCache = null
let pushVisibilityHeartbeatTimer = null

export function isPushSupported() {
    if (typeof window === 'undefined') return false
    if (!('Notification' in window)) return false
    if (!('serviceWorker' in navigator)) return false
    if (!('PushManager' in window)) return false
    if (!window.isSecureContext) return false
    if (!process.env.VUE_APP_PUSH_KEY) return false
    return true
}

export function isIos() {
    if (typeof navigator === 'undefined') return false
    return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

export function isStandalonePwa() {
    if (typeof window === 'undefined') return false
    return window.matchMedia?.('(display-mode: standalone)')?.matches || window.navigator.standalone === true
}

export function canPromptForPermission() {
    if (!isPushSupported()) return false
    if (!isIos()) return true
    return isStandalonePwa()
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i)
    }

    return outputArray
}

function getSubscriptionData(subscription) {
    if (!subscription) return null
    return subscription.toJSON ? subscription.toJSON() : subscription
}

function getSubscriptionAuth(subscription) {
    return getSubscriptionData(subscription)?.keys?.auth || null
}

function getSubscriptionFingerprint(subscription) {
    const data = getSubscriptionData(subscription)
    const endpoint = data?.endpoint || null
    const auth = data?.keys?.auth || null

    if (!endpoint) return null

    return `${endpoint}::${auth || ''}`
}

function getPlatform() {
    const ua = navigator.userAgent || ''

    if (/android/i.test(ua)) return 'android'
    if (/iphone|ipad|ipod/i.test(ua)) return 'ios'
    if (/win/i.test(ua)) return 'windows'
    if (/mac/i.test(ua)) return 'macos'
    if (/linux/i.test(ua)) return 'linux'

    return 'unknown'
}

function getBrowser() {
    const ua = navigator.userAgent || ''

    if (/edg/i.test(ua)) return 'edge'
    if (/opr|opera/i.test(ua)) return 'opera'
    if (/chrome|crios/i.test(ua)) return 'chrome'
    if (/firefox|fxios/i.test(ua)) return 'firefox'
    if (/safari/i.test(ua)) return 'safari'

    return 'unknown'
}

function buildRegisterPayload(subscription) {
    return {
        subscription: {
            ...getSubscriptionData(subscription),
            platform: getPlatform(),
            browser: getBrowser(),
            metadata: {
                app_version: pkg.version,
                lang: document?.documentElement?.lang || navigator.language || 'ru',
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
            }
        }
    }
}

function buildStatusPayload(subscription) {
    const data = getSubscriptionData(subscription)

    if (!data?.endpoint) return null

    return {
        subscription: {
            endpoint: data.endpoint,
            keys: {
                auth: data?.keys?.auth || null
            }
        }
    }
}

async function getServiceWorkerRegistration() {
    if (!isPushSupported()) return null

    if (window.__swRegistration__) return window.__swRegistration__

    try {
        return await navigator.serviceWorker.ready
    } catch (error) {
        return null
    }
}

function setPushAuth(auth) {
    store.commit('SET_PUSH_AUTH', auth || null)
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

function setBackendStatusCache(subscription, status = {}) {
    const fingerprint = getSubscriptionFingerprint(subscription)

    if (!fingerprint) {
        backendStatusCache = null
        return
    }

    backendStatusCache = {
        fingerprint,
        checked: !!status.checked,
        isSubscribed: !!status.isSubscribed,
        raw: status.raw || null
    }
}

function getCachedBackendStatus(subscription) {
    const fingerprint = getSubscriptionFingerprint(subscription)

    if (!fingerprint || !backendStatusCache) return null
    if (backendStatusCache.fingerprint !== fingerprint) return null

    return backendStatusCache
}

function shouldSuppressBrowserPush() {
    const isVisible = typeof document !== 'undefined'
        ? document.visibilityState === 'visible'
        : store?.state?.visibilityState !== false

    if (isVisible && isStandalonePwa()) {
        return true
    }

    return !store?.state?.isMobile && store?.state?.remoteAccess?.agentStatus === REMOTE_ACCESS_AGENT_STATUSES.CONNECTED
}

async function syncPushVisibilityState() {
    if (!isPushSupported()) return

    const suppress = shouldSuppressBrowserPush()
    const visibleUntil = suppress ? Date.now() + PUSH_VISIBILITY_TTL_MS : 0

    await postToServiceWorker({
        type: 'UPDATE_PUSH_VISIBILITY_STATE',
        suppress,
        visibleUntil,
        standalone: isStandalonePwa()
    })
}

function restartPushVisibilityHeartbeat() {
    if (pushVisibilityHeartbeatTimer) {
        clearInterval(pushVisibilityHeartbeatTimer)
        pushVisibilityHeartbeatTimer = null
    }

    syncPushVisibilityState()

    if (!shouldSuppressBrowserPush()) return

    pushVisibilityHeartbeatTimer = setInterval(() => {
        syncPushVisibilityState()
    }, PUSH_VISIBILITY_HEARTBEAT_MS)
}

function bindPushSuppressionListener() {
    if (pushSuppressionListenerBound) return
    if (typeof navigator === 'undefined' || !navigator.serviceWorker) return

    pushSuppressionListenerBound = true

    navigator.serviceWorker.addEventListener('message', event => {
        if (!event.data || event.data.type !== 'GET_PUSH_SUPPRESSION_STATE') return

        const payload = {
            type: 'PUSH_SUPPRESSION_STATE',
            suppress: shouldSuppressBrowserPush()
        }

        if (event.ports && event.ports[0]) {
            event.ports[0].postMessage(payload)
            return
        }

        if (event.source && typeof event.source.postMessage === 'function') {
            event.source.postMessage(payload)
        }
    })

    window.addEventListener('focus', restartPushVisibilityHeartbeat)
    window.addEventListener('pageshow', restartPushVisibilityHeartbeat)
    window.addEventListener('pagehide', syncPushVisibilityState)
    window.addEventListener('beforeunload', syncPushVisibilityState)
    document.addEventListener('visibilitychange', restartPushVisibilityHeartbeat)

    restartPushVisibilityHeartbeat()
}

async function syncBrowserPushSubscription() {
    if (syncInFlight) return syncInFlight

    syncInFlight = (async () => {
        try {
            if (!isPushSupported()) return
            if (!store?.state?.user?.user?.id) return
            if (Notification.permission !== 'granted') return
            const registration = await getServiceWorkerRegistration()
            const subscription = registration ? await registration.pushManager.getSubscription() : null

            if (!subscription) {
                setPushAuth(null)
                return
            }

            const auth = getSubscriptionAuth(subscription)
            setPushAuth(auth)

            const backendStatus = await getBrowserPushBackendStatus(subscription)

            if (!backendStatus.isSubscribed) {
                await registerBrowserPush({ requestPermission: false })
            }
        } catch (error) {
            console.log(error, 'syncBrowserPushSubscription')
        } finally {
            syncInFlight = null
        }
    })()

    return syncInFlight
}

function bindSubscriptionSyncListeners() {
    if (syncListenersBound) return
    if (!isPushSupported()) return

    syncListenersBound = true

    const sync = () => {
        syncBrowserPushSubscription()
    }

    window.addEventListener('focus', sync)
    window.addEventListener('pageshow', sync)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            sync()
        }
    })
}

export async function getBrowserPushBackendStatus(subscription, { force = false } = {}) {
    const cached = !force ? getCachedBackendStatus(subscription) : null

    if (cached) {
        return cached
    }

    const payload = buildStatusPayload(subscription)

    if (!payload) {
        return {
            checked: false,
            isSubscribed: false
        }
    }

    try {
        const { data } = await axios.post(STATUS_ENDPOINT, payload)

        const result = {
            checked: true,
            isSubscribed: !!(
                data?.is_subscribed ??
                data?.subscribed ??
                data?.registered ??
                data?.is_registered
            ),
            raw: data
        }

        setBackendStatusCache(subscription, result)

        return result
    } catch (error) {
        console.log(error, 'getBrowserPushBackendStatus')

        return {
            checked: false,
            isSubscribed: false,
            error
        }
    }
}

export async function getBrowserPushStatus() {
    const supported = isPushSupported()
    const ios = isIos()
    const standalone = isStandalonePwa()
    const permission = typeof Notification === 'undefined' ? 'default' : Notification.permission
    const registration = supported ? await getServiceWorkerRegistration() : null
    const subscription = registration ? await registration.pushManager.getSubscription() : null
    const auth = getSubscriptionAuth(subscription) || store.state.pushAuth || null
    const backendStatus = subscription
        ? await getBrowserPushBackendStatus(subscription)
        : { checked: false, isSubscribed: false }

    return {
        supported,
        permission,
        isIos: ios,
        isStandalonePwa: standalone,
        canPrompt: canPromptForPermission(),
        hasSubscription: !!subscription,
        enabled: !!subscription && permission === 'granted',
        backendChecked: backendStatus.checked,
        backendSubscribed: backendStatus.isSubscribed,
        backendStatus: backendStatus.raw || null,
        auth,
        needsPwaInstall: ios && !standalone
    }
}

function bindPermissionPrompt() {
    if (promptListenersBound) return
    if (!canPromptForPermission()) return
    if (Notification.permission !== 'default') return

    promptListenersBound = true

    const events = ['pointerdown', 'touchend', 'keydown']

    const cleanup = () => {
        promptListenersBound = false
        events.forEach(eventName => {
            window.removeEventListener(eventName, onInteraction, true)
        })
    }

    const onInteraction = async () => {
        cleanup()

        try {
            await registerBrowserPush({ requestPermission: true })
        } catch (error) {
            console.log(error, 'registerBrowserPush:onInteraction')
        }
    }

    events.forEach(eventName => {
        window.addEventListener(eventName, onInteraction, { capture: true, passive: true })
    })
}

export async function unregisterBrowserPush({ unsubscribe = false } = {}) {
    const registration = await getServiceWorkerRegistration()
    const subscription = registration ? await registration.pushManager.getSubscription() : null
    const auth = getSubscriptionAuth(subscription) || store.state.pushAuth

    if (!auth) {
        setPushAuth(null)
        return
    }

    try {
        await axios.post(UNREGISTER_ENDPOINT, { auth })
    } catch (error) {
        console.log(error, 'unregisterBrowserPush')
    }

    if (unsubscribe && subscription) {
        try {
            await subscription.unsubscribe()
        } catch (error) {
            console.log(error, 'unsubscribeBrowserPush')
        }
    }

    setPushAuth(null)
    setBackendStatusCache(subscription, {
        checked: true,
        isSubscribed: false,
        raw: { is_subscribed: false }
    })
}

export async function registerBrowserPush({ requestPermission = false } = {}) {
    if (!isPushSupported()) return

    const registration = await getServiceWorkerRegistration()
    if (!registration) return

    let permission = Notification.permission

    if (permission === 'default' && requestPermission && canPromptForPermission()) {
        permission = await Notification.requestPermission()

        if (permission === 'granted') {
            setTimeout(() => {
                syncBrowserPushSubscription()
            }, 300)
        }
    }

    if (permission !== 'granted') {
        if (permission === 'denied') {
            await unregisterBrowserPush({ unsubscribe: true })
        }
        return
    }

    let subscription = await registration.pushManager.getSubscription()

    if (!subscription && requestPermission) {
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(process.env.VUE_APP_PUSH_KEY)
        })
    }

    const auth = getSubscriptionAuth(subscription)
    setPushAuth(auth)

    if (!subscription) return

    const backendStatus = requestPermission
        ? null
        : await getBrowserPushBackendStatus(subscription)

    if (backendStatus?.isSubscribed) {
        return
    }

    await axios.post(REGISTER_ENDPOINT, buildRegisterPayload(subscription))
    setBackendStatusCache(subscription, {
        checked: true,
        isSubscribed: true,
        raw: { is_subscribed: true }
    })
}

export async function initBrowserPush() {
    if (!isPushSupported()) return
    if (!store?.state?.user?.user?.id) return

    bindPushSuppressionListener()
    bindSubscriptionSyncListeners()

    const registration = await getServiceWorkerRegistration()
    if (!registration) return

    const existingSubscription = await registration.pushManager.getSubscription()
    setPushAuth(getSubscriptionAuth(existingSubscription))

    if (Notification.permission === 'granted') {
        if (existingSubscription) {
            await syncBrowserPushSubscription()
        }
        return
    }

    if (Notification.permission === 'denied') {
        await unregisterBrowserPush({ unsubscribe: true })
        return
    }

    bindPermissionPrompt()
}
