const CHANNEL = 'chat_sync_v1'
const LS_KEY = '__chat_sync_v1__'

const canBC = typeof window !== 'undefined' && 'BroadcastChannel' in window
const bc = canBC ? new BroadcastChannel(CHANNEL) : null

const listeners = new Set()

const tabId = () => {
    if (typeof window === 'undefined') return 'ssr'
    try {
        if (window.__chatSyncTabId) return window.__chatSyncTabId
        const v = `${Date.now()}_${Math.random().toString(16).slice(2)}`
        window.__chatSyncTabId = v
        return v
    } catch (e) {
        return `${Date.now()}_${Math.random().toString(16).slice(2)}`
    }
}

const emit = payload => {
    listeners.forEach(fn => {
        try { fn(payload) } catch (e) {}
    })
}

const onStorage = e => {
    if (!e || e.key !== LS_KEY || !e.newValue) return
    try {
        const payload = JSON.parse(e.newValue)
        emit(payload)
    } catch (e) {}
}

if (typeof window !== 'undefined') {
    window.addEventListener('storage', onStorage)
    if (bc) {
        bc.onmessage = e => emit(e.data)
    }
}

const post = payload => {
    const base = { ...payload, ts: Date.now(), from: tabId() }

    try {
        if (bc) {
            bc.postMessage(base)
            return
        }
    } catch (e) {}

    try {
        localStorage.setItem(LS_KEY, JSON.stringify(base))
    } catch (e) {}
}

export default {
    subscribe(fn) {
        listeners.add(fn)
        return () => listeners.delete(fn)
    },

    menuSet(name, value) {
        post({ type: 'menu_set', name, value })
    },
    menuInc(name, delta = 1, mentionDelta = 0) {
        post({ type: 'menu_inc', name, delta, mentionDelta })
    },
    menuClear(name) {
        post({ type: 'menu_clear', name })
    },

    chatInc(chat_uid, delta = 1, mentionDelta = 0) {
        post({ type: 'chat_inc', chat_uid, delta, mentionDelta })
    },
    chatClear(chat_uid) {
        post({ type: 'chat_clear', chat_uid })
    },
    chatSet(chat_uid, value) {
        post({ type: 'chat_set', chat_uid, value })
    },

    tabId: tabId()
}