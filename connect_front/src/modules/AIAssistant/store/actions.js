import axios from '@/config/axios'
import { v1 as uuidv1 } from 'uuid'
import moment from 'moment'
import { i18n } from '@/config/i18n-setup'

const PENDING_MESSAGE_STATUSES = ['queued', 'processing_classify', 'processing_intent', 'generating_reply']

export default {
    getChat({ commit }) {
        return new Promise((resolve, reject) => {
            commit('SET_CHAT_LOADING', true)
            axios.get('/chat_ai/chats/')
                .then(({ data }) => {
                    if (data) {
                        const activeChat = data.results[0] || null
                        commit('SET_CHAT_LIST', data)
                        commit('SET_ACTIVE_CHAT', activeChat)
                        if (activeChat?.id)
                            commit('CHAT_INIT_MESSAGES', activeChat.id)
                    }
                    commit('SET_CHAT_LOADING', false)
                    resolve(data)
                })
                .catch(error => {
                    commit('SET_CHAT_LOADING', false)
                    reject(error)
                })
        })
    },

    getMessage({ commit, state }, paramsOverride = {}) {
        return new Promise((resolve, reject) => {
            if (!state.activeChat?.id || !state.chatMessages?.[state.activeChat.id]) {
                resolve(null)
                return
            }

            const currentChatState = state.chatMessages[state.activeChat.id]
            const params = {
                page: currentChatState.page,
                page_size: 15,
                chat: state.activeChat.id,
                ...paramsOverride
            }

            if (currentChatState.slice_count > 0 && params.slice_count === undefined)
                params.slice_count = currentChatState.slice_count

            axios.get('/chat_ai/messages/', { params })
                .then(({ data }) => {
                    if (data)
                        commit('MESSAGE_SCROLL', { chatId: state.activeChat.id, data })
                    resolve(data)
                })
                .catch(error => {
                    commit('SET_CHAT_LOADING', false)
                    reject(error)
                })
        })
    },

    fetchMessageById({ commit, state }, { messageId, chatId = state.activeChat?.id } = {}) {
        return new Promise((resolve, reject) => {
            if (!messageId || !chatId) {
                resolve(null)
                return
            }

            axios.get(`/chat_ai/messages/${messageId}/`)
                .then(({ data }) => {
                    if (data) {
                        commit('UPSERT_MESSAGE', {
                            chatId,
                            message: data
                        })
                    }
                    resolve(data)
                })
                .catch(error => {
                    const statusCode = error?.response?.status
                    if (statusCode === 404 || statusCode === 403) {
                        commit('REMOVE_MESSAGE', { chatId, messageId })
                    }
                    reject(error)
                })
        })
    },

    reconcilePendingMessages({ dispatch, state }, { chatId = state.activeChat?.id } = {}) {
        return new Promise((resolve) => {
            const chatState = chatId ? state.chatMessages?.[chatId] : null
            if (!chatState?.results?.length) {
                resolve([])
                return
            }

            const pendingIds = Array.from(new Set(
                chatState.results
                    .filter(message => message?.is_bot && message?.id)
                    .filter(message => ['accepted', 'stage', 'streaming'].includes(message.stream_state)
                        || PENDING_MESSAGE_STATUSES.includes(message.status))
                    .map(message => message.id)
            ))

            if (!pendingIds.length) {
                resolve([])
                return
            }

            Promise.allSettled(
                pendingIds.map(messageId => dispatch('fetchMessageById', { chatId, messageId }))
            ).then(results => resolve(results))
        })
    },

    sendMessage({ commit, state, rootState }, { text, addNewMessage = () => {}, clearInput = () => {} }) {
        return new Promise((resolve, reject) => {
            const chatId = state.activeChat?.id
            const clientMessageId = uuidv1()

            commit('ADD_NEW_MESSAGE', {
                chatId,
                message: {
                    id: clientMessageId,
                    text,
                    is_bot: false,
                    is_intent: false,
                    created_at: moment().format(),
                    reply_to: null,
                    message_author: rootState.user.user,
                    status: 'queued',
                    is_local_only: true
                }
            })

            addNewMessage()
            clearInput()

            axios.post('/chat_ai/messages/', {
                text,
                chat: chatId
            })
                .then(({ data }) => {
                    if (data?.user_message) {
                        commit('REPLACE_MESSAGE', {
                            chatId,
                            targetId: clientMessageId,
                            message: data.user_message
                        })
                    }

                    if (data?.assistant_message) {
                        commit('UPSERT_MESSAGE', {
                            chatId,
                            message: {
                                ...data.assistant_message,
                                stream_state: 'accepted',
                                stream_stage_text: '',
                                stream_error: null
                            }
                        })
                    }

                    resolve(data)
                })
                .catch(error => {
                    commit('ADD_NEW_MESSAGE', {
                        chatId,
                        message: {
                            text: i18n.t('ai_assistant.unexpected_error'),
                            is_error: true,
                            is_bot: true,
                            is_intent: false,
                            id: uuidv1(),
                            created_at: moment().format(),
                            reply_to: null,
                            status: 'failed'
                        }
                    })
                    reject(error)
                })
        })
    }
}
