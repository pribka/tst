const STORAGE_KEY = 'chat_voice_playback_sync'
const TAB_ID = `tab_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
const ELEMENT_INSTANCE_KEY = '__mediaPlaybackInstanceId'

const registry = new Map()
let initialized = false

function getWindow() {
    return typeof window !== 'undefined' ? window : null
}

function readElementsByChat(chatUid) {
    const win = getWindow()
    if (!win || !chatUid) return []

    return Array.from(win.document.querySelectorAll(`.voice_player[data-chat-uid="${String(chatUid)}"]`))
}

function getRegistryEntry(instanceId) {
    return registry.get(instanceId) || null
}

function emitSyncEvent(payload) {
    const win = getWindow()
    if (!win) return

    try {
        win.localStorage.setItem(STORAGE_KEY, JSON.stringify({
            ...payload,
            tabId: TAB_ID,
            ts: Date.now()
        }))
    } catch (error) {
        // Ignore sync errors caused by storage restrictions.
    }
}

function pauseEntry(entry, options = {}) {
    if (!entry || typeof entry.pause !== 'function') return
    entry.pause(options)
}

function pauseAllLocal(exceptInstanceId = null, options = {}) {
    registry.forEach((entry, instanceId) => {
        if (exceptInstanceId && instanceId === exceptInstanceId) return
        pauseEntry(entry, options)
    })
}

function handleStorage(event) {
    if (event.key !== STORAGE_KEY || !event.newValue) return

    try {
        const payload = JSON.parse(event.newValue)
        if (!payload || payload.tabId === TAB_ID) return

        if (payload.type === 'play') {
            pauseAllLocal(null, { source: 'remote-play' })
            return
        }

        if (payload.type === 'pause-all') {
            pauseAllLocal(null, { source: 'remote-pause-all' })
        }
    } catch (error) {
        // Ignore malformed storage events.
    }
}

function ensureInitialized() {
    const win = getWindow()
    if (!win || initialized) return

    win.addEventListener('storage', handleStorage)
    initialized = true
}

export function registerVoicePlayer(entry) {
    if (!entry?.instanceId) return

    ensureInitialized()
    registry.set(entry.instanceId, entry)
}

export function registerMediaPlayer(entry) {
    registerVoicePlayer(entry)
}

export function unregisterVoicePlayer(instanceId) {
    if (!instanceId) return
    registry.delete(instanceId)
}

export function unregisterMediaPlayer(instanceId) {
    unregisterVoicePlayer(instanceId)
}

export function requestVoicePlayback(instanceId) {
    if (!instanceId) return

    pauseAllLocal(instanceId, { source: 'local-play' })
    emitSyncEvent({ type: 'play', instanceId })
}

export function requestMediaPlayback(instanceId) {
    requestVoicePlayback(instanceId)
}

export function pauseAllVoicePlayback(options = {}) {
    pauseAllLocal(null, options)

    if (options.broadcast !== false) {
        emitSyncEvent({ type: 'pause-all', reason: options.reason || 'manual' })
    }
}

export function playNextVoiceMessage(instanceId) {
    const currentEntry = getRegistryEntry(instanceId)
    const chatUid = currentEntry?.chatUid
    if (!currentEntry || !chatUid) return false

    const elements = readElementsByChat(chatUid)
    const currentIndex = elements.findIndex(element => element.dataset.instanceId === instanceId)
    if (currentIndex === -1) return false

    const nextElement = elements.slice(currentIndex + 1).find(element => {
        const nextInstanceId = element.dataset.instanceId
        return !!getRegistryEntry(nextInstanceId)
    })

    if (!nextElement) return false

    const nextInstanceId = nextElement.dataset.instanceId
    const nextEntry = getRegistryEntry(nextInstanceId)
    if (!nextEntry || typeof nextEntry.play !== 'function') return false

    const messageElement = nextElement.closest('.msg_item') || nextElement
    if (messageElement?.scrollIntoView) {
        messageElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        })
    }

    nextEntry.play({ autoplay: true, source: 'auto-next' })
    return true
}

export function bindMediaElement(element, options = {}) {
    if (!element) return null

    ensureInitialized()

    const instanceId = options.instanceId || `media_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    const onPlay = () => {
        requestMediaPlayback(instanceId)
    }

    registerMediaPlayer({
        instanceId,
        chatUid: options.chatUid || '',
        messageUid: options.messageUid || '',
        play: async () => {
            if (typeof element.play !== 'function') return false

            try {
                requestMediaPlayback(instanceId)
                await element.play()
                return true
            } catch (error) {
                return false
            }
        },
        pause: () => {
            if (typeof element.pause === 'function') {
                element.pause()
            }
        }
    })

    element.dataset.instanceId = instanceId
    element[ELEMENT_INSTANCE_KEY] = {
        instanceId,
        onPlay
    }
    element.addEventListener('play', onPlay)

    return instanceId
}

export function unbindMediaElement(element) {
    const entry = element?.[ELEMENT_INSTANCE_KEY]
    if (!element || !entry) return

    element.removeEventListener('play', entry.onPlay)
    unregisterMediaPlayer(entry.instanceId)
    delete element[ELEMENT_INSTANCE_KEY]
}
