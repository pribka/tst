import moment from 'moment'
import axios from '@/config/axios'
import { setData, getById, updateById } from '../utils/indexedDB.js'

export default {
    getTaskActions({ commit }, { task_type, id }) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/${id}/action_info/`)
                .then(({ data }) => {
                    commit('SET_TASK_ACTIONS', {
                        data,
                        id,
                        task_type
                    })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    async getStatusList({ commit, state }, { task_type }) {
        try {
            commit('SET_STATUS_LOADER', true)
            if(state.statusList?.[task_type]?.length) {
                return state.statusList[task_type]
            } 
            const {data} = await axios.get('/help_desk/tickets/statuses/')

            commit('SET_STATUS_LIST', {
                data,
                task_type
            })
        } catch(e) {
            console.log(e, 'getStatusList')
        } finally {
            commit('SET_STATUS_LOADER', false)
        }
    }
}