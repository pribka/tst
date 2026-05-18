let bc = null
let listeners = []
let storageHandler = null

function ensureChannel() {
    if (bc || storageHandler)
        return
    if (typeof BroadcastChannel !== 'undefined') {
        bc = new BroadcastChannel('connect_notifications')
        bc.addEventListener('message', e => {
            try {
                const data = e.data || {}
                listeners.slice().forEach(fn => {
                    try { fn(data) } catch(err) {}
                })
            } catch(e) {}
        })
    } else {
        storageHandler = e => {
            if (e.key !== 'connect_notifications' || !e.newValue) return
            try {
                const data = JSON.parse(e.newValue || '{}')
                listeners.slice().forEach(fn => {
                    try { fn(data) } catch(err) {}
                })
            } catch(err) {}
        }
        window.addEventListener('storage', storageHandler)
    }
}

function teardownChannel() {
    try {
        if (bc) {
            bc.close()
            bc = null
        }
        if (storageHandler) {
            window.removeEventListener('storage', storageHandler)
            storageHandler = null
        }
    } catch(e) {}
}

export default {
    subscribe(fn) {
        if (typeof window === 'undefined')
            return () => {}
        if (typeof fn !== 'function')
            return () => {}
        if (listeners.length === 0)
            ensureChannel()
        listeners.push(fn)
        let removed = false
        return () => {
            if (removed) return
            removed = true
            listeners = listeners.filter(x => x !== fn)
            if (listeners.length === 0)
                teardownChannel()
        }
    },
    broadcastClose(key) {
        if (!key) return
        const payload = { type: 'close', key, t: Date.now() }
        try {
            if (bc) {
                bc.postMessage(payload)
            } else {
                try {
                    localStorage.setItem('connect_notifications', JSON.stringify(payload))
                } catch(e) {}
            }
        } catch(e) {}
    },
    broadcastCloseAll() {
        const payload = { type: 'close_all', t: Date.now() }
        try {
            if (bc) {
                bc.postMessage(payload)
            } else {
                try {
                    localStorage.setItem('connect_notifications', JSON.stringify(payload))
                } catch(e) {}
            }
        } catch(e) {}
    }
}