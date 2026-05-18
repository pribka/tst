import axios from '@/config/axios'

export default {
    async fetchActionInfo({ state, commit }, contractorId) {
        if(!contractorId) {
            commit('RESET')
            return {}
        }

        if(state.loaded && state.contractorId === contractorId) {
            return state.actions
        }

        const { data } = await axios.get('/wiki/current_contractor/action_info/')
        const actions = data?.actions || {}

        commit('SET_ACTIONS', actions)
        commit('SET_CONTRACTOR_ID', contractorId)
        commit('SET_LOADED', true)

        return actions
    }
}
