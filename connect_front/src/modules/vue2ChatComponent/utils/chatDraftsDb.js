const DB_NAME = 'chatDrafts'
const STORE_NAME = 'drafts'
const DB_VERSION = 1

const hasIndexedDb = () => typeof window !== 'undefined' && typeof window.indexedDB !== 'undefined'

const openDb = () => new Promise((resolve, reject) => {
    if (!hasIndexedDb()) {
        resolve(null)
        return
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => reject(request.error || new Error('Failed to open chat drafts db'))
    request.onsuccess = () => resolve(request.result)
    request.onupgradeneeded = event => {
        const db = event.target.result
        const store = db.objectStoreNames.contains(STORE_NAME)
            ? event.target.transaction.objectStore(STORE_NAME)
            : db.createObjectStore(STORE_NAME, { keyPath: 'id' })

        if (!store.indexNames.contains('userId')) {
            store.createIndex('userId', 'userId', { unique: false })
        }
    }
})

const getDraftId = (userId, chatUid) => `${userId}:${chatUid}`

const normalizeDraftPayload = ({ userId, chatUid, draft }) => ({
    ...draft,
    id: getDraftId(userId, chatUid),
    userId,
    chatUid,
    updatedAt: draft?.updatedAt || new Date().toISOString()
})

export const getChatDraft = async({ userId, chatUid }) => {
    const db = await openDb()
    if (!db || !userId || !chatUid) return null

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly')
        const store = tx.objectStore(STORE_NAME)
        const request = store.get(getDraftId(userId, chatUid))

        request.onerror = () => reject(request.error || new Error('Failed to read chat draft'))
        request.onsuccess = () => resolve(request.result || null)
    })
}

export const getChatDraftsByUser = async(userId) => {
    const db = await openDb()
    if (!db || !userId) return {}

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly')
        const store = tx.objectStore(STORE_NAME)
        const index = store.index('userId')
        const request = index.openCursor(IDBKeyRange.only(userId))
        const result = {}

        request.onerror = () => reject(request.error || new Error('Failed to read chat drafts'))
        request.onsuccess = event => {
            const cursor = event.target.result

            if (!cursor) {
                resolve(result)
                return
            }

            const value = cursor.value || {}
            if (value.chatUid) {
                result[value.chatUid] = value
            }
            cursor.continue()
        }
    })
}

export const saveChatDraft = async({ userId, chatUid, draft }) => {
    const db = await openDb()
    if (!db || !userId || !chatUid) return null

    const payload = normalizeDraftPayload({ userId, chatUid, draft })

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite')
        const store = tx.objectStore(STORE_NAME)
        const request = store.put(payload)

        request.onerror = () => reject(request.error || new Error('Failed to save chat draft'))
        request.onsuccess = () => resolve(payload)
    })
}

export const removeChatDraft = async({ userId, chatUid }) => {
    const db = await openDb()
    if (!db || !userId || !chatUid) return false

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite')
        const store = tx.objectStore(STORE_NAME)
        const request = store.delete(getDraftId(userId, chatUid))

        request.onerror = () => reject(request.error || new Error('Failed to delete chat draft'))
        request.onsuccess = () => resolve(true)
    })
}
