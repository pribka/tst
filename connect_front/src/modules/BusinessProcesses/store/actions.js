import axios from '@/config/axios'
export default {
    getMainList({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.processList?.length) {
                resolve(state.processList)
            } else {
                axios.get('/processes/business_process_template/list/')
                    .then(({ data }) => {
                        if(data?.length)
                            commit('SET_PROCESS_LIST', data)
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    }
}