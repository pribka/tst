/**
 * Cross-window communication channel for the call popup window.
 *
 * Main tab → Popup:
 *   { type: 'CALL_STATE', calls: [...] }     – current state of active calls
 *   { type: 'CALL_CLOSE_POPUP' }             – ask the popup to close itself
 *
 * Popup → Main tab:
 *   { type: 'CALL_POPUP_READY' }             – popup finished loading
 *   { type: 'CALL_ACTION', action, callId }  – user clicked a button
 */

const CHANNEL_NAME = 'meeting-call-popup'
const STATE_KEY = 'meeting-call-popup:state'
const MSG_KEY = 'meeting-call-popup:msg'

const hasBC = typeof BroadcastChannel !== 'undefined'

let _channel = null
let _listeners = []
let _storageHandler = null

function _dispatch(data) {
    _listeners.forEach(fn => {
        try { fn(data) } catch (e) { /* noop */ }
    })
}

const CallPopupChannel = {
    init() {
        if (_channel) return

        if (hasBC) {
            _channel = new BroadcastChannel(CHANNEL_NAME)
            _channel.onmessage = e => _dispatch(e.data)
        }

        _storageHandler = e => {
            if (e.key !== MSG_KEY || !e.newValue) return
            try { _dispatch(JSON.parse(e.newValue)) } catch (e) { /* noop */ }
        }
        window.addEventListener('storage', _storageHandler)
    },

    post(data) {
        if (_channel) {
            _channel.postMessage(data)
            return
        }
        // localStorage fallback for browsers without BroadcastChannel
        try {
            localStorage.setItem(MSG_KEY, JSON.stringify(data))
            localStorage.removeItem(MSG_KEY)
        } catch (e) { /* noop */ }
    },

    onMessage(fn) {
        _listeners.push(fn)
        return () => {
            _listeners = _listeners.filter(l => l !== fn)
        }
    },

    saveState(state) {
        try { localStorage.setItem(STATE_KEY, JSON.stringify(state)) } catch (e) { /* noop */ }
    },

    readState() {
        try {
            const raw = localStorage.getItem(STATE_KEY)
            return raw ? JSON.parse(raw) : null
        } catch (e) {
            return null
        }
    },

    clearState() {
        try { localStorage.removeItem(STATE_KEY) } catch (e) { /* noop */ }
    },

    destroy() {
        if (_channel) {
            _channel.close()
            _channel = null
        }
        if (_storageHandler) {
            window.removeEventListener('storage', _storageHandler)
            _storageHandler = null
        }
        _listeners = []
    }
}

export default CallPopupChannel
