const CHANNEL_NAME = 'recent_users_sync'

const canUseBroadcast = typeof window !== 'undefined' && 'BroadcastChannel' in window

const createChannel = () => {
    if (!canUseBroadcast) return null
    return new BroadcastChannel(CHANNEL_NAME)
}

const emitStorage = (payload) => {
    try {
        localStorage.setItem(CHANNEL_NAME, JSON.stringify({
            ts: Date.now(),
            payload
        }))
        localStorage.removeItem(CHANNEL_NAME)
    } catch (e) {}
}

const createTabId = () => {
    try {
        return `${Date.now()}_${Math.random().toString(16).slice(2)}`
    } catch (e) {
        return `${Date.now()}`
    }
}

export default function recentUsersSyncPlugin(store) {
    const tabId = createTabId()
    const ch = createChannel()

    let isApplying = false

    const apply = (payload) => {
        if (!payload) return
        if (payload.tabId === tabId) return

        isApplying = true
        store.commit('recentUsers/SET_LIST', payload.list || [])
        store.commit('recentUsers/SET_LOADED', true)
        isApplying = false
    }

    if (ch) {
        ch.onmessage = (e) => apply(e.data)
    }

    window.addEventListener('storage', (e) => {
        if (e.key !== CHANNEL_NAME || !e.newValue) return
        try {
            const parsed = JSON.parse(e.newValue)
            apply(parsed.payload)
        } catch (err) {}
    })

    store.subscribe((mutation, state) => {
        if (mutation.type !== 'recentUsers/SET_LIST') return
        if (isApplying) return

        const payload = {
            tabId,
            list: state.recentUsers.list || []
        }

        if (ch) ch.postMessage(payload)
        else emitStorage(payload)
    })
}