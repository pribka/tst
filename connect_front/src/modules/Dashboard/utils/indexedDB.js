const connectDb = (databaseName) => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(databaseName, 1)

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

// Установить значение
export const setData = async({data, databaseName}) => {
    const db = await connectDb(databaseName)
    const tx = await db.transaction('data', 'readwrite')
    const store = await tx.objectStore('data')
    return new Promise((resolve, reject) => {
        const req = store.add(data)

        req.onsuccess = e => {
            resolve(e.target.result)
        }
    })
}

// Удалить значние по id
export const deleteById = async({id, databaseName}) => {
    const db = await connectDb(databaseName)
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

// Получить значение по id
export const getById = async({id, databaseName}) => {
    const db = await connectDb(databaseName)
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

// Обновить значение по id
export const updateById = async({id, value, databaseName}) => {
    const db = await connectDb(databaseName)
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

// Удалить таблицу
export const deleteDb = ({databaseName}) => {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase(databaseName)

        req.onerror = function(event) {
            reject(false)
        }

        req.onsuccess = function(event) {
            resolve(true)
        }
    })
}