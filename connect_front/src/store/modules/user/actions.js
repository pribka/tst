import axios from '@/config/axios'
import socket from '@/config/socket'
import { saveUsers, getUsers } from '@/utils/userUtils'
import eventBus from '@/utils/eventBus'
import { getBrowserTimeZone } from '@/utils/timezones'

const deleteDb = (name) => {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase(name)
        req.onerror = () => {
            reject(false)
        }

        req.onsuccess = () => {
            resolve(true)
        }

        req.onblocked = () => {
            resolve(true)
            console.log("Couldn't delete database due to the operation being blocked")
        }
    })
}

const localStorageClear = () => {
    localStorage.removeItem('miniMenu')
    localStorage.removeItem('task_list_type')
    localStorage.removeItem('ticket_list_type')
}

export default {
    skipPassword({commit}) {
        return new Promise((resolve, reject) => {
            axios.post('/users/skip_set_new_password/')
                .then(({data}) => {
                    commit('DISABLE_PASS_GENERATE')
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    setPassword({commit}, form) {
        return new Promise((resolve, reject) => {
            axios.post('/users/set_new_password/', form)
                .then(({data}) => {
                    commit('DISABLE_PASS_GENERATE')
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getProfileMenu({commit, state}) {
        return new Promise((resolve, reject) => {
            if(state.profileMenu?.length) {
                resolve(state.profileMenu)
            } else {
                axios.get('/app_info/private_office/')
                    .then(({data}) => {
                        commit('SET_PROFILE_MENU', data)
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    async localUserLogout({commit, rootState}) {
        try {
            commit('SET_REDIRECT_LANG')
            socket.disconnect()
        
            if(rootState.storageList?.length) {
                rootState.storageList.forEach(item => {
                    localStorage.removeItem(item)
                })
            }

            if(rootState.dbList?.length) {
                for(const key in rootState.dbList) {
                    await deleteDb(rootState.dbList[key])
                }
            }

            await deleteDb('bannerNews').catch(() => true)

            localStorage.removeItem('lang')
            commit('SET_USER', null)
            localStorageClear()
        } catch(e) {
            console.log(e, 'localUserLogout')
        }
    },
    async localUserLogout2({commit, rootState}) {
        try {
            commit('SET_REDIRECT_LANG')
            socket.disconnect()
        
            if(rootState.storageList?.length) {
                rootState.storageList.forEach(item => {
                    localStorage.removeItem(item)
                })
            }

            await deleteDb('bannerNews').catch(() => true)

            localStorage.removeItem('lang')
            commit('SET_USER', null)
            localStorageClear()
        } catch(e) {
            console.log(e, 'localUserLogout')
        }
    },
    logout({ dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get('/users/logout/')
                .then(({data}) => {
                    dispatch('localUserLogout2')
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    login({ commit }, form) {
        return new Promise((resolve, reject) => {
            axios.post('/users/login2/', form)
                .then(({data}) => {
                    if(data) {
                        saveUsers(data)
                        //localStorage.setItem('user', JSON.stringify(data))
                        commit('SET_USER', data)
                        // socket.connect()
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getUserInfo({ commit, dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get('/users/info/')
                .then(async ({data}) => {
                    if(data?.status !== 401 && data?.user) {
                        let currentUser = data.user

                        if (currentUser?.timezone_auto_detect) {
                            const browserTimezone = getBrowserTimeZone()
                            if (browserTimezone && currentUser.timezone !== browserTimezone) {
                                try {
                                    const { data: updatedUser } = await axios.put('/users/update_profile/', {
                                        timezone: browserTimezone
                                    })
                                    if (updatedUser) {
                                        currentUser = updatedUser
                                    } else {
                                        currentUser = {
                                            ...currentUser,
                                            timezone: browserTimezone
                                        }
                                    }
                                } catch (error) {
                                    console.log(error, 'timezone auto detect sync')
                                }
                            }
                        }

                        data.user = currentUser
                        //localStorage.setItem('user', JSON.stringify(currentUser))
                        commit('SET_USER', currentUser)
                        socket.connect()
                        eventBus.$emit('user_logged')
                    } else {
                        dispatch('localUserLogout')
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    init({ commit }) {
        return new Promise((resolve, reject) => {
            getUsers()
                .then(data => {
                    if(data?.value) {
                        commit('SET_USER_AUTH', data.value)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getAuthConfig({ commit }) {
        return new Promise((resolve, reject) => {
            axios.get('/app_info/entry/')
                .then(({data}) => {
                    commit('SET_AUTH_CONFIG', data)
                    resolve(data)
                })
                .catch((error) => { 
                    commit('SET_AUTH_CONFIG', {
                        default: true
                    })
                    resolve({
                        default: true
                    }) })
        })
    },
}
