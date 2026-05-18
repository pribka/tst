const hasBC = typeof BroadcastChannel !== 'undefined'
const bc = hasBC ? new BroadcastChannel('connect_sound_master') : null

const leaderKey = 'connect_sound_leader'
const lastKey = k => `connect_sound_last_${k}`
const evtKey = k => `connect_sound_evt_${k}`
const heartbeatMs = 1000
const staleMs = 3500
const cooldownMs = 900

const now = () => Date.now()
const rid = () => `${now()}_${Math.random().toString(36).slice(2)}`
const tabId = rid()

let isLeader = false
let hbTimer = null
let ensureTimer = null
let resolver = null
let lastLeaderSeen = 0
let needUnlock = false
let pendingLoopKey = null
let unlockListenerAttached = false
const activeLoops = new Set()

const setAmbientAudioSession = () => {
    try {
        if (navigator && navigator.audioSession && navigator.audioSession.type !== 'ambient') {
            navigator.audioSession.type = 'ambient'
        }
    } catch (e) {}
}

const parseJson = v => {
    try {
        return v ? JSON.parse(v) : null
    } catch (e) {
        return null
    }
}

const readLeader = () => {
    try {
        const v = localStorage.getItem(leaderKey)
        return v ? JSON.parse(v) : null
    } catch (e) {
        return null
    }
}

const writeLeader = data => {
    try {
        localStorage.setItem(leaderKey, JSON.stringify(data))
    } catch (e) {}
}

const removeLeader = () => {
    try {
        localStorage.removeItem(leaderKey)
    } catch (e) {}
}

const broadcast = payload => {
    if (bc) bc.postMessage(payload)
    try {
        if (payload.type === 'sound' || payload.type === 'sound_loop_start' || payload.type === 'sound_loop_stop') {
            localStorage.setItem(evtKey(payload.key), JSON.stringify(payload))
        } else if (payload.type === 'hb' || payload.type === 'stepdown') {
            localStorage.setItem(leaderKey, JSON.stringify({ id: payload.id, ts: payload.ts }))
        }
    } catch (e) {}
}

const becomeLeader = () => {
    if (isLeader) return
    isLeader = true
    if (hbTimer) clearInterval(hbTimer)
    hbTimer = setInterval(() => {
        const ts = now()
        writeLeader({ id: tabId, ts })
        broadcast({ type: 'hb', id: tabId, ts })
    }, heartbeatMs)
}

const followLeader = () => {
    isLeader = false
    if (hbTimer) {
        clearInterval(hbTimer)
        hbTimer = null
    }
}

const tryBecomeLeader = () => {
    const cur = readLeader()
    const t = now()
    if (!cur || t - cur.ts > staleMs) {
        writeLeader({ id: tabId, ts: t })
        const check = readLeader()
        if (check && check.id === tabId) {
            becomeLeader()
            const ts2 = now()
            broadcast({ type: 'hb', id: tabId, ts: ts2 })
            lastLeaderSeen = ts2
        }
    }
}

const ensureLeader = () => {
    const l = readLeader()
    const t = now()
    if (!l || t - l.ts > staleMs) {
        tryBecomeLeader()
    } else {
        if (l.id === tabId) becomeLeader()
        else followLeader()
    }
}

const attachCore = () => {
    if (ensureTimer) return
    ensureLeader()
    ensureTimer = setInterval(() => {
        ensureLeader()
        if (!isLeader && now() - lastLeaderSeen > staleMs) tryBecomeLeader()
    }, heartbeatMs)
    window.addEventListener('storage', e => {
        if (e.key === leaderKey) {
            const l = parseJson(e.newValue)
            if (l && l.ts) lastLeaderSeen = l.ts
            ensureLeader()
        }
        if (e.key && e.key.startsWith('connect_sound_evt_')) {
            const data = parseJson(e.newValue)
            if (!data) return
            onEvent(data)
        }
    })
    if (bc) {
        bc.onmessage = ev => {
            const m = ev.data || {}
            if (m.type === 'hb') {
                lastLeaderSeen = m.ts || now()
                if (m.id !== tabId) followLeader()
            } else if (m.type === 'stepdown') {
                lastLeaderSeen = 0
                tryBecomeLeader()
            } else if (m.type === 'sound' || m.type === 'sound_loop_start' || m.type === 'sound_loop_stop') {
                onEvent(m)
            }
        }
    }
    window.addEventListener('pagehide', () => {
        if (isLeader) {
            const ts = now()
            broadcast({ type: 'stepdown', id: tabId, ts })
            removeLeader()
        }
    })
    window.addEventListener('beforeunload', () => {
        if (isLeader) {
            const ts = now()
            try {
                if (navigator.sendBeacon) {
                    const blob = new Blob([JSON.stringify({ type: 'stepdown', id: tabId, ts })], { type: 'application/json' })
                    navigator.sendBeacon('/.sound-stepdown', blob)
                }
            } catch (e) {}
            broadcast({ type: 'stepdown', id: tabId, ts })
            removeLeader()
        }
    })
}

