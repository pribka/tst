const connectDb = () => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('sort', 1)

        request.onerror = e => {
            console.log('Error opening db', e)
            reject('Error')
        }

        request.onsuccess = e => {
            resolve(e.target.result)
        }

        request.onupgradeneeded = e => {
            const db = e.target.result
            const store = db.createObjectStore("data", { keyPath:'id' })
            store.createIndex('id', 'id')
        }
    })
}

export const setData = async(payload) => {
    const db = await connectDb()
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')

    return new Promise((resolve, reject) => {
        const req = store.add(payload)

        req.onsuccess = e => {
            resolve(e.target.result)
        }
    })
}

export const deleteDataById = async(id) => {
    const db = await connectDb()
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')

    return new Promise((resolve, reject) => {
        const req = store.delete(id)

        req.onerror = e => {
            reject(false)
        }

        req.onsuccess = e => {
            resolve(e.target.result)
        }
    })
}

export const getDataById = async(id) => {
    const db = await connectDb()
    const tx = db.transaction('data')
    const store = tx.objectStore('data')

    return new Promise((resolve, reject) => {
        const req = store.get(id)

        req.onerror = e => {
            reject(false)
        }

        req.onsuccess = e => {
            resolve(e.target.result)
        }
    })
}

export const getDataAll = async() => {
    const db = await connectDb()
    const tx = db.transaction('data')
    const store = tx.objectStore('data')

    return new Promise((resolve, reject) => {
        const req = store.getAll()

        req.onerror = e => {
            reject(false)
        }

        req.onsuccess = e => {
            resolve(e.target.result)
        }
    })
}

export const updateDataById = async({id, value}) => {
    const db = await connectDb()
    const tx = db.transaction('data', 'readwrite')
    const store = tx.objectStore('data')

    return new Promise((resolve, reject) => {
        const req = store.get(id)

        req.onerror = e => {
            reject(false)
        }

        req.onsuccess = e => {
            let data = e.target.result
            data.value = value

            const reqUpdate = store.put(data)

            reqUpdate.onerror = e => {
                reject(false)
            }

            reqUpdate.onsuccess = e => {
                resolve(e.target.result)
            }
        }
    })
}

export const deleteDb = () => {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase('table')

        req.onerror = function(event) {
            reject(false)
        }

        req.onsuccess = function(event) {
            resolve(true)
        }
    })
}