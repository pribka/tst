export default {
    SET_ACTIONS(state, value) {
        state.actions = value || {}
    },
    SET_CONTRACTOR_ID(state, value) {
        state.contractorId = value || null
    },
    SET_LOADED(state, value) {
        state.loaded = value
    },
    RESET(state) {
        state.actions = {}
        state.contractorId = null
        state.loaded = false
    }
}
