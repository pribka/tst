import axios from '@/config/axios'
import { errorHandler } from '@/utils/index.js'
import axiosMain from 'axios'
import notySyncChannel from '@/utils/notySyncChannel'
import { closeAllBrowserPushNotifications, closeBrowserPushNotification, closeBrowserPushNotifications } from '@/utils/browserPushNotifications'

let countSource = null
let categoriesRequestPromise = null
let listSource = null
let listRequestId = 0

const isCanceledRequest = error => axiosMain.isCancel?.(error) || error?.code === 'ERR_CANCELED'
export default {
    async getUnreadCount({ commit }) {
        let source;
        try {
            if(countSource)
                countSource.cancel()
            source = await axiosMain.CancelToken.source()
            countSource = { cancel: source.cancel }
            const { data } = await axios.get('notifications/unread_count/', { cancelToken: source.token })
            if(data) {
                commit('SET_UNREAD_COUNTS', {
                    unreadCount: data.unread_count,
                    unreadMentionsCount: data.unread_mentions_count,
                    unreadByCategory: data.unread_by_category
                })
                const totalUnread = (Number(data.unread_count) || 0) + (Number(data.unread_mentions_count) || 0)
                commit("SET_PWA_COUNTER", { name: 'noty', value: totalUnread }, { root: true })
                notySyncChannel.setCount({
                    count: totalUnread,
                    unread_count: data.unread_count,
                    unread_mentions_count: data.unread_mentions_count,
                    unread_by_category: data.unread_by_category
                })
            }
        } catch(error) {

        } finally {
            if(countSource === source)
                countSource = null
        }
    },
    async getCategories({ commit, state }) {
        if (state.categoriesLoaded && state.categories.length)
            return state.categories
        if (categoriesRequestPromise)
            return categoriesRequestPromise

        commit('SET_VALUE_STATE', { name: 'categoriesLoading', data: true })
        categoriesRequestPromise = axios.get('notifications/categories/')
            .then(({ data }) => {
                const categories = Array.isArray(data) ? data : []
                commit('SET_NOTIFICATION_CATEGORIES', categories)
                commit('SET_VALUE_STATE', { name: 'categoriesLoaded', data: true })
                return categories
            })
            .catch((error) => {
                errorHandler({ error, show: false })
                throw error
            })
            .finally(() => {
                commit('SET_VALUE_STATE', { name: 'categoriesLoading', data: false })
                categoriesRequestPromise = null
            })

        return categoriesRequestPromise
    },
    async refreshCategories({ commit }) {
        if (categoriesRequestPromise)
            return categoriesRequestPromise

        commit('SET_VALUE_STATE', { name: 'categoriesLoading', data: true })
        categoriesRequestPromise = axios.get('notifications/categories/')
            .then(({ data }) => {
                const categories = Array.isArray(data) ? data : []
                commit('SET_NOTIFICATION_CATEGORIES', categories)
                commit('SET_VALUE_STATE', { name: 'categoriesLoaded', data: true })
                return categories
            })
            .catch((error) => {
                errorHandler({ error, show: false })
                throw error
            })
            .finally(() => {
                commit('SET_VALUE_STATE', { name: 'categoriesLoading', data: false })
                categoriesRequestPromise = null
            })

        return categoriesRequestPromise
    },
    cancelListNotyRequest() {
        listRequestId += 1
        if (listSource) {
            listSource.cancel('Notifications list request cancelled')
            listSource = null
        }
    },
    getListNoty({ commit, state }, { page_name, filters = null, reset = false } = {}) {
        return new Promise((resolve, reject) => {
            if (reset) {
                if (listSource) {
                    listSource.cancel('Notifications list request cancelled')
                }
                listRequestId += 1
            }

            const requestId = listRequestId
            const nextPage = state.page + 1
            const source = axiosMain.CancelToken.source()
            listSource = source

            commit('SET_PAGE', nextPage)
            const params = {
                page_size: 10,
                page: nextPage,
                page_name
            }
            if (filters && Object.keys(filters).length) {
                params.filters = JSON.stringify(filters)
            }
            axios.get('notifications/', {
                params,
                cancelToken: source.token
            })
                .then(({ data }) => {
                    if (requestId !== listRequestId) {
                        resolve(null)
                        return
                    }

                    if (data) {
                        commit('SET_NEXT', data.next)
                        commit('SET_LIST_NOTY', data)
                    }
                    resolve(data)
                })
                .catch((error) => {
                    if (isCanceledRequest(error)) {
                        resolve(null)
                        return
                    }

                    if (requestId === listRequestId) {
                        commit('SET_PAGE', Math.max(0, nextPage - 1))
                        if (error?.response?.status === 404) {
                            commit('SET_NEXT', false)
                            resolve({ next: null, results: [] })
                            return
                        }
                    }
                    errorHandler({error, show: false})
                    reject(error)
                })
                .finally(() => {
                    if (listSource === source) {
                        listSource = null
                    }
                })
        })
    },
    getNotyBell({ commit }, { page, user }) {
        return new Promise((resolve, reject) => {
            axios.get('notifications/', {
                params: {
                    page_size: 10, page,
                    filters:
                    {
                        webnotificationrecipientmodel__is_read: false,
                        webnotificationrecipientmodel__recipient__id: user
                    }
                }
            })
                .then(({ data }) => {
                    if (data) {
                        commit('SET_LIST_NOTY_BELL', data)

                    }
                    resolve(data)
                })
                .catch((error) => { 
                    errorHandler({error, show: false})
                    reject(error) 
                })
        })
    },
    readNoty({ commit }, payload) {
        return new Promise((resolve, reject) => {
            const id = typeof payload === 'object' && payload !== null ? payload.id : payload
            const isMention = typeof payload === 'object' && payload !== null ? payload.isMention : null
            const categoryCode = typeof payload === 'object' && payload !== null ? payload.categoryCode : null
            const objectId = typeof payload === 'object' && payload !== null ? payload.objectId : null

            axios.post('notifications/is_read/', { notifications: [id] })
                .then(({ data }) => {
                    if (data) {
                        commit("READ_NOTY", { id, isMention, categoryCode })
                        notySyncChannel.readOne(id, { isMention, categoryCode, objectId })
                        closeBrowserPushNotification(id)
                    }
                    resolve(data)
                })
                .catch((error) => { 
                    errorHandler({error})
                    reject(error) 
                })
        })
    },
    readGroupNoty({ dispatch }, payload = {}) {
        return new Promise((resolve, reject) => {
            const objectId = typeof payload === 'object' && payload !== null ? payload.objectId : payload
            const notificationIds = Array.isArray(payload?.notificationIds) ? payload.notificationIds : []

            axios.post('notifications/is_read/', { object_id: objectId })
                .then(async ({ data }) => {
                    if (data) {
                        notySyncChannel.readGroup(objectId, { notificationIds })
                        await closeBrowserPushNotifications(notificationIds)
                    }
                    dispatch('getUnreadCount')
                    resolve(data)
                })
                .catch((error) => {
                    errorHandler({error})
                    reject(error)
                })
        })
    },
    readAllNoty({ commit, dispatch }, payload = {}) {
        return new Promise((resolve, reject) => {
            const categoryCodes = Array.isArray(payload.categoryCodes) ? payload.categoryCodes : []
            const isMention = !!payload.isMention
            const hasCategoryFilter = categoryCodes.length > 0
            const requestPayload = {
                notifications: 'all'
            }

            if (isMention) {
                requestPayload.is_mention = true
            } else if (hasCategoryFilter) {
                requestPayload.is_mention = false
                requestPayload.category = categoryCodes
            }

            axios.post('notifications/is_read/', requestPayload)
                .then(({ data }) => {
                    if (data) {
                        if (isMention) {
                            commit("READ_MENTION_NOTY")
                            notySyncChannel.readMentions()
                        } else if (hasCategoryFilter) {
                            commit("READ_NOTY_BY_CATEGORIES", { categoryCodes })
                            notySyncChannel.readByCategories(categoryCodes)
                        } else {
                            commit("READ_NOTY", { id: 'all' })
                            notySyncChannel.readAll()
                            notySyncChannel.setCount({
                                count: 0,
                                unread_count: 0,
                                unread_mentions_count: 0,
                                unread_by_category: {}
                            })
                            closeAllBrowserPushNotifications()
                        }
                    }
                    dispatch('getUnreadCount')
                    resolve(data)
                })
                .catch((error) => { 
                    errorHandler({error})
                    reject(error) 
                })
        })
    },
}
