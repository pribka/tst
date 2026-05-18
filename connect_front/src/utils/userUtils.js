import { setData, getById, updateById } from './cacheDb'

const databaseName = 'users'
const updateUserData = (data) => {
    updateById({
        id: 'list',
        value: JSON.stringify(data),
        databaseName
    })
}

export const getUsers = () => {
    return new Promise((resolve, reject) => {
        getById({id: 'list', databaseName})
            .then(dbData => {
                resolve(dbData)
            })
            .catch(e => {reject(e)})
    })
}

export const saveUsers = (data) => {
    getById({id: 'list', databaseName})
        .then(dbData => {
            if(dbData?.value) {
                let users = JSON.parse(dbData.value)
                const index = users.findIndex(f => f.email === data.email)
                if(index !== -1) {
                    users.splice(index, 1)
                    users.unshift({
                        email: data.email,
                        username: data.username
                    })
                } else
                    users.unshift({
                        email: data.email,
                        username: data.username
                    })

                updateUserData(users)
            } else {
                setData({
                    data: {
                        id: 'list',
                        value: JSON.stringify([{
                            email: data.email,
                            username: data.username
                        }])
                    },
                    databaseName
                })
            }
        })
        .catch(e => {console.log(e)})
}