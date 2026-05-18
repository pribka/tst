import Vue from 'vue'
export default {
    SET_FORM_INFO(state, { form, data }) {
        Vue.set(state.formInfo, form, data)
    }
}