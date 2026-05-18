const buildVersion = process.env.VUE_APP_BUILD_VERSION || ''

const clearCachesAndReload = async () => {
    try {
        if ('caches' in window) {
            const keys = await caches.keys()
            await Promise.all(keys.map(k => caches.delete(k)))
        }
        if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
            const regs = await navigator.serviceWorker.getRegistrations()
            await Promise.all(regs.map(r => r.unregister()))
        }
    } catch (e) {}
    window.location.reload(true)
}

const checkVersionOnce = async () => {
    try {
        if (navigator.serviceWorker && navigator.serviceWorker.controller) {
            await new Promise(resolve => {
                const onMsg = (e) => {
                    try {
                        if (e.data && e.data.type === 'VERSION_RESPONSE') {
                            navigator.serviceWorker.removeEventListener('message', onMsg)
                            const data = e.data.version
                            if (data && data.version && data.version !== buildVersion) clearCachesAndReload()
                            resolve()
                        }
                    } catch (err) {
                        navigator.serviceWorker.removeEventListener('message', onMsg)
                        resolve()
                    }
                }
                navigator.serviceWorker.addEventListener('message', onMsg)
                try {
                    navigator.serviceWorker.controller.postMessage({ type: 'GET_VERSION', ts: Date.now() })
                } catch (e) {
                    navigator.serviceWorker.removeEventListener('message', onMsg)
                    resolve()
                }
                setTimeout(() => { navigator.serviceWorker.removeEventListener('message', onMsg); resolve() }, 5000)
            })
            return
        }

        const res = await fetch(`/version.json?v=${Date.now()}`, { cache: 'no-store' })
        const data = await res.json()
        if (data && data.version && data.version !== buildVersion) await clearCachesAndReload()
    } catch (e) {}
}

export default function setupVersionWatch(router) {
    checkVersionOnce()
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') checkVersionOnce()
    })
    if (router && router.afterEach) {
        let last = 0
        router.afterEach(() => {
            const now = Date.now()
            if (now - last > 60000) {
                last = now
                checkVersionOnce()
            }
        })
    }
}
