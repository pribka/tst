const ensureDb = (databaseName, version) => {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(databaseName, version || undefined)
        req.onerror = e => reject('Error')
        req.onupgradeneeded = e => {
            const db = e.target.result
            let store
            if (!db.objectStoreNames.contains('data')) {
                store = db.createObjectStore('data', { keyPath: 'id' })
            } else {
                store = e.target.transaction.objectStore('data')
            }
            const indexes = ['id','groups_select','organizations_select','projects_select','user_select']
            indexes.forEach(ix => {
                if (!store.indexNames.contains(ix)) store.createIndex(ix, 'id')
            })
        }
        req.onsuccess = e => resolve(e.target.result)
    })
}

const connectDb = databaseName => {
    return new Promise((resolve, reject) => {
        ensureDb(databaseName)
            .then(db => {
                const needStore = !db.objectStoreNames.contains('data')
                let needIndexes = []
                if (!needStore) {
                    try {
                        const tx = db.transaction('data', 'readonly')
                        const store = tx.objectStore('data')
                        const indexes = ['id','groups_select','organizations_select','projects_select','user_select']
                        indexes.forEach(ix => {
                            if (!store.indexNames.contains(ix)) needIndexes.push(ix)
                        })
                    } catch (_) {
                    }
                }
                if (needStore || needIndexes.length) {
                    const nextVersion = db.version + 1
                    db.close()
                    ensureDb(databaseName, nextVersion)
                        .then(db2 => resolve(db2))
                        .catch(() => reject('Error'))
                } else {
                    resolve(db)
                }
            })
            .catch(() => reject('Error'))
    })
}

export const setData = async ({ data, databaseName }) => {
    const db = await connectDb(databaseName)
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')
    return new Promise((resolve, reject) => {
        const req = store.put(data)
        req.onerror = e => reject(false)
        req.onsuccess = e => resolve(e.target.result)
    })
}

export const deleteById = async ({ id, databaseName }) => {
    const db = await connectDb(databaseName)
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')
    return new Promise((resolve, reject) => {
        const req = store.delete(id)
        req.onerror = e => reject(false)
        req.onsuccess = e => resolve(e.target.result)
    })
}

export const getById = async ({ id, databaseName }) => {
    const db = await connectDb(databaseName)
    const tx = db.transaction('data')
    const store = tx.objectStore('data')
    return new Promise((resolve, reject) => {
        const req = store.get(id)
        req.onerror = e => reject(false)
        req.onsuccess = e => resolve(e.target.result)
    })
}

export const updateById = async ({ id, value, databaseName }) => {
    const db = await connectDb(databaseName)
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')
    return new Promise((resolve, reject) => {
        const req = store.get(id)
        req.onerror = e => reject(false)
        req.onsuccess = e => {
            let data = e.target.result
            if (data) {
                data.value = value
            } else {
                data = { id, value }
            }
            const reqUpdate = store.put(data)
            reqUpdate.onerror = e => reject(false)
            reqUpdate.onsuccess = e => resolve(e.target.result)
        }
    })
}

export const deleteDb = ({ databaseName }) => {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase(databaseName)
        req.onerror = event => reject(false)
        req.onsuccess = event => resolve(true)
    })
}
