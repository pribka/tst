import Vue from 'vue'

function ensureChatState(state, chatId) {
    if (!chatId)
        return null

    if (!state.chatMessages[chatId]) {
        Vue.set(state.chatMessages, chatId, {
            page: 1,
            next: true,
            results: [],
            count: 0,
            slice_count: 0,
            empty: false,
            aiLoading: false
        })
    }

    return state.chatMessages[chatId]
}

function mergeMessage(oldMessage = {}, patch = {}) {
    return {
        ...oldMessage,
        ...patch
    }
}

function shouldTrackSliceCount(message = {}) {
    return !message?.is_bot
}

function getSliceCountIncrement(message = {}) {
    return shouldTrackSliceCount(message) ? 2 : 0
}

function normalizeServerMessage(message = {}, currentMessage = {}) {
    if (!message || message.stream_state !== undefined)
        return message

    if (message.status === 'done') {
        return mergeMessage(message, {
            stream_state: 'done',
            stream_stage: null,
            stream_stage_text: '',
            stream_error: null,
            is_error: false
        })
    }

    if (message.status === 'failed') {
        return mergeMessage(message, {
            stream_state: 'error',
            stream_stage: null,
            stream_stage_text: '',
            stream_error: currentMessage.stream_error || message.text || null,
            is_error: true
        })
    }

    if (['queued', 'processing_classify', 'processing_intent', 'generating_reply'].includes(message.status)) {
        return mergeMessage(message, {
            stream_state: currentMessage.stream_state || 'accepted',
            stream_stage: currentMessage.stream_stage || null,
            stream_stage_text: currentMessage.stream_stage_text || '',
            stream_error: null
        })
    }

    return message
}

