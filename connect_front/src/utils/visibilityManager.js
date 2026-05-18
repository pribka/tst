let refCount = 0
let tabId = null
function ensureInit() {
    if(tabId)
        return
    tabId = sessionStorage.getItem('connect_tab_id') || `tab_${Date.now()}_${Math.random().toString(36).slice(2)}`
    sessionStorage.setItem('connect_tab_id', tabId)
    updateVisibilityRecord()
    document.addEventListener('visibilitychange', updateVisibilityRecord)
    window.addEventListener('storage', onStorageEvent)
    window.addEventListener('focus', updateVisibilityRecord)
    window.addEventListener('blur', updateVisibilityRecord)
    window.addEventListener('beforeunload', cleanupOnUnload)
}
function updateVisibilityRecord() {
    try {
        const isVisible = document.visibilityState === 'visible'
        const raw = localStorage.getItem('connect_visible_tabs') || '{}'
        let obj = JSON.parse(raw || '{}')
        if(isVisible)
            obj[tabId] = Date.now()
        else
            delete obj[tabId]
        localStorage.setItem('connect_visible_tabs', JSON.stringify(obj))
    } catch(e) {}
}
function onStorageEvent(e) {
    if(e.key !== 'connect_visible_tabs')
        return
}
function cleanupOnUnload() {
    try {
        const raw = localStorage.getItem('connect_visible_tabs') || '{}'
        const obj = JSON.parse(raw || '{}')
        delete obj[tabId]
        localStorage.setItem('connect_visible_tabs', JSON.stringify(obj))
    } catch(e) {}
}
export default {
    init() {
        refCount++
        ensureInit()
    },
    destroy() {
        refCount = Math.max(0, refCount - 1)
        if(refCount === 0) {
            document.removeEventListener('visibilitychange', updateVisibilityRecord)
            window.removeEventListener('storage', onStorageEvent)
            window.removeEventListener('focus', updateVisibilityRecord)
            window.removeEventListener('blur', updateVisibilityRecord)
            window.removeEventListener('beforeunload', cleanupOnUnload)
        }
    },
    getNotifyDuration() {
        try {
            return document.visibilityState === 'visible' ? 10 : 0
        } catch(e) {
            return 0
        }
    }
}