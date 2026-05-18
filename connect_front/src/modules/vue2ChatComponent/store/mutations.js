import Vue from 'vue'
import { orderBy } from 'lodash'
import ChatEventBus from '../utils/ChatEventBus'
import store from '@/store'
import chatSync from '@/utils/chatSync'

function toBoolean(value) {
    if (typeof value === 'boolean') return value
    if (typeof value === 'string') {
        const normalized = value.trim().toLowerCase()
        if (normalized === 'true') return true
        if (normalized === 'false') return false
    }

    return Boolean(value)
}

function applyDeletedState(target) {
    if (!target || typeof target !== 'object') return false

    let changed = false

    if (target.is_deleted !== true) {
        Vue.set(target, 'is_deleted', true)
        changed = true
    }
    if (target.text !== '') {
        Vue.set(target, 'text', '')
        changed = true
    }
    if (!Array.isArray(target.attachments) || target.attachments.length) {
        Vue.set(target, 'attachments', [])
        changed = true
    }
    if (target.share !== null) {
        Vue.set(target, 'share', null)
        changed = true
    }

    return changed
}

function markDeletedMessageByUid(target, messageUid) {
    if (!target || typeof target !== 'object' || !messageUid) return false

    let changed = false

    if (target.message_uid === messageUid) {
        changed = applyDeletedState(target) || changed
    }

    if (target.message_forwarded && typeof target.message_forwarded === 'object') {
        changed = markDeletedMessageByUid(target.message_forwarded, messageUid) || changed
    }

    if (target.message_reply && typeof target.message_reply === 'object') {
        changed = markDeletedMessageByUid(target.message_reply, messageUid) || changed
    }

    return changed
}

function updateTaskShareById(target, task) {
    if (!target || typeof target !== 'object' || !task?.id) return false

    let changed = false
    const targetShare = target.share

    if (
        targetShare
        && targetShare.type === 'tasks.TaskModel'
        && String(targetShare.id) === String(task.id)
    ) {
        Vue.set(target, 'share', {
            ...targetShare,
            ...task
        })
        changed = true
    }

    if (target.message_forwarded && typeof target.message_forwarded === 'object') {
        changed = updateTaskShareById(target.message_forwarded, task) || changed
    }

    if (target.message_reply && typeof target.message_reply === 'object') {
        changed = updateTaskShareById(target.message_reply, task) || changed
    }

    return changed
}

function normalizeComparableText(text) {
    return String(text || '').trim()
}

function normalizeComparableAttachments(attachments) {
    if (!Array.isArray(attachments)) return []

    return attachments
        .map(item => String(item?.id || item?.iid || item?.uid || item?.file?.id || item?.file?.iid || item?.file?.uid || item?.file?.path || ''))
        .filter(Boolean)
        .sort()
}

function isSameAttachmentSet(left, right) {
    if (left.length !== right.length) return false
    return left.every((value, index) => value === right[index])
}

function isSameReply(left, right) {
    const leftUid = left?.message_uid || left?.id || null
    const rightUid = right?.message_uid || right?.id || null

    if (!leftUid && !rightUid) return true

    return String(leftUid) === String(rightUid)
}

function findOptimisticMessageIndex(list, message) {
    if (!Array.isArray(list) || !list.length || !message) return -1

    const incomingClientUid = String(message.client_uid || '')
    const incomingAuthorId = String(message?.message_author?.id || '')
    const incomingChatUid = String(message?.chat_uid || '')

    if (incomingClientUid) {
        const directIndex = list.findIndex(item => {
            if (item?.is_optimistic !== true) return false
            if (String(item?.client_uid || '') !== incomingClientUid) return false
            if (String(item?.chat_uid || '') !== incomingChatUid) return false
            if (String(item?.message_author?.id || '') !== incomingAuthorId) return false

            return true
        })
        if (directIndex !== -1) return directIndex
    }

    const incomingText = normalizeComparableText(message?.text)
    const incomingAttachments = normalizeComparableAttachments(message?.attachments)

    return list.findIndex(item => {
        if (item?.is_optimistic !== true) return false
        if (String(item?.chat_uid || '') !== incomingChatUid) return false
        if (String(item?.message_author?.id || '') !== incomingAuthorId) return false
        if (normalizeComparableText(item?.text) !== incomingText) return false
        if (!isSameReply(item?.message_reply, message?.message_reply)) return false

        const itemAttachments = normalizeComparableAttachments(item?.attachments)
        return isSameAttachmentSet(itemAttachments, incomingAttachments)
    })
}

function remapMessageChat(message, chatUid) {
    return {
        ...message,
        chat: chatUid,
        chat_uid: chatUid
    }
}

function messageExistsInList(list, message) {
    if (!Array.isArray(list) || !message) return false

    return list.some(item => {
        if (message.client_uid && item.client_uid) {
            return String(item.client_uid) === String(message.client_uid)
        }

        if (message.message_uid && item.message_uid) {
            return String(item.message_uid) === String(message.message_uid)
        }

        return false
    })
}

function mergeOpenMessagesWithOptimistic(currentList, incomingList, chatUid) {
    const result = Array.isArray(incomingList)
        ? incomingList.map(message => remapMessageChat(message, chatUid))
        : []
    const current = Array.isArray(currentList) ? currentList : []
    const matchedOptimisticIndexes = new Set()

    result.forEach(message => {
        const optimisticIndex = findOptimisticMessageIndex(current, message)
        if (optimisticIndex !== -1) {
            matchedOptimisticIndexes.add(optimisticIndex)
        }
    })

    current.forEach((message, index) => {
        if (message?.is_optimistic !== true) return
        if (matchedOptimisticIndexes.has(index)) return

        const remappedMessage = remapMessageChat(message, chatUid)
        if (!messageExistsInList(result, remappedMessage)) {
            result.push(remappedMessage)
        }
    })

    return result
}

