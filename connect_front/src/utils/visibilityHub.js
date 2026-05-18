const key = 'connect_visible_tabs'
const hasBC = typeof BroadcastChannel !== 'undefined'
const bc = hasBC ? new BroadcastChannel('connect_visibility') : null
const beatMs = 2000
const staleMs = 5000

let tabId = null
let visible = typeof document === 'undefined' ? false : document.visibilityState === 'visible'
let timer = null
let state = {}
let listeners = []

const now = () => Date.now()

const read = () => {
    try {
        const v = localStorage.getItem(key)
        return v ? JSON.parse(v) : {}
    } catch (e) {
        return {}
    }
}

const write = s => {
    try {
        localStorage.setItem(key, JSON.stringify(s))
    } catch (e) {}
}

const prune = s => {
    const t = now()
    const r = {}
    Object.keys(s || {}).forEach(id => {
        if (t - s[id] <= staleMs) r[id] = s[id]
    })
    return r
}

const notify = () => {
    const anyVis = anyVisible()
    listeners.forEach(fn => fn(anyVis))
}

const heartbeat = () => {
    if (!visible || !tabId) return
    state[tabId] = now()
    state = prune(state)
    write(state)
    notify()
    if (bc) bc.postMessage({ type: 'beat', id: tabId, ts: state[tabId] })
}

const setVisible = v => {
    visible = v
    if (v) state[tabId] = now()
    else delete state[tabId]
    state = prune(state)
    write(state)
    notify()
    if (bc) bc.postMessage({ type: v ? 'show' : 'hide', id: tabId, ts: now() })
}

const start = id => {
    if (tabId) return
    tabId = id
    state = prune(read())
    if (visible) state[tabId] = now()
    write(state)
    notify()
    if (timer) clearInterval(timer)
    timer = setInterval(heartbeat, beatMs)
    document.addEventListener('visibilitychange', () => setVisible(document.visibilityState === 'visible'))
    window.addEventListener('pagehide', () => setVisible(false))
    window.addEventListener('beforeunload', () => setVisible(false))
    window.addEventListener('storage', e => {
        if (e.key === key) {
            state = prune(read())
            notify()
        }
    })
    if (bc) {
        bc.onmessage = () => {
            state = prune(read())
            notify()
        }
    }
}

const anyVisible = () => {
    const t = now()
    return Object.values(state).some(ts => t - ts <= staleMs)
}

const onChange = fn => {
    listeners.push(fn)
    fn(anyVisible())
}

export default { start, anyVisible, onChange }
