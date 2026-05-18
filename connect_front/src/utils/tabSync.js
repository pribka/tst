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

export const createRecentUsersSync = (store) => {
    const ch = createChannel()

    const apply = (payload) => {
        if (!payload) return
        if (payload.type === 'recentUsers:set') {
            store.commit('recentUsers/SET_LIST', payload.list || [])
            store.commit('recentUsers/SET_LOADED', true)
        }
        if (payload.type === 'recentUsers:clear') {
            store.commit('recentUsers/SET_LIST', [])
            store.commit('recentUsers/SET_LOADED', true)
        }
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

    return {
        post(payload) {
            if (ch) ch.postMessage(payload)
            else emitStorage(payload)
        }
    }
}