export default {
    SET_CHAT_SEARCH_MORE_SCROLL_DONE(state, { key, value }) {
        if (!state.chatSearchMoreScrollDoneByKey) Vue.set(state, 'chatSearchMoreScrollDoneByKey', {})
        if (value) Vue.set(state.chatSearchMoreScrollDoneByKey, key, true)
        else if (state.chatSearchMoreScrollDoneByKey?.[key]) Vue.delete(state.chatSearchMoreScrollDoneByKey, key)
    },

    CLEAR_CHAT_SEARCH_MORE_SCROLL_DONE(state, key) {
        if (state.chatSearchMoreScrollDoneByKey?.[key]) Vue.delete(state.chatSearchMoreScrollDoneByKey, key)
    },
    SET_CHAT_SEARCH_TEXT(state, { chat_uid, text }) {
        if (!chat_uid) return
        if (!state.chatSearchTextByChat) Vue.set(state, 'chatSearchTextByChat', {})

        const prev = (state.chatSearchTextByChat?.[chat_uid] || '').toString().trim()
        const next = (text || '').toString()
        const nextTrim = next.trim()

        if (prev !== nextTrim) {
            const map = state.chatSearchMoreScrollDoneByKey
            if (map) {
                Object.keys(map).forEach(k => {
                    if (k.indexOf(`${chat_uid}|`) === 0) Vue.delete(map, k)
                })
            }
        }

        if (nextTrim) Vue.set(state.chatSearchTextByChat, chat_uid, nextTrim)
        else Vue.delete(state.chatSearchTextByChat, chat_uid)
    },

    CLEAR_CHAT_SEARCH(state, chat_uid) {
        if (!chat_uid) return
        if (state.chatSearchTextByChat?.[chat_uid]) Vue.delete(state.chatSearchTextByChat, chat_uid)
        if (state.chatSearchMessageByChat?.[chat_uid]) Vue.delete(state.chatSearchMessageByChat, chat_uid)
        const map = state.chatSearchMoreScrollDoneByKey
        if (map) {
            Object.keys(map).forEach(k => {
                if (k.indexOf(`${chat_uid}|`) === 0) Vue.delete(map, k)
            })
        }
    },
    SET_CHAT_HISTORY_STATE(state, { chat_uid, data }) {
        if (!chat_uid) return

        const current = state.chatHistoryStateByChat?.[chat_uid] || {}
        const currentDividerActive = current.active === true && current.dividerCreated
        Vue.set(state.chatHistoryStateByChat, chat_uid, {
            ...current,
            // Здесь храним два разных якоря.
            // readCursorCreated - живой прогресс чтения.
            // dividerCreated/dividerAtStart - фиксированная граница, где надо рисовать линию входа.
            active: data?.active !== false,
            canLoadAfter: !!data?.canLoadAfter,
            unreadCount: Number(data?.unreadCount || 0),
            unreadMentionCount: Number(data?.unreadMentionCount || 0),
            readCursorCreated: data?.readCursorCreated || current.readCursorCreated || null,
            dividerCreated: currentDividerActive || data?.dividerCreated || data?.readCursorCreated || current.readCursorCreated || null,
            dividerAtStart: data?.dividerAtStart === true || (current.dividerAtStart === true && !data?.dividerCreated),
            afterCreated: data?.afterCreated || current.afterCreated || null
        })
    },
    UPDATE_CHAT_HISTORY_CURSOR(state, { chat_uid, afterCreated, canLoadAfter }) {
        if (!chat_uid || !state.chatHistoryStateByChat?.[chat_uid]) return

        // Курсор нижней догрузки history-хвоста.
        const nextState = {
            ...state.chatHistoryStateByChat[chat_uid],
            afterCreated: afterCreated || state.chatHistoryStateByChat[chat_uid].afterCreated || null
        }

        if (typeof canLoadAfter === 'boolean') {
            nextState.canLoadAfter = canLoadAfter
        }

        Vue.set(state.chatHistoryStateByChat, chat_uid, nextState)
    },
    REGISTER_LOCAL_UNREAD_MESSAGE(state, { chat_uid, message }) {
        if (!chat_uid || !message) return

        const list = state.chatMessage[chat_uid]?.value
        if (!Array.isArray(list) || !list.length) return

        const current = state.chatHistoryStateByChat?.[chat_uid] || {}
        const lastLoadedCreated = list[list.length - 1]?.created || null
        const dividerCreated = current.active === true && current.dividerCreated
            ? current.dividerCreated
            : lastLoadedCreated

        if (!dividerCreated) return

        const myId = store.state.user?.user?.id
        const hasMention = Array.isArray(message.mentions)
            && message.mentions.some(id => String(id) === String(myId))

        Vue.set(state.chatHistoryStateByChat, chat_uid, {
            ...current,
            active: true,
            canLoadAfter: false,
            unreadCount: Number(current.active === true ? current.unreadCount || 0 : 0) + 1,
            unreadMentionCount: Number(current.active === true ? current.unreadMentionCount || 0 : 0) + (hasMention ? 1 : 0),
            readCursorCreated: current.readCursorCreated || dividerCreated,
            dividerCreated,
            dividerAtStart: false,
            afterCreated: current.afterCreated || null,
            local: true
        })
    },
    DEACTIVATE_CHAT_HISTORY(state, chat_uid) {
        if (!chat_uid || !state.chatHistoryStateByChat?.[chat_uid]) return

        // Переключение обратно в стандартный режим отображения.
        Vue.set(state.chatHistoryStateByChat, chat_uid, {
            ...state.chatHistoryStateByChat[chat_uid],
            active: false,
            canLoadAfter: false
        })
    },
    CLEAR_CHAT_HISTORY(state, chat_uid) {
        if (!chat_uid) return
        if (state.chatHistoryStateByChat?.[chat_uid]) {
            // Полный сброс временного unread-history состояния для конкретного чата.
            Vue.delete(state.chatHistoryStateByChat, chat_uid)
        }
    },
    APPLY_CHAT_READ_PROGRESS(state, { chat_uid, data }) {
        if (!chat_uid || !data) return

        const unreadCount = Number(data.unread_count || 0)
        const unreadMentionCount = Number(data.unread_mention_count || 0)
        const readCreated = data.my_readed_at || data.created || null

        const chatIndex = state.chatList.findIndex(el => el.chat_uid === chat_uid)
        if (chatIndex !== -1) {
            Vue.set(state.chatList[chatIndex], 'new_message_count', unreadCount)
            Vue.set(state.chatList[chatIndex], 'new_mention_count', unreadMentionCount)
            Vue.set(state.chatList[chatIndex], 'my_readed_at', readCreated)
        }

        if (state.activeChat?.chat_uid === chat_uid) {
            Vue.set(state.activeChat, 'new_message_count', unreadCount)
            Vue.set(state.activeChat, 'new_mention_count', unreadMentionCount)
            Vue.set(state.activeChat, 'my_readed_at', readCreated)
        }

        if (unreadCount <= 0) {
            if (state.chatHistoryStateByChat?.[chat_uid]) {
                Vue.set(state.chatHistoryStateByChat, chat_uid, {
                    ...state.chatHistoryStateByChat[chat_uid],
                    // Когда unread закончился, history-режим выключаем,
                    // но divider оставляем, чтобы линия "Новые сообщения" не пропала в текущей сессии.
                    active: false,
                    canLoadAfter: false,
                    unreadCount: 0,
                    unreadMentionCount: 0,
                    readCursorCreated: readCreated || state.chatHistoryStateByChat[chat_uid].readCursorCreated || null,
                    dividerCreated: state.chatHistoryStateByChat[chat_uid].dividerCreated
                        || state.chatHistoryStateByChat[chat_uid].readCursorCreated
                        || readCreated
                        || null,
                    dividerAtStart: state.chatHistoryStateByChat[chat_uid].dividerAtStart === true,
                })
            }
            return
        }

        if (state.chatHistoryStateByChat?.[chat_uid]) {
            Vue.set(state.chatHistoryStateByChat, chat_uid, {
                ...state.chatHistoryStateByChat[chat_uid],
                active: true,
                unreadCount,
                unreadMentionCount,
                readCursorCreated: readCreated || state.chatHistoryStateByChat[chat_uid].readCursorCreated || null,
                dividerCreated: state.chatHistoryStateByChat[chat_uid].dividerCreated
                    || state.chatHistoryStateByChat[chat_uid].readCursorCreated
                    || readCreated
                    || null,
                dividerAtStart: state.chatHistoryStateByChat[chat_uid].dividerAtStart === true,
            })
        }
    },

    SET_CHAT_SEARCH_MESSAGES(state, { chat_uid, data, query, page_size = 15 }) {
        const results = Array.isArray(data?.results) ? data.results : []

        if (!state.chatSearchMessageByChat) Vue.set(state, 'chatSearchMessageByChat', {})
        if (!state.chatSearchMessageByChat[chat_uid]) {
            Vue.set(state.chatSearchMessageByChat, chat_uid, {
                results: [],
                page: 1,
                hasMore: false,
                loading: false,
                query: ''
            })
        }

        const bucket = state.chatSearchMessageByChat[chat_uid]

        bucket.results = results
        bucket.page = 1
        bucket.query = query || ''

        bucket.hasMore = typeof data?.next !== 'undefined'
            ? !!data.next
            : results.length === page_size
    },

    PUSH_CHAT_SEARCH_MESSAGES(state, { chat_uid, data, page, page_size = 15 }) {
        const bucket = state.chatSearchMessageByChat?.[chat_uid]
        if (!bucket) return

        const incoming = Array.isArray(data?.results) ? data.results : []
        const old = Array.isArray(bucket.results) ? bucket.results : []

        bucket.results = incoming.concat(old) // старые сверху
        bucket.page = page

        bucket.hasMore = typeof data?.next !== 'undefined'
            ? !!data.next
            : incoming.length === page_size
    },

    SET_CHAT_SEARCH_LOADING(state, { chat_uid, value }) {
        if (!chat_uid) return
        if (!state.chatSearchMessageByChat) Vue.set(state, 'chatSearchMessageByChat', {})

        if (!state.chatSearchMessageByChat[chat_uid]) {
            Vue.set(state.chatSearchMessageByChat, chat_uid, {
                results: [],
                page: 1,
                hasMore: false,
                loading: false,
                query: ''
            })
        }

        Vue.set(state.chatSearchMessageByChat[chat_uid], 'loading', value === true)
    },

    TOGGLE_SEARCH_PANEL(state, payload) {
        const chat_uid = typeof payload === 'string'
            ? payload
            : payload?.chat_uid || state.activeChat?.chat_uid

        if (!chat_uid) return

        if (!state.chatSearchPanelOpen) Vue.set(state, 'chatSearchPanelOpen', {})

        const hasValue = payload && Object.prototype.hasOwnProperty.call(payload, 'value')
        const current = state.chatSearchPanelOpen?.[chat_uid] === true
        const next = hasValue ? payload.value === true : !current

        if (next) Vue.set(state.chatSearchPanelOpen, chat_uid, true)
        else Vue.delete(state.chatSearchPanelOpen, chat_uid)
    },
    UPDATE_MESSAGE_FROM_SOCKET(state, { data }) {
        const mergeReactionsKeepMy = (oldReactions, newReactions) => {
            const old = Array.isArray(oldReactions) ? oldReactions : []
            const fresh = Array.isArray(newReactions) ? newReactions : []

            const oldMap = {}
            old.forEach(r => {
                const id = r?.reaction?.id
                if (id !== undefined) oldMap[id] = r.my_reaction === true
            })

            return fresh.map(r => {
                const id = r?.reaction?.id
                return {
                    ...r,
                    my_reaction: id !== undefined ? oldMap[id] === true : false
                }
            })
        }

        const mergeMessage = (oldMsg, newMsg) => {
            const next = {
                ...oldMsg,
                ...newMsg
            }

            if (newMsg?.reactions) {
                next.reactions = mergeReactionsKeepMy(oldMsg?.reactions, newMsg.reactions)
            }

            return next
        }

        const chatIndex = state.chatList.findIndex(c => c.chat_uid === data.chat_uid)
        if (chatIndex !== -1) {
            const chat = state.chatList[chatIndex]
            const last = chat?.last_message

            if (last?.message_uid === data.message_uid) {
                Vue.set(chat, 'last_message', mergeMessage(last, data))
            }
        }

        for (const chat_uid in state.chatMessage) {
            const bucket = state.chatMessage[chat_uid]
            const list = bucket?.value
            if (!Array.isArray(list) || !list.length) continue

            const idx = list.findIndex(m => m.message_uid === data.message_uid)
            if (idx === -1) continue

            const next = mergeMessage(list[idx], data)
            Vue.set(state.chatMessage[chat_uid].value, idx, next)
        }

        for (const chat_uid in state.pinMessage) {
            const bucket = state.pinMessage[chat_uid]
            const list = bucket?.results
            if (!Array.isArray(list) || !list.length) continue

            const idx = list.findIndex(m => m.message_uid === data.message_uid)
            if (idx === -1) continue

            const next = mergeMessage(list[idx], data)
            Vue.set(state.pinMessage[chat_uid].results, idx, next)
        }
    },
    UPDATE_TASK_SHARE_FROM_SOCKET(state, { task }) {
        if (!task?.id) return

        state.chatList.forEach(chat => {
            if (chat?.last_message) {
                updateTaskShareById(chat.last_message, task)
            }
        })

        for (const chat_uid in state.chatMessage) {
            const list = state.chatMessage[chat_uid]?.value
            if (!Array.isArray(list) || !list.length) continue

            list.forEach(message => {
                updateTaskShareById(message, task)
            })
        }

        for (const chat_uid in state.pinMessage) {
            const list = state.pinMessage[chat_uid]?.results
            if (!Array.isArray(list) || !list.length) continue

            list.forEach(message => {
                updateTaskShareById(message, task)
            })
        }
    },
    CREATE_VIRTUAL_CHAT(state, value) {
        let chat = {
            recipient: value,
            chat_author: value.chat_author,
            chat_uid: value.id,
            is_active: true,
            is_moderator: false,
            is_open: true,
            is_public: false,
            member_count: 2,
            no_create: true,
            color: value.color,
            name: value.full_name
        }

        state.activeChat = chat
        Vue.set(state.message, value.id, {
            text: ''
        })

        Vue.set(state.messageModal, value.id, {
            text: ''
        })
    },

    SET_NEW_CREATED_CHAT(state, { value, user }) {
        let id = value.chat_uid
        const previousActiveChat = state.activeChat
        const virtualIdCandidates = [
            value.recipient?.id,
            previousActiveChat?.no_create ? previousActiveChat.chat_uid : null,
            previousActiveChat?.no_create ? previousActiveChat.recipient?.id : null
        ]
            .map(item => item == null ? '' : String(item))
            .filter(Boolean)
        const virtualId = virtualIdCandidates.find(item => state.chatMessage[item])



        if (value.recipient) {
            Vue.set(state.message, id, {
                text: state.message[value.recipient.id]?.text ?
                    state.message[value.recipient.id]?.text : ''
            })

            Vue.set(state.messageModal, id, {
                text: state.messageModal[value.recipient.id]?.text ?
                    state.messageModal[value.recipient.id]?.text : ''
            })


            let files = state.fileList[value.recipient.id]?.length ? state.fileList[value.recipient.id] : []

            Vue.set(state.fileList, id, files)

            const virtualMessages = virtualId ? state.chatMessage[virtualId] : null
            if (virtualMessages) {
                const realMessages = state.chatMessage[id] || {
                    value: [],
                    status: virtualMessages.status,
                    bottomStatus: virtualMessages.bottomStatus,
                    page: virtualMessages.page || 1
                }
                const realList = Array.isArray(realMessages.value) ? realMessages.value.slice() : []
                const movedList = Array.isArray(virtualMessages.value)
                    ? virtualMessages.value.map(message => remapMessageChat(message, id))
                    : []

                movedList.forEach(message => {
                    const optimisticIndex = findOptimisticMessageIndex(realList, message)
                    if (optimisticIndex !== -1) {
                        Vue.set(realList, optimisticIndex, {
                            ...realList[optimisticIndex],
                            ...message
                        })
                        return
                    }

                    const exists = realList.find(item => {
                        if (message.client_uid && item.client_uid) {
                            return String(item.client_uid) === String(message.client_uid)
                        }

                        return item.message_uid && message.message_uid && String(item.message_uid) === String(message.message_uid)
                    })

                    if (!exists) {
                        realList.push(message)
                    }
                })

                Vue.set(state.chatMessage, id, {
                    ...realMessages,
                    value: realList,
                    slice_count: Math.max(Number(realMessages.slice_count || 0), realList.length)
                })
                Vue.set(state.chatMessage, virtualId, {
                    ...realMessages,
                    value: realList,
                    slice_count: Math.max(Number(realMessages.slice_count || 0), realList.length)
                })
                setTimeout(() => {
                    if (state.activeChat?.chat_uid !== virtualId && state.chatMessage[virtualId]) {
                        Vue.delete(state.chatMessage, virtualId)
                    }
                }, 0)

                if (realList.length) {
                    value = {
                        ...value,
                        last_message: realList[realList.length - 1],
                        last_sent: realList[realList.length - 1].created || value.last_sent
                    }
                }
            }
        }

        if (value.chat_author.id === user.id)
            state.activeChat = value



        if (state.chatList && state.chatList.length > 0) {
            const chatIndex = state.chatList.findIndex(chat => chat.chat_uid === value.chat_uid)
            if (chatIndex !== -1) {
                Vue.set(state.chatList, chatIndex, {
                    ...state.chatList[chatIndex],
                    ...value
                })
            } else {
                state.chatList = state.chatList.concat(value)
            }
            state.chatList = orderBy(state.chatList, ['last_sent'], ['desc'])
        } else {
            state.chatList.push(value)
            state.chatList = orderBy(state.chatList, ['last_sent'], ['desc'])
        }


    },
    incrimentMessageCount(state, {chat_uid, data}) {
        const findIndex = state.chatList.findIndex(el => el.chat_uid === chat_uid)
        if (findIndex !== -1) {
            state.chatList[findIndex].new_message_count++
            if (state.activeChat?.chat_uid === chat_uid) {
                Vue.set(state.activeChat, 'new_message_count', Number(state.activeChat.new_message_count || 0) + 1)
            }

            if(data?.mentions?.length) {
                const find = data.mentions.find(f => f === store.state.user?.user?.id)
                if(find) {
                    state.chatList[findIndex].new_mention_count++
                    if (state.activeChat?.chat_uid === chat_uid) {
                        Vue.set(state.activeChat, 'new_mention_count', Number(state.activeChat.new_mention_count || 0) + 1)
                    }
                }
            }
        }

        this.commit('INCRIMENT_PWA_COUNTER', 'chat')
    },
    clearMessageCount(state, payload) {
        const chat_uid = typeof payload === 'string' ? payload : payload?.chat_uid
        const __fromSync = typeof payload === 'object' ? payload.__fromSync === true : false

        const findIndex = state.chatList.findIndex(el => el.chat_uid === chat_uid)
        if (findIndex === -1) return

        // Это старый blunt-reset unread.
        // Оставлен только для legacy-сценариев вроде search/jump, пока они не переведены на read_progress.
        if (!__fromSync) {
            if (state.chatList[findIndex].new_message_count || state.chatList[findIndex].new_mention_count) {
                this.dispatch('chat/getMessageCount')
            }
            this.commit('REMOVE_PWA_COUNTER', { name: 'chat', value: state.chatList[findIndex].new_message_count })
        }

        state.chatList[findIndex].new_message_count = 0
        state.chatList[findIndex].new_mention_count = 0
        if (state.activeChat?.chat_uid === chat_uid) {
            Vue.set(state.activeChat, 'new_message_count', 0)
            Vue.set(state.activeChat, 'new_mention_count', 0)
        }

        if (!__fromSync) {
            if (state.chatMessage[chat_uid]) {
                let last = state.activeChat.last_message
                if(!last)
                    last = state.chatMessage[chat_uid].value[state.chatMessage[chat_uid].value.length - 1]
            }
            chatSync.chatClear(chat_uid)
        }

        if (state.chatHistoryStateByChat?.[chat_uid]) {
            Vue.delete(state.chatHistoryStateByChat, chat_uid)
        }
    },
    ADD_MESSAGE(state, value) {
        const id = value.chat_uid

        const isActive = state.activeChat && state.activeChat.chat_uid === id

        if (!state.chatMessage[id]) {
            if (!isActive) return

            Vue.set(state.chatMessage, id, {
                value: [value],
                status: false,
                bottomStatus: false,
                page: 1
            })

            if (state.chatMessage[id]) {
                if (state.chatMessage[id].slice_count) {
                    Vue.set(state.chatMessage[id], 'slice_count', state.chatMessage[id].slice_count + 1)
                } else {
                    Vue.set(state.chatMessage[id], 'slice_count', 1)
                }
            }

            ChatEventBus.$emit('newMessageArreaScroll')
            return
        }

        if (!state.chatMessage[id].prev) {
            const optimisticIndex = findOptimisticMessageIndex(state.chatMessage[id].value, value)
            if (optimisticIndex !== -1) {
                Vue.set(state.chatMessage[id].value, optimisticIndex, {
                    ...state.chatMessage[id].value[optimisticIndex],
                    ...value,
                    is_optimistic: false
                })

                if (isActive) {
                    ChatEventBus.$emit('newMessageArreaScroll')
                }
                return
            }

            const find = state.chatMessage[id].value.find(f => f.message_uid === value.message_uid)
            if (!find) {
                state.chatMessage[id].value.push(value)

                if (state.chatMessage[id]) {
                    if (state.chatMessage[id].slice_count) {
                        Vue.set(state.chatMessage[id], 'slice_count', state.chatMessage[id].slice_count + 1)
                    } else {
                        Vue.set(state.chatMessage[id], 'slice_count', 1)
                    }
                }

                if (isActive) {
                    ChatEventBus.$emit('newMessageArreaScroll')
                }
            }
        }
    },
    addLastMessage(state, message) {
        const findIndex = state.chatList.findIndex(el => el.chat_uid === message.chat_uid)
        if (findIndex !== -1) {
            state.chatList[findIndex].last_message = message
        } else {
            if(state.chatList?.length && message?.is_optimistic !== true)
                ChatEventBus.$emit('updateChatList', { reason: 'message' })
        }

        const chatIndex = state.chatList.findIndex(el => el.chat_uid === message.chat_uid)
        if (chatIndex !== -1) {
            state.chatList[chatIndex]['last_sent'] = new Date()
            state.chatList = orderBy(state.chatList, ['last_sent'], ['desc'])
        }
    },
    setScrollToped(state, value) {
        if (state.activeChat)
            state.activeChat.scrolled = value
    },
    ADD_MESSAGE_BY_ID(state, { chat_uid, value }) {
        if (state.chatMessage[chat_uid])
            state.chatMessage[chat_uid].value.push(value)
    },
    CLEAR_INPUT(state, id) {
        Vue.set(state.message, id, {text: ''})
        Vue.set(state.messageModal, id, {text: ''})
    },
    SET_CHAT_DRAFTS(state, drafts) {
        Vue.set(state, 'chatDrafts', drafts || {})
    },
    SET_CHAT_DRAFT(state, { chatUid, draft }) {
        if (!state.chatDrafts) {
            Vue.set(state, 'chatDrafts', {})
        }

        Vue.set(state.chatDrafts, chatUid, draft)
    },
    REMOVE_CHAT_DRAFT(state, chatUid) {
        if (state.chatDrafts?.[chatUid]) {
            Vue.delete(state.chatDrafts, chatUid)
        }
    },
    SET_SEARCH_CHAT_MESSAGE(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid) return

        if (state.activeChat?.chat_uid === chat_uid) {
            state.activeChat.downKey = Math.random() * Math.random()
        }

        let next = '',
            prev = ''

        if (data.next && data.next.length) {
            let nextArray = data.next.split('?')[1].split('&'),
                nextArrayGenerate = []

            nextArray.forEach(item => {
                if (!item.includes("message"))
                    nextArrayGenerate.push(item)
            })
            next = nextArrayGenerate.join('&')
        }
        if (data.previous && data.previous.length) {
            let prevArray = data.previous.split('?')[1].split('&'),
                prevArrayGenerate = []

            prevArray.forEach(item => {
                if (!item.includes("message"))
                    prevArrayGenerate.push(item)
            })
            prev = prevArrayGenerate.join('&')
            state.messageListPrev = true
        } else state.messageListPrev = false

        const chatMessage = {
            value: data.results,
            status: true,
            next,
            prev,
            bottomStatus: true,
            page: 1
        }
        Vue.set(state.chatMessage, chat_uid, chatMessage)
    },
    CHANGE_MEMBER_MODERATE(state, value) {
        const id = state.activeChat.chat_uid
        const index = state.chatMembers[id].results.findIndex(item => item.user.id === value.id)
        if (index !== -1)
            state.chatMembers[id].results[index].is_moderator = value.is_moderator
    },
    RENAME_CHAT(state, { chat_uid, chat_name }) {
        if (!chat_uid) return

        const isActiveChat = state.activeChat?.chat_uid === chat_uid
        if (isActiveChat) {
            Vue.set(state.activeChat, 'name', chat_name)
        }

        const findIndex = state.chatList.findIndex(el => el.chat_uid === chat_uid)
        if (findIndex !== -1) {
            Vue.set(state.chatList[findIndex], 'name', chat_name)
        }
    },
    MESSAGE_SOCKET_REACT(state, { data }) {
        for (const chat_uid in state.chatMessage) {
            if (chat_uid !== data.chat_uid) continue

            const messages = state.chatMessage[chat_uid].value
            const index = messages.findIndex(
                mes => mes.message_uid === data.message_uid
            )
            if (index === -1) return

            const oldReactions = messages[index].reactions || []

            const oldMap = {}
            oldReactions.forEach(r => {
                oldMap[r.reaction.id] = r.my_reaction
            })

            const newReactions = data.reactions.map(r => {
                return {
                    ...r,
                    my_reaction: oldMap[r.reaction.id] === true
                }
            })

            Vue.set(state.chatMessage[chat_uid].value[index], 'reactions', newReactions)
        }
    },
    MESSAGE_CHANGE_REACT(state, { message, reaction, chat_uid }) {
        const index = state.chatMessage[chat_uid].value.findIndex(
            mes => mes.message_uid === message.message_uid
        )

        if (index === -1) return

        const current = state.chatMessage[chat_uid].value[index]
        const reactions = current.reactions || []

        let nextReactions = [...reactions]

        const myIndex = nextReactions.findIndex(r => r.my_reaction)

        if (reaction === null) {
            if (myIndex !== -1) {
                const item = nextReactions[myIndex]

                if (item.users_count > 1) {
                    nextReactions[myIndex] = {
                        ...item,
                        users_count: item.users_count - 1,
                        my_reaction: false
                    }
                } else {
                    nextReactions.splice(myIndex, 1)
                }
            }

            Vue.set(state.chatMessage[chat_uid].value[index], 'reactions', nextReactions)
            return
        }

        // ⬇️ ЕСЛИ МЕНЯЕМ РЕАКЦИЮ — УБИРАЕМ СТАРУЮ МОЮ
        if (myIndex !== -1) {
            const myItem = nextReactions[myIndex]

            if (myItem.reaction.id === reaction.id) {
                Vue.set(state.chatMessage[chat_uid].value[index], 'reactions', nextReactions)
                return
            }

            if (myItem.users_count > 1) {
                nextReactions[myIndex] = {
                    ...myItem,
                    users_count: myItem.users_count - 1,
                    my_reaction: false
                }
            } else {
                nextReactions.splice(myIndex, 1)
            }
        }

        const existIndex = nextReactions.findIndex(
            r => r.reaction.id === reaction.id
        )

        if (existIndex !== -1) {
            const item = nextReactions[existIndex]

            nextReactions[existIndex] = {
                ...item,
                users_count: item.users_count + 1,
                my_reaction: true
            }
        } else {
            nextReactions.push({
                my_reaction: true,
                users_count: 1,
                reaction
            })
        }

        Vue.set(state.chatMessage[chat_uid].value[index], 'reactions', nextReactions)
    },

    PIN_MESSAGE(state, message) {
        // console.log("message pin  ", message)
        if (state.pinMessage[message.chat_uid]) {
            state.pinMessage[message.chat_uid].results.unshift(message)
            state.pinMessage[message.chat_uid].count = state.pinMessage[message.chat_uid].count + 1
        } else {
            const pin = {
                results: [message],
                next: null,
                count: 1
            }
            Vue.set(state.pinMessage, [message.chat_uid], pin)
        }

        const index = state.chatMessage[message.chat_uid].value.findIndex(item => item.id === message.id)
        if (index !== -1)
            state.chatMessage[message.chat_uid].value[index].is_pinned = true
    },
    UNPIN_MESSAGE(state, message) {
        // console.log("message unpin", message)

        if (state.pinMessage[message.chat_uid]) {
            const index = state.pinMessage[message.chat_uid].results.findIndex(pin => pin.id === message.id)
            if (index !== -1)
                Vue.delete(state.pinMessage[message.chat_uid].results, index)

            const pinIndex = state.chatMessage[message.chat_uid].value.findIndex(item => item.id === message.id)
            if (pinIndex !== -1)
                state.chatMessage[message.chat_uid].value[pinIndex].is_pinned = false

            state.pinMessage[message.chat_uid].count = state.pinMessage[message.chat_uid].count - 1
        }
    },

    PIN_GENERATE(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid) return
        Vue.set(state.pinMessage, chat_uid, data)
    },
    PIN_PUSH(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid || !state.pinMessage[chat_uid]) return
        state.pinMessage[chat_uid].results = state.pinMessage[chat_uid].results.concat(data.results)
        state.pinMessage[chat_uid].next = data.next
    },
    UNPIN_ALL(state, {chat_uid}) {
        if (state.pinMessage[chat_uid]) {
            state.pinMessage[chat_uid].results.forEach(pin => {
                const index = state.chatMessage[chat_uid].value.findIndex(item => item.chat_uid === pin.id)
                if (index !== -1)
                    state.chatMessage[chat_uid].value[index].is_pinned = false
            })
        }
        Vue.delete(state.pinMessage, chat_uid)
    },

    setSidebarActiveTab(state, value) {
        state.sidebarActiveTab = value
    },

    CONCAT_SPLICE_MEMBERS(state, value) {
        const index = state.addMembersList.findIndex(item => item.id === value.user.id)
        if (index !== -1)
            state.addMembersList.splice(index, 1)
    },
    CONCAT_ADD_MEMBERS_CLEAR(state) {
        state.addMembersList = []
    },
    CONCAT_ADD_MEMBERS(state, value) {
        state.addMembersList = state.addMembersList.concat(value)
    },
    SET_ADD_MEMBER_POPUP(state, value) {
        state.addMemberPopup = value
    },
    SET_SEARCH_TEXT(state, value) {
        state.searchText = value
    },
    CLEAR_SEARCH_RESULT(state) {
        state.searchResult = []
    },
    CONCAT_SEARCH_RESULT(state, value) {
        state.searchResult = state.searchResult.concat(value)
    },

    SET_SELECT_IMG(state, value) {
        state.selectImage = value
        state.imagePopup = true
    },
    SET_IMAGE_POPUP(state, value) {
        state.imagePopup = value
    },

    TOGGLE_INFO_SIDEBAR(state, value) {
        state.sidebarInfo = value
    },
    TOGGLE_TASKS_SIDEBAR(state, value) {
        state.sidebarTasks = value
    },
    TOGGLE_CREATE_CHAT(state, value) {
        state.createChat = value
    },
    CONCAT_CONTACTS(state, value) {
        state.contactList = state.contactList.concat(value)
    },
    CONTACT_GROUP_CONTACTS(state, value) {
        state.contactsGroup = state.contactsGroup.concat(value)
    },
    SET_SELECTED_CONTACTS(state, value) {
        state.selectedContacts = value
    },
    SET_MODERATE(state, value) {
        state.moderate = value
    },
    CONCAT_CHAT(state, value) {
        let data = value.map(el => {
            return {
                ...el,
                is_moderator: toBoolean(el.is_moderator),
                last_sent: new Date(el.last_sent)
            }
        })

        state.chatList = orderBy(state.chatList.concat(data), ['last_sent'], ['desc'])
    },
    UPSERT_CHAT_DETAIL(state, value) {
        if (!value?.chat_uid) return

        const normalizeChat = chat => ({
            ...chat,
            is_moderator: toBoolean(chat?.is_moderator),
            last_sent: chat?.last_sent ? new Date(chat.last_sent) : null
        })
        const mergeChat = oldChat => {
            const next = normalizeChat({
                ...oldChat,
                ...value
            })

            if (oldChat?.last_message && !value.last_message) {
                next.last_message = oldChat.last_message
            }
            if (oldChat?.last_sent && (!value.last_sent || new Date(oldChat.last_sent) > new Date(value.last_sent))) {
                next.last_sent = oldChat.last_sent
            }

            return next
        }

        const chatIndex = state.chatList.findIndex(chat => chat.chat_uid === value.chat_uid)
        if (chatIndex !== -1) {
            Vue.set(state.chatList, chatIndex, mergeChat(state.chatList[chatIndex]))
        } else {
            state.chatList.push(normalizeChat(value))
        }
        state.chatList = orderBy(state.chatList, ['last_sent'], ['desc'])

        if (state.activeChat?.chat_uid === value.chat_uid) {
            const nextActiveChat = mergeChat(state.activeChat)
            Object.keys(nextActiveChat).forEach(key => {
                Vue.set(state.activeChat, key, nextActiveChat[key])
            })
        }
    },
    CLEAR_CHAT_LIST(state) {
        state.chatListPage = 0
        state.chatList = []
        state.chatListNext = true
    },
    HYDRATE_CHAT_WINDOW_CACHE(state, payload = {}) {
        const normalizeChat = item => ({
            ...item,
            is_moderator: toBoolean(item?.is_moderator),
            last_sent: item?.last_sent ? new Date(item.last_sent) : null
        })

        if (Array.isArray(payload.chatList)) {
            state.chatList = payload.chatList.map(normalizeChat)
        }

        if (typeof payload.chatListPage === 'number') {
            state.chatListPage = payload.chatListPage
        }

        if (typeof payload.chatListNext === 'boolean') {
            state.chatListNext = payload.chatListNext
        }

        if (Array.isArray(payload.contactList)) {
            state.contactList = payload.contactList
        }

        if (typeof payload.contactListPage === 'number') {
            state.contactListPage = payload.contactListPage
        }

        if (typeof payload.contactListNext === 'boolean') {
            state.contactListNext = payload.contactListNext
        }

        if (Array.isArray(payload.helpDeskList)) {
            state.helpDeskList = payload.helpDeskList
        }

        if (typeof payload.helpDeskPage === 'number') {
            state.helpDeskPage = payload.helpDeskPage
        }

        if (typeof payload.helpDeskNext === 'boolean') {
            state.helpDeskNext = payload.helpDeskNext
        }

        if (payload.chatDrafts && typeof payload.chatDrafts === 'object') {
            state.chatDrafts = payload.chatDrafts
        }

        if (typeof payload.sidebarActiveTab === 'number') {
            state.sidebarActiveTab = payload.sidebarActiveTab
        }
    },
    SET_ACTIVE_CHAT(state, value) {
        if (value) {
            Vue.set(value, 'is_moderator', toBoolean(value.is_moderator))
            state.activeChat = value
            const findIndex = state.chatList.findIndex(el => el.chat_uid === value.chat_uid)
            if (findIndex !== -1) {
                Vue.set(state.chatList[findIndex], 'is_moderator', toBoolean(state.chatList[findIndex].is_moderator))
            }
        }
    },
    CLEAR_CHAT(state) {
        state.activeChat = false
    },
    SET_ACTIVE_CHAT_FROM_UID(state, uid) {
        const findIndex = state.chatList.findIndex(el => el.chat_uid === uid)
        if (findIndex !== -1) {
            Vue.set(state.chatList[findIndex], 'is_moderator', toBoolean(state.chatList[findIndex].is_moderator))
            state.activeChat = state.chatList[findIndex]
        }
    },
    SET_UNREAD_MESSAGE_COUNT_BY_CHAT_ID(state, { chatUid, messageCount }) {
        const index = state.chatList.findIndex(chat => chat.chat_uid === chatUid)
        if (index !== -1) {
            const normalizedCount = Number(messageCount || 0)
            Vue.set(state.chatList[index], 'new_message_count', normalizedCount)

            if (normalizedCount <= 0) {
                Vue.set(state.chatList[index], 'new_mention_count', 0)
            }
        }

        if (state.activeChat?.chat_uid === chatUid) {
            const normalizedCount = Number(messageCount || 0)
            Vue.set(state.activeChat, 'new_message_count', normalizedCount)

            if (normalizedCount <= 0) {
                Vue.set(state.activeChat, 'new_mention_count', 0)
            }
        }
    },
    SET_LAST_MESSAGE_BY_CHAT_ID(state, { chatUid, lastMessage }) {
        const index = state.chatList.findIndex(chat => chat.chat_uid === chatUid)
        if (index !== -1) {
            Vue.set(state.chatList[index], 'last_message', lastMessage)
            Vue.set(state.chatList[index], 'last_sent', lastMessage?.created || null)
        }

        if (state.activeChat?.chat_uid === chatUid) {
            Vue.set(state.activeChat, 'last_message', lastMessage || null)
        }
    },
    SET_CHAT_READED_AT_BY_CHAT_ID(state, { chatUid, readedAt }) {
        if (!chatUid) return

        const index = state.chatList.findIndex(chat => chat.chat_uid === chatUid)
        if (index !== -1) {
            Vue.set(state.chatList[index], 'readed_at', readedAt || null)
        }

        if (state.activeChat?.chat_uid === chatUid) {
            Vue.set(state.activeChat, 'readed_at', readedAt || null)
        }
    },
    SET_CHAT_MESSAGE_MODAL(state, id) {
        if (!state.messageModal?.[id]) {
            Vue.set(state.messageModal, id, {
                text: ''
            })
        }
    },
    CHANGE_CHAT_MESSAGE_MODAL(state, { id, message }) {
        if (!state.messageModal?.[id]) {
            Vue.set(state.messageModal, id, {
                text: ''
            })
        }
        Vue.set(state.messageModal[id], 'text', message)
    },
    SET_CHAT_MESSAGE(state, id) {
        if (!state.message?.[id]) {
            Vue.set(state.message, id, {
                text: ''
            })
        }
    },
    ADD_CHAT_MESSAGE_ATTACHMENT(state, { id, attachment }) {
        const msg = state.message[id] || {}

        const list = Array.isArray(msg.attachments) ? msg.attachments.slice() : []
        list.push(attachment)

        Vue.set(msg, 'attachments', list)
        Vue.set(state.message, id, msg)
    },
    REMOVE_CHAT_MESSAGE_ATTACHMENT(state, { id, attachmentId, index }) {
        const msg = state.message?.[id]
        const list = msg?.attachments

        if (!msg || !Array.isArray(list) || !list.length) return

        let i = -1
        if (attachmentId) i = list.findIndex(f => f && f.id === attachmentId)
        else if (Number.isInteger(index)) i = index

        if (i === -1) return

        const next = list.slice()
        next.splice(i, 1)

        Vue.set(state.message[id], 'attachments', next)
    },
    CHANGE_CHAT_MESSAGE(state, { id, message }) {
        if (!state.message?.[id]) {
            Vue.set(state.message, id, {
                text: ''
            })
        }
        Vue.set(state.message[id], 'text', message)
    },
    CHANGE_CHAT_ALL_MESSAGE(state, { id, message }) {
        Vue.set(state.message, id, message)
    },
    CHANGE_CHAT_MESSAGE_BY_KEY(state, { id, value, key }) {
        Vue.set(state.message[id], key, value)
    },
    CLEAR_EDIT_MESSAGE(state, { id }) {
        Vue.set(state.message, id, {
            text: ""
        })
    },
    SET_MESSAGE_NEXT(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid || !state.chatMessage[chat_uid]) return
        state.chatMessage[chat_uid].next = data.next ? data.next.split('?')[1] : ''
    },
    CONCAT_CHAT_MESSAGE(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid || !state.chatMessage[chat_uid]) return
        state.chatMessage[chat_uid].value.unshift(...data.results)
    },
    OPEN_CHAT_MESSAGE(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid) return

        const hasPrev = !!(data.previous && data.previous.length)
        const currentList = state.chatMessage[chat_uid]?.value

        const chatMessage = {
            value: mergeOpenMessagesWithOptimistic(currentList, data.results, chat_uid),
            status: data.next ? true : false,
            next: data.next ? data.next.split('?')[1] : '',
            prev: data.previous ? data.previous.split('?')[1] : '',
            bottomStatus: hasPrev,
            page: 1
        }
        state.messageListPrev = hasPrev
        Vue.set(state.chatMessage, chat_uid, chatMessage)
    },
    SET_MESSAGE_PREV(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid || !state.chatMessage[chat_uid]) return
        const nextPrev = data.previous ? data.previous.split('?')[1] : ''
        state.chatMessage[chat_uid].prev = nextPrev
        state.chatMessage[chat_uid].bottomStatus = !!nextPrev
        state.messageListPrev = !!nextPrev
    },
    SET_MESSAGE_PREV_VALUE(state, { chat_uid, value = '' }) {
        if (!chat_uid || !state.chatMessage[chat_uid]) return
        state.chatMessage[chat_uid].prev = value
        state.chatMessage[chat_uid].bottomStatus = !!value
        state.messageListPrev = !!value
    },
    PUSH_CHAT_MESSAGE(state, payload) {
        const chat_uid = payload?.chat_uid || state.activeChat?.chat_uid
        const data = payload?.data || payload
        if (!chat_uid || !state.chatMessage[chat_uid]) return
        state.chatMessage[chat_uid].value.push(...data.results)
    },
    SET_CHAT_LIST_NEXT(state, value) {
        if (!value)
            state.chatListNext = false
    },
    CLEAR_CONTACT_LIST(state) {
        state.contactListNext = true
        state.contactList = []
    },
    SET_CONTACT_LIST_NEXT(state, value) {
        if (!value)
            state.contactListNext = false
    },
    SET_CONTACT_GROUP_NEXT(state, value) {
        if (!value)
            state.contactGroupNext = false
    },
    SET_CHAT_LIST_PAGE(state, value) {
        state.chatListPage = value
    },
    SET_CONTACT_LIST_PAGE(state, value) {
        state.contactListPage = value
    },
    SET_CONTACT_GROUP_PAGE(state, value) {
        state.contactGroupPage = value
    },
    SET_CHAT_MEMBERS(state, { data, chat }) {
        Vue.set(state.chatMembers, chat, {
            ...data,
            page: 2
        })
    },
    setValueState(state, { name, value }) {
        state[name] = value
    },
    CONCAT_CHAT_MEMBERS(state, { data, chat }) {
        state.chatMembers[chat].results = state.chatMembers[chat].results.concat(data.results)
        state.chatMembers[chat].next = data.next
        state.chatMembers[chat].page = state.chatMembers[chat].page + 1
    },
    setReplyMessage(state, { id, mesage }) {
        Vue.set(state.replyMessage, id, mesage)
    },
    setReplyMessageModal(state, { id, mesage }) {
        Vue.set(state.replyMessageModal, id, mesage)
    },
    DELETE_REPLY_MESSAGE(state, id) {
        Vue.delete(state.replyMessage, id)
    },
    DELETE_REPLY_MESSAGE_MODAL(state, id) {
        Vue.delete(state.replyMessageModal, id)
    },
    PUSH_FILE_LIST(state, { id, file }) {
        if (state.fileList?.[id]?.length) {
            state.fileList[id].push(file)
        } else {
            Vue.set(state.fileList, id, [file])
        }

    },
    FILE_CHANGE_FIELD(state, { id, field, fileId, value }) {
        if (state.fileList?.[id]?.length) {
            const index = state.fileList[id].findIndex(elem => elem.iid === fileId)
            if (index !== -1) {
                Vue.set(state.fileList[id][index], field, value)
            }
        }
    },
    FILE_DELETE(state, id) {
        if (state.fileList?.[id]?.length) {
            Vue.delete(state.fileList, id)
        }
    },
    SET_FILE_LIST(state, { id, files }) {
        if (Array.isArray(files) && files.length) {
            Vue.set(state.fileList, id, files)
        } else if (state.fileList?.[id]) {
            Vue.delete(state.fileList, id)
        }
    },
    FILE_DELETE_BY_KEY(state, { id, fileId }) {
        if (state.fileList?.[id]?.length) {
            const index = state.fileList[id].findIndex(elem => elem.iid === fileId)
            if (index !== -1) {
                Vue.delete(state.fileList[id], index)
            }
        }
    },
    SET_FILE_MODAL(state, { id, value }) {
        Vue.set(state.fileModal, id, value)
    },
    clearContactsGroup(state) {
        state.contactsGroup = []
        state.contactGroupNext = true
        state.contactGroupPage = 0
    },
    DELETE_MEMBER(state, { chat, user }) {
        if (state.chatMembers[chat]) {
            state.activeChat.member_count -= 1
            state.chatMembers[chat].count -= 1
            state.contactGroupPage = 0
            state.chatMembers[chat].results = state.chatMembers[chat].results.filter(el => el.user.id !== user)
        }
    },
    ADD_MEMBER(state, data) {
        // state.activeChat.member_count += data?.members.length
        // state.chatMembers[id].results
    },
    INIT_MEMBERS_LIST(state, data) {
        const chat = data.chat_uid

        if(state.chatMembers[chat]) {
            state.chatMembers[chat].results = []
            state.chatMembers[chat].next = true
            state.chatMembers[chat].page = 0
        }

        state.contactGroupPage = 0
    },
    CHAT_PLUS_MEMBERS(state, data) {
        if(state.activeChat && data?.members?.length) {
            state.activeChat.member_count += data.members.length
        }
    },
    LEAVE_CHAT(state, { chat }) {
        state.chatList = state.chatList.filter(el => el.chat_uid !== chat)
        state.activeChat = null
    },
    addUserCount(state) {
        state.activeChat.member_count += state.selectedContacts.length
        state.selectedContacts.forEach(el => {
            state.contactsGroup = state.contactsGroup.filter(item => item.id !== el)

        })
    },
    clearMessage(state) {
        const chat_uid = state.activeChat?.chat_uid
        if (!chat_uid) return
        Vue.delete(state.chatMessage, chat_uid)
        if (state.chatHistoryStateByChat?.[chat_uid]) {
            Vue.delete(state.chatHistoryStateByChat, chat_uid)
        }
    },

    clearMemberSideBar(state) {
        state.moderate = []
        state.selectedContacts = []
    },

    SET_LOADING_INFOCHAT(state, value) {
        state.loadingInfoChat = value
    },
    DELETE_CHAT(state, chat) {
        state.chatList = state.chatList.filter(el => el.chat_uid !== chat)
        state.activeChat = state.chatList[0]
    },
    removeMessage(state, { chat_uid, message_uid }) {
        if (!message_uid) return

        Object.keys(state.chatMessage || {}).forEach(currentChatUid => {
            const bucket = state.chatMessage?.[currentChatUid]
            const list = bucket?.value
            if (!Array.isArray(list) || !list.length) return

            if (chat_uid && currentChatUid === chat_uid) {
                const nextList = list.filter(el => el.message_uid !== message_uid)
                Vue.set(bucket, 'value', nextList)

                const lastMessage = nextList.length ? nextList[nextList.length - 1] : null

                const chatIndex = state.chatList.findIndex(c => c.chat_uid === chat_uid)
                if (chatIndex !== -1) {
                    const chat = state.chatList[chatIndex]

                    Vue.set(chat, 'last_message', lastMessage)
                    Vue.set(chat, 'last_sent', lastMessage?.created || null)
                }

                if (state.activeChat?.chat_uid === chat_uid) {
                    Vue.set(state.activeChat, 'last_message', lastMessage)
                }

                if (bucket.slice_count) {
                    if (bucket.slice_count === 1)
                        Vue.delete(bucket, 'slice_count')
                    else
                        Vue.set(bucket, 'slice_count', bucket.slice_count - 1)
                }

                return
            }

            list.forEach(message => {
                markDeletedMessageByUid(message, message_uid)
            })
        })

        ;(state.chatList || []).forEach(chat => {
            markDeletedMessageByUid(chat?.last_message, message_uid)
        })

        if (state.activeChat?.last_message) {
            markDeletedMessageByUid(state.activeChat.last_message, message_uid)
        }

        Object.keys(state.pinMessage || {}).forEach(currentChatUid => {
            const bucket = state.pinMessage?.[currentChatUid]
            const list = bucket?.results
            if (!Array.isArray(list) || !list.length) return

            list.forEach(message => {
                markDeletedMessageByUid(message, message_uid)
            })
        })

        if (chat_uid && state.replyMessage?.[chat_uid]) {
            markDeletedMessageByUid(state.replyMessage[chat_uid], message_uid)
        }

        if (chat_uid && state.replyMessageModal?.[chat_uid]) {
            markDeletedMessageByUid(state.replyMessageModal[chat_uid], message_uid)
        }
    },
    setStatusUser(state, data) {
        state.statusUsers = []
        if (data.public) {
            if(data.members?.length) {
                data.members.forEach(el => {
                    state.statusUsers.push({ user_uid: el.user, online: el.status.online })
                })
            }
        } else {
            state.statusUsers.push({ ...data.members })
        }

    },

    setOfflineUser(state, { user, last_activity }) {
        if (state.statusUsers[user]) {
            state.statusUsers[user].online = false
            state.statusUsers[user].last_activity = last_activity
        } else {
            Vue.set(state.statusUsers, user, { online: false })
        }
    },

    setOnlineUser(state, { user }) {
        // console.log("USER", state.statusUsers[user])
        if (state.statusUsers[user])
            state.statusUsers[user].online = true
        else
            Vue.set(state.statusUsers, user, { online: true })

    },
    addChatList(state, chat) {
        state.chatList.push(chat)
        state.chatList = orderBy(state.chatList, ['last_sent'], ['desc'])

    },

    CHANGE_SOCKET_MODER(state, {data, user}) {
        if (!data?.chat_uid || !Array.isArray(data.members) || !data.members.length) return

        const currentUserChange = user
            ? data.members.find(member => String(member.user) === String(user.id))
            : null

        if (currentUserChange) {
            if (state.activeChat?.chat_uid === data.chat_uid) {
                Vue.set(state.activeChat, 'is_moderator', toBoolean(currentUserChange.is_moderator))
            }

            const chatIndex = state.chatList.findIndex(chat => chat.chat_uid === data.chat_uid)
            if (chatIndex !== -1) {
                Vue.set(state.chatList[chatIndex], 'is_moderator', toBoolean(currentUserChange.is_moderator))
            }
        }

        if (state.chatMembers?.[data.chat_uid]?.results?.length) {
            data.members.forEach(member => {
                const index = state.chatMembers[data.chat_uid].results.findIndex(f => String(f.user.id) === String(member.user))
                if (index !== -1) {
                    Vue.set(state.chatMembers[data.chat_uid].results[index], 'is_moderator', toBoolean(member.is_moderator))
                }
            })
        }
    },
    CHANGE_CHAT_AUTHOR(state, { data, user }) {
        if (!data?.chat_uid || !data?.chat_author) return

        if (state.activeChat?.chat_uid === data.chat_uid) {
            Vue.set(state.activeChat, 'chat_author', data.chat_author)

            if (String(data.chat_author.id) === String(user?.id)) {
                Vue.set(state.activeChat, 'is_moderator', true)
            }
        }

        const chatIndex = state.chatList.findIndex(chat => chat.chat_uid === data.chat_uid)
        if (chatIndex !== -1) {
            Vue.set(state.chatList[chatIndex], 'chat_author', data.chat_author)

            if (String(data.chat_author.id) === String(user?.id)) {
                Vue.set(state.chatList[chatIndex], 'is_moderator', true)
            }
        }

        if (state.chatMembers?.[data.chat_uid]?.results?.length) {
            state.chatMembers[data.chat_uid].results.forEach((member, index) => {
                const isAuthor = String(member.user?.id) === String(data.chat_author.id)

                Vue.set(state.chatMembers[data.chat_uid].results[index], 'is_author', isAuthor)

                if (isAuthor) {
                    Vue.set(state.chatMembers[data.chat_uid].results[index], 'is_moderator', true)
                }
            })
        }
    },

    ADD_CHAT_SPLICE(state, value) {
        if(state.chatMessage[value.chat_uid]) {
            if(state.chatMessage[value.chat_uid].slice_count) {
                Vue.set(state.chatMessage[value.chat_uid], 'slice_count', state.chatMessage[value.chat_uid].slice_count + 1)
            } else {
                Vue.set(state.chatMessage[value.chat_uid], 'slice_count', 1)
            }
        }
    },
    SET_SUPPORT_MESSAGE_TEMPLATES(state, value) {
        state.supportMessageTemplates.push(...value)
    },
    RESET_SUPPORT_MESSAGE_TEMPLATES(state) {
        state.supportMessageTemplates = []
    },
    UPDATE_SUPPORT_MESSAGE_TEMPLATE(state, data) {
        state.supportMessageTemplates[data.index] = { ...data.template }
    },
    ADD_SUPPORT_MESSAGE_TEMPLATE(state, template) {
        state.supportMessageTemplates.unshift(template)
    },
    RESET_SMT_PAGE(state) {
        state.smt_page = 1
    },
    INCREMENT_SMT_PAGE(state) {
        state.smt_page += 1
    },
    SET_SMT_END_OF_LIST(state, value) {
        state.smt_endOfList = value
    },
    CONCAT_HELPDESK(state, value) {
        state.helpDeskList = state.helpDeskList.concat(value)
    },
    CLEAR_HELPDESK_LIST(state) {
        state.helpDeskList = []
        state.helpDeskNext = true
        state.helpDeskPage = 0
    },
    SET_HELPDESK_LIST_NEXT(state, value) {
        if (!value) state.helpDeskNext = false
    },
    SET_HELPDESK_LIST_PAGE(state, value) {
        state.helpDeskPage = value
    },
    SET_REACTIONS(state, value) {
        state.reactions = value
    }
}
