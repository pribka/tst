import Vue from 'vue'

export default {
    SET_LOADING(state, value) {
        state.loading = value
    },
    SET_LOADED(state, value) {
        state.loaded = value
    },
    SET_LIST(state, list) {
        Vue.set(state, 'list', Array.isArray(list) ? list : [])
    }
}
