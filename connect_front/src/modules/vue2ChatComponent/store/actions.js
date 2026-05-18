import axios from '@/config/axios'
import axiosMain from 'axios'
import ChatEventBus from '../utils/ChatEventBus'

let countTimer;
let countSource = null
let sidebarChatPendingRequest = null
let sidebarChatPendingMode = null
let sidebarChatCancelSource = null
let activeChatDetailRequestId = 0
let activeChatDetailCancelSource = null
let activeChatMessageCancelSource = null
let activeChatPinCancelSource = null

const createSidebarChatCancelError = () => {
    const error = new Error('Sidebar chat request canceled')
    error.__CANCEL__ = true
    return error
}

const isCancelError = error => axiosMain.isCancel(error) || error?.__CANCEL__

const cancelSourceSilently = source => {
    if (source?.cancel) source.cancel('Canceled due to a newer chat request')
}

export default {
    async searchChatMessages({ commit }, { chat_uid, text }) {
        if (!chat_uid) return

        const q = (text || '').toString().trim()
        commit('SET_CHAT_SEARCH_TEXT', { chat_uid, text: q })

        const key = `${chat_uid}|${q}`
        commit('CLEAR_CHAT_SEARCH_MORE_SCROLL_DONE', key)

        if (!q) {
            commit('CLEAR_CHAT_SEARCH', chat_uid)
            return
        }

        if (q.length < 3) {
            commit('SET_CHAT_SEARCH_MESSAGES', { chat_uid, data: { results: [], next: null }, query: q, page_size: 15 })
            return
        }

        const page_size = 15

        try {
            commit('SET_CHAT_SEARCH_LOADING', { chat_uid, value: true })
            const { data } = await this._vm.$http.get('/chat/message/search/', {
                params: { text: q, chat: chat_uid, page_size, page: 1 }
            })
            commit('SET_CHAT_SEARCH_MESSAGES', { chat_uid, data, query: q, page_size })
        } finally {
            commit('SET_CHAT_SEARCH_LOADING', { chat_uid, value: false })
        }
    },

    async searchChatMessagesMore({ commit, state }, chat_uid) {
        if (!chat_uid) return

        const q = (state.chatSearchTextByChat?.[chat_uid] || '').toString().trim()
        const bucket = state.chatSearchMessageByChat?.[chat_uid]

        if (!q || q.length < 3 || !bucket) return
        if (bucket.loading) return

        if ((bucket.query || '').trim() !== q) return

        if (!bucket.hasMore) return

        const page_size = 15
        const nextPage = (bucket.page || 1) + 1

        try {
            commit('SET_CHAT_SEARCH_LOADING', { chat_uid, value: true })
            const { data } = await this._vm.$http.get('/chat/message/search/', {
                params: { text: q, chat: chat_uid, page_size, page: nextPage }
            })
            commit('PUSH_CHAT_SEARCH_MESSAGES', { chat_uid, data, page: nextPage, page_size })
        } finally {
            commit('SET_CHAT_SEARCH_LOADING', { chat_uid, value: false })
        }
    },
    getReactions({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.reactions.length)
                resolve(state.reactions)
            else {
                axios.get('/reactions/', {
                    params: {
                        page_size: 10
                    }
                })
                    .then(({ data }) => {
                        if(data?.results?.length)
                            commit('SET_REACTIONS', data.results)
                        resolve(data)
                    })
                    .catch(e => {
                        console.log(e)
                        reject(e)
                    })
            }
        })
    },
    getMessageCount({ commit }) {
        clearTimeout(countTimer)
        countTimer = setTimeout(async () => {
            let source;
            try {
                if(countSource)
                    countSource.cancel()
                source = await axiosMain.CancelToken.source()
                countSource = { cancel: source.cancel }
                const { data } = await axios.get('chat/message/count/', { cancelToken: source.token })
                if(data) {
                    commit("SET_PWA_COUNTER", { name: 'chat', value: data.count }, { root: true })
                    commit("navigation/SET_MENU_COUNTER", { value: data, name: "chat" }, { root: true })
                }
            } catch(error) {
                console.log(error)
            } finally {
                if(countSource === source)
                    countSource = null
            }
        }, 500)
    },
    getUnreadMessageCountByChatId({ commit }, chatUid) {
        const url = 'chat/message/count/'
        const params = { chat: chatUid }
        return axios.get(url, { params })
            .then(({ data }) => {
                commit('SET_UNREAD_MESSAGE_COUNT_BY_CHAT_ID', { chatUid, messageCount: data.count })
            })
            .catch(error => {
                console.error(error)
            })
    },
    getLastMessageByChatId({ commit }, chatUid) {
        const url = `chat/${chatUid}/last_message/`
        return axios.get(url)
            .then(({ data }) => {
                commit('SET_LAST_MESSAGE_BY_CHAT_ID', { chatUid, lastMessage: data })
            })
            .catch(error => {
                console.error(error)
            })
    },
    getChatMembers({ commit, state }, { chat }) {
        return new Promise((resolve, reject) => {
            axios.get('/chat/member/list/', {
                params: {
                    page: state.chatMembers?.[chat]?.page ? state.chatMembers[chat].page : 1,
                    page_size: 18,
                    chat
                }
            })
                .then(({ data }) => {
                    if (state.chatMembers?.[chat]?.results?.length) {
                        commit('CONCAT_CHAT_MEMBERS', { data, chat })
                    } else {
                        commit('SET_CHAT_MEMBERS', { data, chat })
                    }
                    resolve(data)
                })
                .catch(e => {
                    console.log(e)
                    reject(e)
                })
        })
    },
    cancelSidebarChatPrefetch() {
        if (sidebarChatPendingMode === 'prefetch' && sidebarChatCancelSource) {
            sidebarChatCancelSource.cancel('Sidebar chat prefetch canceled')
        }

        return Promise.resolve()
    },
    getSidebarChat({ commit, state }, options = {}) {
        return new Promise((resolve, reject) => {
            const mode = options.prefetch ? 'prefetch' : 'default'

            if (sidebarChatPendingRequest) {
                if (mode === 'default' && sidebarChatPendingMode === 'prefetch' && sidebarChatCancelSource) {
                    sidebarChatCancelSource.cancel('Sidebar chat prefetch canceled by foreground request')
                } else {
                    sidebarChatPendingRequest.then(resolve).catch(reject)
                    return
                }
            }

            const nextPage = state.chatListPage + 1
            sidebarChatCancelSource = axiosMain.CancelToken.source()

            const request = axios.get('/chat/list/', {
                params: {
                    page: nextPage,
                    page_size: 15
                },
                cancelToken: sidebarChatCancelSource.token
            })
                .then(({ data }) => {
                    commit('SET_CHAT_LIST_PAGE', nextPage)
                    commit('CONCAT_CHAT', data.results)
                    commit('SET_CHAT_LIST_NEXT', data.next)
                    resolve(data)
                    return data
                })
                .catch(e => {
                    if (axiosMain.isCancel(e) || e?.__CANCEL__) {
                        reject(createSidebarChatCancelError())
                        throw createSidebarChatCancelError()
                    }

                    console.log(e)
                    reject(e)
                    throw e
                })
                .finally(() => {
                    if (sidebarChatPendingRequest === request) {
                        sidebarChatPendingRequest = null
                        sidebarChatPendingMode = null
                        sidebarChatCancelSource = null
                    }
                })

            sidebarChatPendingRequest = request
            sidebarChatPendingMode = mode
        })
    },
    getSidebarContact({ commit, state }, { all, search, user }) {
        return new Promise((resolve, reject) => {
            commit('SET_CONTACT_LIST_PAGE', state.contactListPage + 1)

            let fullname = ''

            if(search?.length)
                fullname = search

            if(fullname?.length) {
                axios.get('/users/search/', {
                    params: {
                        page_size: 15,
                        fullname,
                        exclude_users: user.id
                    }
                })
                    .then(({ data }) => {
                        commit('CONCAT_CONTACTS', data.results)
                        commit('SET_CONTACT_LIST_NEXT', data.next)
                        resolve(data)
                    })
                    .catch(e => {
                        console.log(e)
                        reject(e)
                    })
            } else {
                axios.get('/chat/users/', {
                    params: {
                        page: state.contactListPage,
                        page_size: 15,
                        all
                    }
                })
                    .then(({ data }) => {
                        commit('CONCAT_CONTACTS', data.results)
                        commit('SET_CONTACT_LIST_NEXT', data.next)
                        resolve(data)
                    })
                    .catch(e => {
                        console.log(e)
                        reject(e)
                    })
            }
        })
    },
    // Основной список help-desk
    getSidebarHelpDesk({ commit, state }, { all } = {}) {
        return new Promise((resolve, reject) => {
            commit('SET_HELPDESK_LIST_PAGE', state.helpDeskPage + 1)
            axios.get('/chat/users/', {
                params: {
                    page: state.helpDeskPage,
                    page_size: 15,
                    all,
                    display: 'help_desk',
                }
            })
                .then(({ data }) => {
                    commit('CONCAT_HELPDESK', data.results)
                    commit('SET_HELPDESK_LIST_NEXT', data.next)
                    resolve(data)
                })
                .catch(e => {
                    console.log(e)
                    reject(e)
                })
        })
    },

    // Поиск внутри help-desk (через /chat/users/ с параметром search)
    getSidebarHelpDeskSearch({ commit, state }, { search, all } = {}) {
        return new Promise((resolve, reject) => {
            commit('SET_HELPDESK_LIST_PAGE', state.helpDeskPage + 1)
            axios.get('/chat/users/', {
                params: {
                    page: state.helpDeskPage,
                    page_size: 15,
                    all,
                    search,
                    display: 'help_desk',
                }
            })
                .then(({ data }) => {
                    commit('CONCAT_HELPDESK', data.results)
                    commit('SET_HELPDESK_LIST_NEXT', data.next)
                    resolve(data)
                })
                .catch(e => {
                    console.log(e)
                    reject(e)
                })
        })
    },

    // Очистить список (например, при смене вкладки/вида)
    clearHelpDeskList({ commit }) {
        commit('CLEAR_HELPDESK_LIST')
    },
    getGroupContact({ commit, state }, { chat }) {
        return new Promise((resolve, reject) => {
            commit('SET_CONTACT_GROUP_PAGE', state.contactGroupPage + 1)

            axios.get('/chat/users/', {
                params: {
                    page: state.contactGroupPage,
                    page_size: 15,
                    chat
                }
            })
                .then(({ data }) => {
                    commit('CONTACT_GROUP_CONTACTS', data.results)
                    commit('SET_CONTACT_GROUP_NEXT', data.next)
                    resolve(data)
                })
                .catch(e => {
                    console.log(e)
                    reject(e)
                })
        })
    },
    getGroupContactSearch({ commit, state }, { search, chat }) {
        return new Promise((resolve, reject) => {
            commit('SET_CONTACT_GROUP_PAGE', state.contactGroupPage + 1)

            axios.get('/chat/users/', {
                params: {
                    page: state.contactGroupPage,
                    page_size: 15,
                    search,
                    chat
                }
            })
                .then(({ data }) => {
                    commit('CONTACT_GROUP_CONTACTS', data.results)
                    commit('SET_CONTACT_GROUP_NEXT', data.next)
                    resolve(data)
                })
                .catch(e => {
                    console.log(e)
                    reject(e)
                })
        })
    },
    getMessage({ commit, state }, payload = false) {
        return new Promise((resolve, reject) => {
            const options = typeof payload === 'object' && payload !== null ? payload : { refresh: !!payload }
            const refresh = !!options.refresh
            const chat_uid = options.chat_uid || state.activeChat?.chat_uid

            if (!chat_uid) {
                resolve(null)
                return
            }

            if (state.chatMessage[chat_uid] && !refresh) {
                resolve(state.chatMessage[chat_uid])
                return
            }

            cancelSourceSilently(activeChatMessageCancelSource)
            const source = axiosMain.CancelToken.source()
            activeChatMessageCancelSource = source

            axios.get('/chat/message/list/', {
                params: {
                    page_size: 15,
                    chat: chat_uid,

                },
                cancelToken: source.token
            })
                .then(({ data }) => {
                    commit('OPEN_CHAT_MESSAGE', { chat_uid, data })
                    resolve(data)
                })
                .catch((error) => {
                    if (isCancelError(error)) {
                        resolve(null)
                        return
                    }
                    reject(error)
                })
                .finally(() => {
                    if (activeChatMessageCancelSource === source) {
                        activeChatMessageCancelSource = null
                    }
                })
        })
    },
    getUnreadEntryMessages({ commit }, payload = {}) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid
            const page_size = payload.page_size || 20

            if (!chat_uid) {
                resolve(null)
                return
            }

            axios.get(`/chat/${chat_uid}/message/unread_entry/`, {
                params: {
                    page_size
                }
            })
                .then(({ data }) => {
                    // При наличии unread входим в чат через специальный срез,
                    // чтобы стартовать у границы первого непрочитанного.
                    if (data?.history_mode && Array.isArray(data.results) && data.results.length) {
                        commit('OPEN_CHAT_MESSAGE', { chat_uid, data })
                        commit('SET_CHAT_HISTORY_STATE', {
                            chat_uid,
                            data: {
                                // Кирилл: readCursorCreated - текущая граница "прочитано".
                                // dividerCreated/dividerAtStart - отдельная привязка линии входа,
                                // чтобы линия "Новые сообщения" не ездила за живым read-progress.
                                active: true,
                                canLoadAfter: !!(data.previous && data.previous.length),
                                unreadCount: data.unread_count,
                                unreadMentionCount: data.unread_mention_count,
                                readCursorCreated: data.last_read_created || null,
                                dividerCreated: data.last_read_created || null,
                                dividerAtStart: !data.last_read_created && Number(data.unread_count || 0) > 0,
                                afterCreated: data.results[data.results.length - 1]?.created || null
                            }
                        })
                    } else {
                        commit('CLEAR_CHAT_HISTORY', chat_uid)
                    }

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    getHistoryAfterMessages({ commit, state }, payload = {}) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
            const historyState = state.chatHistoryStateByChat?.[chat_uid]

            // В history-режиме двигаемся только вперед по дате последнего элемента,
            // без использования id страницы/сообщения.
            if (!chat_uid || !historyState?.afterCreated) {
                resolve(null)
                return
            }

            axios.get(`/chat/${chat_uid}/message/history_after/`, {
                params: {
                    page_size: payload.page_size || 20,
                    after_created: historyState.afterCreated
                }
            })
                .then(({ data }) => {
                    const results = Array.isArray(data?.results) ? data.results : []

                    if (results.length) {
                        commit('PUSH_CHAT_MESSAGE', { chat_uid, data })
                    }

                    commit('UPDATE_CHAT_HISTORY_CURSOR', {
                        chat_uid,
                        afterCreated: data?.next_after_created,
                        canLoadAfter: !!data?.has_more
                    })

                    if (!data?.has_more) {
                        commit('SET_MESSAGE_PREV_VALUE', { chat_uid, value: '' })
                    }

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    async getInitialChatMessages({ dispatch, commit, state }, payload = {}) {
        const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
        const useUnreadHistory = payload.useUnreadHistory === true

        if (!chat_uid) {
            return null
        }

        if (
            useUnreadHistory
            && state.chatMessage[chat_uid]?.value?.length
            && state.chatHistoryStateByChat?.[chat_uid]?.active === true
            && state.chatHistoryStateByChat?.[chat_uid]?.dividerCreated
        ) {
            return state.chatMessage[chat_uid]
        }

        if (useUnreadHistory) {
            const unreadData = await dispatch('getUnreadEntryMessages', {
                chat_uid,
                page_size: payload.page_size || 20
            })

            if (unreadData?.history_mode && Array.isArray(unreadData.results) && unreadData.results.length) {
                return unreadData
            }
        }

        // Фолбэк: если unread-history не применим, работаем старым потоком списка.
        commit('CLEAR_CHAT_HISTORY', chat_uid)
        return dispatch('getMessage', { chat_uid, refresh: true })
    },
    getMessageScroll({ commit, state }, payload = {}) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
            if (!chat_uid || !state.chatMessage[chat_uid]) {
                resolve(null)
                return
            }

            let url = state.chatMessage[chat_uid].next,
                params = {}

            url.split('&').forEach(item => {
                const arr = item.split('=')
                params[arr[0]] = arr[1]
            })

            if(params.slice_count)
                delete params.slice_count

            if(state.chatMessage[chat_uid].slice_count) {
                params['slice_count'] = state.chatMessage[chat_uid].slice_count
            }

            axios.get(`/chat/message/list/`, {
                params
            })
                .then(({ data }) => {
                    if (data.results.length) {
                        commit('SET_MESSAGE_NEXT', { chat_uid, data })
                        commit('CONCAT_CHAT_MESSAGE', { chat_uid, data })
                    }
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    getCurrentChat({ commit }, id) {
        return new Promise((resolve, reject) => {
            cancelSourceSilently(activeChatDetailCancelSource)
            cancelSourceSilently(activeChatMessageCancelSource)
            cancelSourceSilently(activeChatPinCancelSource)

            const requestId = activeChatDetailRequestId + 1
            activeChatDetailRequestId = requestId

            const source = axiosMain.CancelToken.source()
            activeChatDetailCancelSource = source

            axios.get(`/chat/${id}/detail/`, {
                cancelToken: source.token
            })
                .then(({ data }) => {
                    if (data && requestId === activeChatDetailRequestId) {
                        // Предзаполняем history-state сразу на detail,
                        // чтобы при открытии чата сохранить точку входа для divider и unread-flow.
                        if (Number(data?.new_message_count || 0) > 0) {
                            commit('SET_CHAT_HISTORY_STATE', {
                                chat_uid: data.chat_uid,
                                data: {
                                    active: true,
                                    canLoadAfter: false,
                                    unreadCount: data.new_message_count,
                                    unreadMentionCount: data.new_mention_count,
                                    readCursorCreated: data.my_readed_at || null,
                                    dividerCreated: data.my_readed_at || null,
                                    dividerAtStart: !data.my_readed_at && Number(data.new_message_count || 0) > 0,
                                    afterCreated: null
                                }
                            })
                        } else {
                            commit('CLEAR_CHAT_HISTORY', data.chat_uid)
                        }
                        commit('SET_ACTIVE_CHAT', data)
                        commit('SET_CHAT_MESSAGE', data.chat_uid)
                        commit('SET_CHAT_MESSAGE_MODAL', data.chat_uid)
                    }
                    resolve(data)
                })
                .catch((error) => {
                    if (isCancelError(error)) {
                        resolve(null)
                        return
                    }
                    reject(error)
                })
                .finally(() => {
                    if (activeChatDetailCancelSource === source) {
                        activeChatDetailCancelSource = null
                    }
                })
        })
    },
    updateReadProgress({ commit, dispatch }, payload = {}) {
        const chat_uid = payload.chat_uid
        const created = payload.created

        if (!chat_uid || !created) {
            return Promise.resolve(null)
        }

        return axios.post(`/chat/${chat_uid}/message/read_progress/`, {
            created
        }).then(({ data }) => {
            // Бэк здесь источник истины по unread.
            // После ответа не гадаем локально, а применяем точные цифры и синкаем остальные вкладки.
            commit('APPLY_CHAT_READ_PROGRESS', { chat_uid, data })
            ChatEventBus.$emit('chat_member_update_last_message', {
                ...(data || {}),
                chat: data?.chat || chat_uid
            })
            dispatch('getMessageCount')
            return data
        })
    },
    getPrivateChat({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`/chat/private/?user=${id}`)
                .then(({ data }) => {
                    if (data) {
                        // commit('SET_ACTIVE_CHAT', data)
                        // commit('SET_CHAT_MESSAGE', data.chat_uid)
                        // commit('SET_CHAT_MESSAGE_MODAL', data.chat_uid)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    refreshChatDetail({ commit }, chat_uid) {
        if (!chat_uid) return Promise.resolve(null)

        return axios.get(`/chat/${chat_uid}/detail/`)
            .then(({ data }) => {
                if (data?.chat_uid) {
                    commit('UPSERT_CHAT_DETAIL', data)
                }

                return data
            })
    },
    getMessageDownScroll({ commit, state }, payload = {}) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
            if (!chat_uid || !state.chatMessage[chat_uid]) {
                resolve(null)
                return
            }

            axios.get(`/chat/message/list/?${state.chatMessage[chat_uid].prev}`)
                .then(({ data }) => {
                    if (data.results.length) {
                        commit('SET_MESSAGE_PREV', { chat_uid, data })
                        commit('PUSH_CHAT_MESSAGE', { chat_uid, data })
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })

        })
    },
    searchMessages({ commit, state }, payload) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
            if (!chat_uid) {
                resolve(null)
                return
            }

            axios.get(`/chat/message/list/`, {
                params: {
                    message: payload.message_uid,
                    page_size: 15,
                    chat: chat_uid
                }
            })
                .then(({ data }) => {
                    // Это legacy-хвост.
                    // Переход из поиска пока еще грубо чистит unread целиком,
                    // но в идеале его тоже надо перевести на read_progress.
                    commit('clearMessageCount', chat_uid)
                    if (data.results.length)
                        commit('SET_SEARCH_CHAT_MESSAGE', { chat_uid, data })

                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getPinMessage({ commit, state }, payload = {}) {
        const { page_size = 15, page = 1 } = payload
        const chat_uid = payload.chat_uid || state.activeChat?.chat_uid

        if (!chat_uid) return Promise.resolve(null)

        if (state.pinMessage[chat_uid] && state.pinMessage[chat_uid].length)
            return Promise.resolve(state.pinMessage[chat_uid])
        else {
            return new Promise((resolve, reject) => {
                cancelSourceSilently(activeChatPinCancelSource)
                const source = axiosMain.CancelToken.source()
                activeChatPinCancelSource = source

                axios.get('/chat/pinned_message/list/', {
                    params: {
                        page_size,
                        page,
                        chat: chat_uid
                    },
                    cancelToken: source.token
                })
                    .then(({ data }) => {
                        if (data.results) {
                            commit('PIN_GENERATE', { chat_uid, data })
                        }
                        resolve(data)
                    })
                    .catch((error) => {
                        if (isCancelError(error)) {
                            resolve(null)
                            return
                        }
                        reject(error)
                    })
                    .finally(() => {
                        if (activeChatPinCancelSource === source) {
                            activeChatPinCancelSource = null
                        }
                    })
            })
        }
    },
    getPinMessageScroll({ commit, state }, payload = {}) {
        return new Promise((resolve, reject) => {
            const chat_uid = payload.chat_uid || state.activeChat?.chat_uid
            if (!chat_uid || !state.pinMessage[chat_uid]?.next) {
                resolve(null)
                return
            }

            const next = state.pinMessage[chat_uid].next.split('?')[1]
            axios.get(`/chat/pinned_message/list/?${next}`)
                .then(({ data }) => {
                    commit('PIN_PUSH', { chat_uid, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    search({ commit }, payload) {
        return new Promise((resolve, reject) => {
            axios.get(`/chat/search/?text=${payload.val}`, {
                params: {
                    page: payload.page,
                    page_size: 10
                }
            })
                .then(({ data }) => {
                    if (data.results.length) {
                        commit('CONCAT_ADD_MEMBERS_CLEAR')
                        commit('CONCAT_SEARCH_RESULT', data.results)


                        resolve(data)
                    }
                })
                .catch((error) => { reject(error) })
        })
    },
    memberSearch({ commit, state }, payload) {
        return new Promise((resolve, reject) => {
            axios.get(`/chat/search/?text=${payload.value}`, {
                params: {
                    chat: payload.id,
                    page: payload.page,
                    users_only: true,
                }
            })
                .then(({ data }) => {
                    if (data.results.length) {

                        commit('CONTACT_GROUP_CONTACTS', data.results)
                        // commit('CONCAT_ADD_MEMBERS', users)
                        resolve(data)
                    } else
                        resolve(false)
                })
                .catch((error) => { reject(error) })
        })
    },
    async updateSMT({state, commit}, template) {
        if(!template.id)
            return
        const index = state.supportMessageTemplates.findIndex(item => item.id === template.id)
        if(index === -1)
            return
        commit('UPDATE_SUPPORT_MESSAGE_TEMPLATE', {index, template})
    }
}