export default {
    RESET_CHAT_MESSAGES(state, chatId) {
        if (!chatId)
            return

        Vue.set(state.chatMessages, chatId, {
            page: 1,
            next: true,
            results: [],
            count: 0,
            slice_count: 0,
            empty: false,
            aiLoading: false
        })
    },

    SET_CHAT_LIST(state, data) {
        state.chatList = data
    },

    SET_ACTIVE_CHAT(state, chat) {
        state.activeChat = chat
    },

    SET_CHAT_LOADING(state, loading) {
        state.chatLoading = loading
    },

    CLEAR_ACTIVE_CHAT(state) {
        if (!state.activeChat?.id)
            return

        Vue.set(state.chatMessages, state.activeChat.id, {
            page: 1,
            next: true,
            results: [],
            count: 0,
            slice_count: 0,
            empty: true,
            aiLoading: false
        })
    },

    CHAT_INIT_MESSAGES(state, chatId) {
        ensureChatState(state, chatId)
    },

    CHANGE_MESSAGES_FILED(state, { field, value }) {
        if (!state.activeChat?.id)
            return

        const chatState = ensureChatState(state, state.activeChat.id)
        Vue.set(chatState, field, value)
    },

    MESSAGE_SCROLL(state, { chatId, data }) {
        const chatState = ensureChatState(state, chatId)
        chatState.results = data.results.concat(chatState.results)
        chatState.count = data.count
        chatState.next = data.next

        if (chatState.page === 1 && !data.results.length) {
            chatState.empty = true
        } else {
            chatState.page += 1
        }
    },

    ADD_NEW_MESSAGE(state, { message, chatId }) {
        const chatState = ensureChatState(state, chatId)
        if (!chatState)
            return

        const trackedMessage = shouldTrackSliceCount(message)
            ? mergeMessage(message, { slice_count_tracked: true })
            : message

        chatState.empty = false
        chatState.count += 1
        chatState.slice_count += getSliceCountIncrement(trackedMessage)
        chatState.results.push(trackedMessage)
    },

    UPSERT_MESSAGE(state, { chatId, message }) {
        const chatState = ensureChatState(state, chatId)
        if (!chatState || !message?.id)
            return

        const index = chatState.results.findIndex(item => item.id === message.id)
        if (index !== -1) {
            const currentMessage = chatState.results[index] || {}
            const normalizedMessage = normalizeServerMessage(message, currentMessage)
            Vue.set(chatState.results, index, mergeMessage(currentMessage, normalizedMessage))
        } else {
            const normalizedMessage = normalizeServerMessage(message)
            chatState.empty = false
            chatState.count += 1
            chatState.results.push(normalizedMessage)
        }
    },

    REPLACE_MESSAGE(state, { chatId, targetId, message }) {
        const chatState = ensureChatState(state, chatId)
        if (!chatState || !message)
            return

        const index = chatState.results.findIndex(item => item.id === targetId)
        if (index !== -1) {
            Vue.set(chatState.results, index, message)
        } else {
            chatState.results.push(message)
        }
    },

    REMOVE_MESSAGE(state, { chatId, messageId }) {
        const chatState = ensureChatState(state, chatId)
        if (!chatState)
            return

        const index = chatState.results.findIndex(item => item.id === messageId)
        if (index === -1)
            return

        const removedMessage = chatState.results[index]
        chatState.results.splice(index, 1)
        chatState.count = Math.max(0, chatState.count - 1)
        chatState.slice_count = Math.max(0, chatState.slice_count - getSliceCountIncrement(removedMessage))
        chatState.empty = chatState.results.length === 0
    },

    APPLY_AI_EVENT(state, payload) {
        const chatId = payload?.chat_id
        const messageId = payload?.assistant_message_id
        const chatState = ensureChatState(state, chatId)
        if (!chatState || !messageId)
            return

        let index = chatState.results.findIndex(item => item.id === messageId)
        if (index === -1) {
            const baseMessage = payload?.message || {
                id: messageId,
                chat: chatId,
                is_bot: true,
                text: '',
                intents: [],
                created_at: new Date().toISOString(),
                status: 'queued'
            }
            chatState.empty = false
            chatState.count += 1
            chatState.results.push(baseMessage)
            index = chatState.results.length - 1
        }

        const current = chatState.results[index] || {}
        let nextMessage = current

        if (payload?.message) {
            nextMessage = mergeMessage(nextMessage, payload.message)
        }

        if (payload.type === 'accepted') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: 'accepted',
                stream_stage: null,
                stream_stage_text: '',
                stream_error: null
            })
        }

        if (payload.type === 'stage') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: 'stage',
                stream_stage: payload.stage || null,
                stream_stage_text: payload.text || '',
                stream_error: null
            })
        }

        if (payload.type === 'delta') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: 'streaming',
                stream_stage: null,
                stream_stage_text: '',
                text: `${nextMessage.text || ''}${payload.text || ''}`,
                stream_error: null
            })
        }

        if (payload.type === 'intents_ready') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: nextMessage.stream_state || 'stage',
                stream_error: null
            })
        }

        if (payload.type === 'done') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: 'done',
                stream_stage: null,
                stream_stage_text: '',
                stream_error: null
            })
        }

        if (payload.type === 'error') {
            nextMessage = mergeMessage(nextMessage, {
                stream_state: 'error',
                stream_stage: null,
                stream_stage_text: '',
                stream_error: payload.error || payload.text || null,
                is_error: true,
                text: payload.text || nextMessage.text || ''
            })
        }

        Vue.set(chatState.results, index, nextMessage)
    },

    SET_MESSAGE_FIELD_VALUE(state, { messageIndex, widgetKey, value, intentIndex }) {
        if (state.chatMessages?.[state.activeChat.id]?.results?.[messageIndex]?.intents?.[intentIndex]?.resolutions?.[widgetKey]) {
            Vue.set(state.chatMessages[state.activeChat.id].results[messageIndex].intents[intentIndex].resolutions[widgetKey], 'value', value)
        }
    },

    SET_MESSAGE_METADATA(state, { messageIndex, widgetKey, value, intentIndex }) {
        if (state.chatMessages?.[state.activeChat.id]?.results?.[messageIndex]?.intents?.[intentIndex]?.resolutions?.[widgetKey]) {
            Vue.set(state.chatMessages[state.activeChat.id].results[messageIndex].intents[intentIndex].resolutions[widgetKey], 'metadata', value)
        }
    },

    SET_MESSAGE_RELATED(state, { messageIndex, intentIndex, value }) {
        if (state.chatMessages?.[state.activeChat.id]?.results?.[messageIndex]?.intents?.[intentIndex]) {
            Vue.set(state.chatMessages[state.activeChat.id].results[messageIndex].intents[intentIndex], 'related_object', value)
        }
    },

    SET_MESSAGE_RESOLUTION(state, { messageIndex, intentIndex, value }) {
        if (state.chatMessages?.[state.activeChat.id]?.results?.[messageIndex]?.intents?.[intentIndex]) {
            Vue.set(state.chatMessages[state.activeChat.id].results[messageIndex].intents[intentIndex], 'resolutions', value)
        }
    },

    DELETE_INTENTS(state, { messageIndex, intentIndex }) {
        if (state.chatMessages?.[state.activeChat.id]?.results?.[messageIndex]?.intents?.[intentIndex]) {
            Vue.set(state.chatMessages[state.activeChat.id].results[messageIndex].intents, intentIndex, {
                id: Date.now(),
                is_active: false
            })
        }
    }
}
