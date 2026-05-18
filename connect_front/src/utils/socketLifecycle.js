import socket from '@/config/socket'

const RESUME_RECONNECT_DELAY = 1500

let inited = false
let hiddenAt = null
let reconnectTimer = null
function hasAuthorizedUser(store) {
    return !!store?.state?.user?.user?.id
}

function clearReconnectTimer() {
    if (!reconnectTimer) return
    clearTimeout(reconnectTimer)
    reconnectTimer = null
}

function rejoinConnectedRooms(store) {
    const rooms = Array.isArray(store?.state?.connectedRooms)
        ? store.state.connectedRooms.filter(Boolean)
        : []

    rooms.forEach(roomName => {
        try {
            socket.emit('join_universal', roomName)
        } catch (error) {}
    })
}

function ensureSocketConnection(store, { force = false } = {}) {
    if (!hasAuthorizedUser(store)) return

    const isVisible = typeof document === 'undefined' || document.visibilityState === 'visible'
    if (!isVisible && !force) return

    const offline = typeof navigator !== 'undefined' && navigator.onLine === false
    if (offline) return

    const resumeAge = hiddenAt ? Date.now() - hiddenAt : 0
    const shouldReconnectAfterResume = hiddenAt && resumeAge >= RESUME_RECONNECT_DELAY

    clearReconnectTimer()

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null

        if (!hasAuthorizedUser(store)) return

        if (!socket.connected) {
            hiddenAt = null
            socket.connect()
            return
        }

        if (force && shouldReconnectAfterResume) {
            hiddenAt = null
            socket.disconnect()
            socket.connect()
        }
    }, 200)
}

export function initSocketLifecycle(store) {
    if (inited || typeof window === 'undefined') return
    inited = true

    socket.on('connect', () => {
        hiddenAt = null
        rejoinConnectedRooms(store)
    })

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            hiddenAt = Date.now()
            return
        }

        ensureSocketConnection(store, { force: true })
    })

    window.addEventListener('pageshow', () => {
        ensureSocketConnection(store, { force: true })
    })

    window.addEventListener('focus', () => {
        ensureSocketConnection(store)
    })

    window.addEventListener('online', () => {
        ensureSocketConnection(store, { force: true })
    })
}