const setResolver = fn => {
    resolver = fn
    attachCore()
}

const safeReset = a => {
    try {
        a.pause()
        a.currentTime = 0
    } catch (e) {}
}

const canPlayByCooldown = key => {
    try {
        const v = parseInt(localStorage.getItem(lastKey(key)) || '0')
        if (v && now() - v < cooldownMs) return false
        localStorage.setItem(lastKey(key), String(now()))
        return true
    } catch (e) {
        return true
    }
}

const tryPlay = async a => {
    if (!a) return false
    setAmbientAudioSession()
    safeReset(a)
    try {
        a.muted = false
        await a.play()
        return true
    } catch (e) {
        if (e && e.name === 'NotAllowedError') {
            needUnlock = true
            attachUnlockListener()
        }
        return false
    }
}

const tryPlayLoop = async a => {
    if (!a) return false
    setAmbientAudioSession()
    try {
        a.pause()
        a.currentTime = 0
        a.loop = true
        a.muted = false
        await a.play()
        return true
    } catch (e) {
        if (e && e.name === 'NotAllowedError') {
            needUnlock = true
            attachUnlockListener()
        }
        return false
    }
}

const stopLoopLocal = key => {
    if (!key) return
    activeLoops.delete(key)
    if (pendingLoopKey === key) pendingLoopKey = null
    const audio = resolver ? resolver(key) : null
    if (!audio) return
    try {
        audio.loop = false
    } catch (e) {}
    safeReset(audio)
}

const startLoopLocal = async key => {
    if (!key) return false
    const audio = resolver ? resolver(key) : null
    if (!audio) return false
    activeLoops.add(key)
    const ok = await tryPlayLoop(audio)
    if (!ok) pendingLoopKey = key
    return ok
}

const onEvent = async payload => {
    if (!isLeader) return
    if (!payload) return

    if (payload.type === 'sound') {
        if (!canPlayByCooldown(payload.key)) return
        const audio = resolver ? resolver(payload.key) : null
        if (!audio) return
        await tryPlay(audio)
        return
    }

    if (payload.type === 'sound_loop_start') {
        await startLoopLocal(payload.key)
        return
    }

    if (payload.type === 'sound_loop_stop') {
        stopLoopLocal(payload.key)
    }
}

const emit = key => {
    const payload = { type: 'sound', key, ts: now() }
    if (isLeader) {
        if (!canPlayByCooldown(key)) return false
        const audio = resolver ? resolver(key) : null
        if (!audio) return false
        return tryPlay(audio)
    } else {
        broadcast(payload)
        return true
    }
}

const startLoop = key => {
    const payload = { type: 'sound_loop_start', key, ts: now() }
    if (isLeader) {
        return startLoopLocal(key)
    }
    broadcast(payload)
    return true
}

const stopLoop = key => {
    const payload = { type: 'sound_loop_stop', key, ts: now() }
    if (isLeader) {
        stopLoopLocal(key)
        return true
    }
    broadcast(payload)
    return true
}

const unlock = () => {
    needUnlock = false
    if (pendingLoopKey) {
        const k = pendingLoopKey
        pendingLoopKey = null
        if (activeLoops.has(k)) startLoop(k)
    }
}

const attachUnlockListener = () => {
    if (unlockListenerAttached) return
    unlockListenerAttached = true
    window.addEventListener('pointerdown', () => {
        if (needUnlock) unlock()
    })
}

export default {
    emit,
    startLoop,
    stopLoop,
    unlock,
    setResolver,
    isLeader: () => isLeader,
    tabId: () => tabId
}
