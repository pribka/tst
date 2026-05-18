import axios from '@/config/axios'

const uniqById = (arr) => {
    const map = new Map()
    ;(arr || []).forEach(u => {
        if (u && u.id != null && !map.has(u.id)) map.set(u.id, u)
    })
    return Array.from(map.values())
}

const mergeRecent = (current, added, max) => {
    const next = uniqById([...(added || []), ...(current || [])])
    return next.slice(0, max)
}

export default {
    async fetchRecent({ state, commit }) {
        if (state.loaded) return state.list

        commit('SET_LOADING', true)
        try {
            const { data } = await axios.get('app_info/recently_selected_users/')
            commit('SET_LIST', Array.isArray(data) ? data : [])
            commit('SET_LOADED', true)
            return state.list
        } finally {
            commit('SET_LOADING', false)
        }
    },
    async clearAll({ commit }) {
        commit('SET_LOADING', true)
        try {
            await axios.delete('app_info/recently_selected_users/')
            commit('SET_LIST', [])
            commit('SET_LOADED', true)
        } finally {
            commit('SET_LOADING', false)
        }
    },
    async saveRecent({ state, commit }, payload) {
        const usersForBackend = (payload && payload.usersForBackend) || []
        const usersForUi = (payload && payload.usersForUi) || []

        const nextList = mergeRecent(state.list, usersForUi, 30)
        commit('SET_LIST', nextList)

        if (this && this.$recentUsersSync) {
            this.$recentUsersSync.post({ type: 'recentUsers:set', list: nextList })
        }

        const idsToSend = usersForBackend.map(u => u && u.id).filter(Boolean)
        if (!idsToSend.length) return state.list

        commit('SET_LOADING', true)
        try {
            await axios.post('app_info/recently_selected_users/', { id: idsToSend })
        } finally {
            commit('SET_LOADING', false)
        }

        return state.list
    }
}