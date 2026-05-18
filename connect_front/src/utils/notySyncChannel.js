const CHANNEL = 'noty_sync_v1'
const LS_KEY = '__noty_sync_v1__'

const canBC = typeof window !== 'undefined' && 'BroadcastChannel' in window
const bc = canBC ? new BroadcastChannel(CHANNEL) : null
const SOURCE_ID = `${Date.now()}_${Math.random().toString(36).slice(2)}`

const listeners = new Set()
const handledMessages = new Set()

const rememberMessage = id => {
    if (!id) return false
    if (handledMessages.has(id)) return true

    handledMessages.add(id)
    setTimeout(() => handledMessages.delete(id), 30000)
    return false
}

const emit = payload => {
    if (payload?.source === SOURCE_ID) return
    if (rememberMessage(payload?.messageId)) return
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
    const message = {
        ...payload,
        source: SOURCE_ID,
        messageId: `${SOURCE_ID}_${Date.now()}_${Math.random().toString(36).slice(2)}`
    }

    try {
        if (bc) bc.postMessage(message)
    } catch (e) {}

    try {
        localStorage.setItem(LS_KEY, JSON.stringify({ ...message, ts: Date.now() }))
    } catch (e) {}
}

export default {
    subscribe(fn) {
        listeners.add(fn)
        return () => listeners.delete(fn)
    },
    setCount(payload) {
        if (payload && typeof payload === 'object') {
            post({ type: 'set_count', ...payload })
            return
        }

        post({ type: 'set_count', count: payload })
    },
    readOne(id, payload = {}) {
        post({ type: 'read_one', id, ...payload })
    },
    readGroup(objectId, payload = {}) {
        post({ type: 'read_group', objectId, ...payload })
    },
    readMany(ids = []) {
        post({ type: 'read_many', ids })
    },
    readAll() {
        post({ type: 'read_all' })
    },
    readByCategories(categoryCodes = []) {
        post({ type: 'read_by_categories', category_codes: categoryCodes })
    },
    readMentions() {
        post({ type: 'read_mentions' })
    },
    groupNotifications(value) {
        post({ type: 'group_notifications', value: !!value })
    },
    newNoty(data) {
        post({ type: 'new_noty', data })
    }
}
