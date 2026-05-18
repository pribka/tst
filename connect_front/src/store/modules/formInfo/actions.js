import axios from '@/config/axios'
export default {
    getFormInfo({ commit, state }, { form }) {
        return new Promise((resolve, reject) => {
            if(state.formInfo?.[form]) {
                return state.formInfo[form]
            } else {
                const params = {
                    form
                }
                axios.get('app_info/form_fields_info/', { params })
                    .then(({ data }) => {
                        if(data) {
                            commit('SET_FORM_INFO', { data, form })
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    }
}