import { useTitle } from '@vueuse/core'
import axios from '@/config/axios'

export default {
    namespaced: true,
    state: {
        project: null,
        projectActions: null
    },
    mutations: {
        SET_PROJECT(state, value) {
            state.project = value
        },
        SET_PROJECT_ACTIONS(state, value) {
            state.projectActions = value
        }
    },
    actions: {
        getProjectActions({commit}, { id }) {
            return new Promise((resolve, reject) => {
                axios.get(`/sports_facilities/${id}/action_info/`)
                    .then(async ({ data }) => {
                        if(data) {
                            commit('SET_PROJECT_ACTIONS', data)
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            })
        },
        getProject({ commit, state, dispatch }, { id, reload }) {
            return new Promise((resolve, reject) => {
                if(state.project && !reload) {
                    dispatch('getProjectActions', { id })
                        .then(() => {
                            resolve(state.project)
                        })
                        .catch((error) => { reject(error) })
                    
                } else {
                    if(!reload)
                        commit('SET_PROJECT', null)
                    axios.get(`/sports_facilities/${id}/`)
                        .then(async ({ data }) => {
                            if(data) {
                                if(!reload)
                                    await dispatch('getProjectActions', { id })
                                useTitle(`${data.name} | Паспорт объекта`)
                                commit('SET_PROJECT', data)
                            }
                            resolve(data)
                        })
                        .catch((error) => { reject(error) })
                }
            })
        },
        changeStatus({ dispatch }, { id, code }) {
            return new Promise((resolve, reject) => {
                axios.put(`sports_facilities/${id}/update_status/`, {
                    status: code
                })
                    .then(async ({ data }) => {
                        if(data) {
                            await dispatch('getProject', { id, reload: true })
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            })
        }
    }
}