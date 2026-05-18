import axios from '@/config/axios'
import { setData, getById, deleteDb, updateById } from '@/utils/cacheDb'

export default {
    loginConfigInit({ dispatch, commit, state }) {
        return new Promise((resolve, reject) => {
            const params = {}
            /*if(state.isMobile) {
                params.ver = 'mobile'
            }*/
            axios.get('/app_info/global/', { params }).
                then(({ data }) => {
                    getById({ id: 'global', databaseName: 'config' })
                        .then(dbData => {
                            if (dbData?.value) {
                                updateById({
                                    id: 'global',
                                    value: data,
                                    databaseName: 'config'
                                })
                                    .then(() => {
                                        dispatch('config/init', { data })
                                        resolve(data)
                                    })
                                    .catch(e => {
                                        reject(e)
                                    })
                            } else {
                                setData({
                                    data: {
                                        id: 'global',
                                        value: data
                                    },
                                    databaseName: 'config'
                                })
                                    .then(() => {
                                        dispatch('config/init', { data })
                                        resolve(data)
                                    })
                                    .catch(e => {
                                        reject(e)
                                    })
                            }
                        })
                        .catch(e => {
                            console.log(e)
                        })
                })
                .catch(e => {
                    console.log(e, 'config init')
                    reject(e)
                })
        })
    },
    /*loginAppInit({ dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get('/app_info/routes/').
                then(({ data }) => {
                    getById({ id: 'routes', databaseName: 'config' })
                        .then(dbData => {
                            if (dbData?.value?.length) {
                                updateById({
                                    id: 'routes',
                                    value: data,
                                    databaseName: 'config'
                                })
                                    .then(() => {
                                        setTimeout(() => {
                                            dispatch('navigation/init', { data })
                                            dispatch('table/init', { data })
                                            dispatch('form/init', { data })
                                            resolve(data)
                                        }, 600)
                                    })
                                    .catch(e => {
                                        reject(e)
                                    })
                            } else {
                                setData({
                                    data: {
                                        id: 'routes',
                                        value: data
                                    },
                                    databaseName: 'config'
                                })
                                    .then(() => {
                                        setTimeout(() => {
                                            dispatch('navigation/init', { data })
                                            dispatch('table/init', { data })
                                            dispatch('form/init', { data })
                                            resolve(data)
                                        }, 600)
                                    })
                                    .catch(e => {
                                        reject(e)
                                    })
                            }
                        })
                        .catch(e => {
                            console.log(e)
                        })
                })
                .catch(e => {
                    console.log(e, 'app init')
                    reject(e)
                })
        })
    },*/
    getCacheUID({ commit, state }) {
        return new Promise((resolve, reject) => {
            axios.get('/app_info/check_front_cache/')
                .then(({ data }) => {
                    getById({ id: 'isMobile', databaseName: 'app_type' })
                        .then(async dbData => {
                            let update = false
                            if (dbData) {
                                if(dbData.value !== state.isMobile) {
                                    update = true
                                    updateById({
                                        id: 'isMobile',
                                        value: state.isMobile,
                                        databaseName: 'app_type'
                                    })
                                }
                            } else {
                                setData({
                                    data: {
                                        id: 'isMobile',
                                        value: state.isMobile
                                    },
                                    databaseName: 'app_type'
                                })
                            }

                            if(state.cacheUID || update) {
                                if(state.cacheUID !== data.uid || update) {
                                    await deleteDb({databaseName: 'config'})
                                    await deleteDb({databaseName: 'table'})
                                    await deleteDb({databaseName: 'task'})
                                    console.log(`%c UPDATE CACHE 🔄`, 'color: #fa8c16')
                                } else {
                                    console.log(`%c LOAD CACHE 🚀`, 'color: #04d182')
                                }
                            }
        
                            localStorage.setItem('cacheUID', data.uid)
                            commit('SET_CACHE_UID', data.uid)
                            resolve(data)
                        })
                        .catch(e => {
                            console.log(e, 'check cache init')
                            reject(e)
                        })
                })
                .catch(e => {
                    console.log(e, 'check cache init')
                    reject(e)
                })
        })
    },
    configInit({ dispatch, commit, state }) {
        return new Promise((resolve, reject) => {
            getById({ id: 'global', databaseName: 'config' })
                .then(dbData => {
                    if (dbData?.value) {
                        dispatch('config/init', { data: dbData.value })
                        resolve(dbData.value)
                    } else {
                        const params = {}
                        /*if(state.isMobile) {
                            params.ver = 'mobile'
                        }*/
                        axios.get('/app_info/global/', { params }).
                            then(({ data }) => {
                                setData({
                                    data: {
                                        id: 'global',
                                        value: data
                                    },
                                    databaseName: 'config'
                                })
                                dispatch('config/init', { data })
                                resolve(data)
                            })
                            .catch(e => {
                                console.log(e, 'config init')
                                reject(e)
                            })
                    }

                })
                .catch(e => {
                    console.log(e)
                })
        })
    },
    /*
    appInit({ dispatch }) {
        return new Promise((resolve, reject) => {
            getById({ id: 'routes', databaseName: 'config' })
                .then(dbData => {
                    if (dbData?.value?.length) {
                        dispatch('navigation/init', { data: dbData.value })
                        dispatch('table/init', { data: dbData.value })
                        dispatch('form/init', { data: dbData.value })
                        resolve(dbData.value)
                    } else {
                        axios.get('/app_info/routes/').
                            then(({ data }) => {
                                setData({
                                    data: {
                                        id: 'routes',
                                        value: data
                                    },
                                    databaseName: 'config'
                                })
                                    .then(() => {
                                        setTimeout(() => {
                                            dispatch('navigation/init', { data })
                                            dispatch('table/init', { data })
                                            dispatch('form/init', { data })
                                            resolve(data)
                                        }, 600)
                                    })
                                    .catch(e => {
                                        reject(e)
                                    })
                            })
                            .catch(e => {
                                console.log(e, 'app init')
                                reject(e)
                            })
                    }

                })
                .catch(e => {
                    console.log(e)
                })
        })
    }*/
}
