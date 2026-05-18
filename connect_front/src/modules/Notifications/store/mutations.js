import moment from 'moment'

const toSafeInt = value => {
    const parsed = Number(value)
    if (!Number.isFinite(parsed) || parsed <= 0) return 0
    return Math.floor(parsed)
}

const normalizeUnreadByCategory = value => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return {}

    return Object.keys(value).reduce((acc, code) => {
        const unread = toSafeInt(value[code])
        if (unread > 0) acc[code] = unread
        return acc
    }, {})
}

const totalUnreadCount = state => toSafeInt(state.unreadCount) + toSafeInt(state.unreadMentionsCount)

const syncPwaCounter = function(state) {
    this.commit('SET_PWA_COUNTER', { name: 'noty', value: totalUnreadCount(state) })
}

const canShowInCurrentList = (state, data) => {
    if (!data) return false
    if (state.activeTab === 'mentions') {
        return !!data.is_mention
    }
    if (data.is_mention) {
        return false
    }
    if (!state.selectedCategoryCodes.length) {
        return true
    }

    return state.selectedCategoryCodes.includes(data?.category?.code)
}

export default {
    SET_DRAWER_Z_INDEX(state, value = null) {
        if(value) {
            state.drawerZIndex = value
        } else {
            state.drawerZIndex = 801
        }
    },
    SET_DRAWER_VISIBLE(state, value) {
        state.visible = value
    },
    SET_VALUE_STATE(state, { name, data }) {
        state[name] = data
    },
    SET_UNREAD_COUNTS(state, payload = {}) {
        state.unreadCount = toSafeInt(payload.unreadCount)
        state.unreadMentionsCount = toSafeInt(payload.unreadMentionsCount)
        state.unreadByCategory = normalizeUnreadByCategory(payload.unreadByCategory)
    },
    SET_NOTIFICATION_CATEGORIES(state, categories = []) {
        state.categories = categories
    },
    SET_ACTIVE_TAB(state, tab) {
        state.activeTab = tab === 'mentions' ? 'mentions' : 'notifications'
    },
    SET_SELECTED_CATEGORY_CODES(state, codes = []) {
        state.selectedCategoryCodes = Array.from(new Set(codes))
    },
    SET_NEXT(state, value) {
        state.next = value
    },
    SET_PAGE(state, value) {
        state.page = value
    },
    CLEAR_LIST(state) {
        state.next = true
        state.page = 0
        state.listNoty = []
    },
    SET_LIST_NOTY(state, data) {
        const results = Array.isArray(data?.results) ? data.results : []
        if (!results.length) return

        if (state.listNoty.length === 0) {
            state.listNoty = results
            return
        }

        const currentMap = new Map(state.listNoty.map(item => [item.id, item]))
        const incomingIds = new Set()

        results.forEach(item => {
            if (!item?.id) return
            incomingIds.add(item.id)
            currentMap.set(item.id, {
                ...(currentMap.get(item.id) || {}),
                ...item
            })
        })

        state.listNoty = state.listNoty.map(item => {
            if (!incomingIds.has(item.id)) return item
            return currentMap.get(item.id) || item
        })

        results.forEach(item => {
            if (!item?.id || state.listNoty.some(existing => existing.id === item.id)) return
            state.listNoty.push(item)
        })
    },
    SET_LIST_NOTY_BELL(state, data) {
        const results = Array.isArray(data?.results) ? data.results : []
        if (!results.length) return

        if (state.listNotyBell.length === 0) {
            state.listNotyBell = results
            return
        }

        const currentMap = new Map(state.listNotyBell.map(item => [item.id, item]))
        const incomingIds = new Set()

        results.forEach(item => {
            if (!item?.id) return
            incomingIds.add(item.id)
            currentMap.set(item.id, {
                ...(currentMap.get(item.id) || {}),
                ...item
            })
        })

        state.listNotyBell = state.listNotyBell.map(item => {
            if (!incomingIds.has(item.id)) return item
            return currentMap.get(item.id) || item
        })

        results.forEach(item => {
            if (!item?.id || state.listNotyBell.some(existing => existing.id === item.id)) return
            state.listNotyBell.push(item)
        })
    },
    clearList(state) {
        state.listNoty = []
    },
    REMOVE_NOTY_FROM_LIST(state, id) {
        state.listNoty = state.listNoty.filter(item => item.id !== id)
    },
    REMOVE_NOTY_BY_CATEGORIES(state, categoryCodes = []) {
        const codes = Array.isArray(categoryCodes) ? categoryCodes : []
        if (!codes.length) return
        const codeSet = new Set(codes)
        state.listNoty = state.listNoty.filter(item => !codeSet.has(item?.category?.code))
    },
    REMOVE_MENTION_NOTY_FROM_LIST(state) {
        state.listNoty = state.listNoty.filter(item => !item?.is_mention)
    },
    READ_NOTY(state, { id, isMention = null, categoryCode = null }) {
        const existedItem = id === 'all'
            ? null
            : state.listNoty.find(item => item.id === id) || state.listNotyBell.find(item => item.id === id) || null
        const mention = typeof isMention === 'boolean' ? isMention : !!existedItem?.is_mention
        const code = categoryCode || existedItem?.category?.code

        state.listNoty = state.listNoty.map(el => {
            let res = el
            if (id === 'all') {
                res.is_read = true
            }
            else if (id === el.id) {
                res.is_read = true
            }


            return res
        })

        if (id === "all") {
            state.unreadCount = 0
            state.unreadMentionsCount = 0
            state.unreadByCategory = {}
            state.listNotyBell = []
        }
        else {
            if (mention) {
                state.unreadMentionsCount = Math.max(0, toSafeInt(state.unreadMentionsCount) - 1)
            } else {
                state.unreadCount = Math.max(0, toSafeInt(state.unreadCount) - 1)
                if (code) {
                    const currentByCategory = toSafeInt(state.unreadByCategory[code])
                    if (currentByCategory > 1) {
                        state.unreadByCategory = {
                            ...state.unreadByCategory,
                            [code]: currentByCategory - 1
                        }
                    } else if (currentByCategory === 1) {
                        const nextByCategory = { ...state.unreadByCategory }
                        delete nextByCategory[code]
                        state.unreadByCategory = nextByCategory
                    }
                }
            }
            state.listNotyBell = state.listNotyBell.filter(el => el.id !== id)
        }

        syncPwaCounter.call(this, state)
    },
    READ_NOTY_BY_CATEGORIES(state, { categoryCodes = [] }) {
        const codes = Array.isArray(categoryCodes) ? categoryCodes : []
        if (!codes.length) return

        const codeSet = new Set(codes)
        let removedUnreadCount = 0

        state.listNoty = state.listNoty.map(item => {
            const categoryCode = item?.category?.code
            if (item && !item.is_read && !item.is_mention && codeSet.has(categoryCode)) {
                return {
                    ...item,
                    is_read: true
                }
            }
            return item
        })

        state.listNotyBell = state.listNotyBell.filter(item => {
            const categoryCode = item?.category?.code
            return !codeSet.has(categoryCode)
        })

        const nextByCategory = { ...state.unreadByCategory }
        codes.forEach(code => {
            const byCategoryCount = toSafeInt(nextByCategory[code])
            removedUnreadCount += byCategoryCount
            delete nextByCategory[code]
        })
        state.unreadByCategory = nextByCategory
        state.unreadCount = Math.max(0, toSafeInt(state.unreadCount) - removedUnreadCount)
        syncPwaCounter.call(this, state)
    },
    READ_NOTIFICATIONS_FROM_SOCKET(state, ids = []) {
        const normalizedIds = Array.isArray(ids)
            ? ids.filter(id => typeof id === 'string' || typeof id === 'number').map(id => String(id))
            : []

        if (!normalizedIds.length) return

        const idsSet = new Set(normalizedIds)

        state.listNoty = state.listNoty.map(item => {
            if (item?.id && idsSet.has(String(item.id))) {
                return {
                    ...item,
                    is_read: true
                }
            }

            return item
        })

        state.listNotyBell = state.listNotyBell.filter(item => !idsSet.has(String(item?.id)))
    },
    READ_MENTION_NOTY(state) {
        const removedMentionsCount = toSafeInt(state.unreadMentionsCount)

        state.listNoty = state.listNoty.map(item => {
            if (item && !item.is_read && item.is_mention) {
                return {
                    ...item,
                    is_read: true
                }
            }
            return item
        })

        state.listNotyBell = state.listNotyBell.filter(item => !item?.is_mention)
        state.unreadMentionsCount = 0

        if (removedMentionsCount > 0) {
            syncPwaCounter.call(this, state)
        }
    },
    addNotyFromSocket(state, data) {
        let findList = state.listNoty.findIndex(el => el.id === data.id)
        let findBell = state.listNotyBell.findIndex(el => el.id === data.id)

        if (findList === -1 && canShowInCurrentList(state, data)) {
            state.listNoty.unshift({
                ...data,
                created_at: moment(data.created_at).add(-1, 'seconds')
            })
        }
        if (findBell === -1) {
            state.listNotyBell.unshift({
                ...data,
                created_at: moment(data.created_at).add(-1, 'seconds')
            })
        }

        if (data?.is_mention)
            state.unreadMentionsCount = toSafeInt(state.unreadMentionsCount) + 1
        else {
            state.unreadCount = toSafeInt(state.unreadCount) + 1
            const categoryCode = data?.category?.code
            if (categoryCode) {
                const current = toSafeInt(state.unreadByCategory[categoryCode])
                state.unreadByCategory = {
                    ...state.unreadByCategory,
                    [categoryCode]: current + 1
                }
            }
        } 
        
        syncPwaCounter.call(this, state)
    }
}
