import axios from '@/config/axios'

export default {
    fetchActions({ commit }) {
        return new Promise((resolve, reject) => {
            commit('SET_LOADING', true)
            axios.get('/okr/objectives/section_info/')
                .then(({data}) => {
                    commit('SET_ACTIONS', data.actions)
                    resolve(data.actions)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_LOADING', false)
                })
        })
    },
    fetchObjectiveStatuses({ state, commit }) {
        if (state.statuses.length > 0)
            return
        return new Promise((resolve, reject) => {
            commit('SET_LOADING', true)
            axios.get('/okr/objectives/objective_statuses/')
                .then(({data}) => {
                    commit('SET_STATUSES', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_LOADING', false)
                })
        })
    },
    fetchDepartments({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                resolve([])
            commit('SET_DEPARTMENTS_LOADING', true)
            axios.get(`users/my_organizations/${currentContractor.id}/departments_select_list/`, {
                params: {
                    page: 1,
                    page_size: 'all'
                }
            })
                .then(({data}) => {
                    commit('SET_DEPARTMENTS', data.results)
                    resolve(data.results)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_DEPARTMENTS_LOADING', false)
                })
        })
    },
    fetchStakeholders({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            const currentUser = rootState.user.user || null
            if (!currentContractor.id || !currentUser.id)
                resolve([])
            commit('SET_STAKEHOLDERS_LOADING', true)
            axios.get('contractor_permissions/app_sections/okr/members/', {
                params: {
                    page: 1,
                    page_size: 'all',
                    contractor: currentContractor.id,
                    first: currentUser.id
                }
            })
                .then(({data}) => {
                    commit('SET_STAKEHOLDERS', data.results)
                    resolve(data.results)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_STAKEHOLDERS_LOADING', false)
                })
        })
    },
    fetchObjectives({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                resolve([])
            commit('SET_OBJECTIVES_LOADING', true)
            axios.get('okr/objectives/', {
                params: {
                    organization: currentContractor.id,
                    page_name: `${currentContractor.id}_objectives_and_key_results`
                }
            })
                .then(({data}) => {
                    commit('SET_OBJECTIVES', data.results)
                    resolve(data.results)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_OBJECTIVES_LOADING', false)
                })
        })
    },
    fetchObjectivesCount({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                resolve({})
            commit('SET_OBJECTIVES_COUNT_LOADING', true)
            axios.get('okr/objectives/objectives_count/', {
                params: {
                    organization: currentContractor.id,
                    page_name: `${currentContractor.id}_objectives_and_key_results`
                }
            })
                .then(({data}) => {
                    commit('SET_OBJECTIVES_COUNT', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_OBJECTIVES_COUNT_LOADING', false)
                })
        })
    },
    fetchMission({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                resolve({})
            commit('SET_MISSION_LOADING', true)
            axios.get('/okr/mission/', {
                params: {
                    organization: currentContractor.id
                }
            })
                .then(({data}) => {
                    if (data.results.length) {
                        commit('SET_MISSION', data.results[0])
                        resolve(data.results[0])
                    } else {
                        commit('SET_MISSION', {})
                        resolve({})
                    }
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_MISSION_LOADING', false)
                })
        })
    },
    fetchValueEfforts({ commit }) {
        return new Promise((resolve, reject) => {
            axios.get('/okr/value_efforts/')
                .then(({data}) => {
                    commit('SET_VALUE_EFFORTS', data)
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    fetchMetrics({ commit, rootState }) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                resolve([])
            axios.get('/okr/metrics/', {
                params: {
                    contractor: currentContractor.id,
                    page_size: 'all'
                }
            })
                .then(({data}) => {
                    if (data?.results) {
                        commit('SET_METRICS', data.results)
                        resolve(data.results)
                    }
                })
                .catch((error) => { reject(error) })
        })
    },
    addMetric({ commit, rootState }, { name, description}) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                reject()
            commit('SET_ADD_METRIC_LOADING', true)
            const payload = {
                contractor: currentContractor.id,
                name: name,
                description: description
            }
            axios.post('/okr/metrics/', payload)
                .then(({data}) => {
                    commit('ADD_METRIC', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_ADD_METRIC_LOADING', false)
                })
        })
    },
    updateMetric({ commit, rootState }, { id, name, description}) {
        return new Promise((resolve, reject) => {
            const currentContractor = rootState.user.user.current_contractor || null
            if (!currentContractor.id)
                reject()
            commit('SET_ADD_METRIC_LOADING', true)
            const payload = {
                contractor: currentContractor.id,
                name: name,
                description: description
            }
            axios.put(`/okr/metrics/${id}/`, payload)
                .then(({data}) => {
                    commit('UPDATE_METRIC', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_ADD_METRIC_LOADING', false)
                })
        })
    },
    fetchReminders({ commit }) {
        return new Promise((resolve, reject) => {
            commit('SET_REMINDERS_LOADING', true)
            axios.get('/okr/objectives/notification_frequencies/')
                .then(({data}) => {
                    commit('SET_REMINDERS', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
                .finally(() => {
                    commit('SET_REMINDERS_LOADING', false)
                })
        })
    },
    fetchObjectiveDetail({ commit }, objectiveID) {
        return new Promise((resolve, reject) => {
            axios.get(`/okr/objectives/${objectiveID}/`)
                .then(({data}) => {
                    commit('SET_OBJECTIVE_DETAIL', data)
                    commit('SET_OBJECTIVE_KEY_RESULTS', data.key_results)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    fetchKeyResults({ commit, state }, { objectiveID, quarter }) {
        return new Promise((resolve, reject) => {
            axios.get('/okr/key_results/', {
                params: {
                    objective: objectiveID,
                    page_size: 'all'
                }
            })
                .then(({ data }) => {
                    if (quarter) {
                        commit('SET_OBJECTIVE_KEY_RESULTS_IN_QUARTER_LIST', {
                            objectiveID: objectiveID,
                            quarter: quarter,
                            keyResults: data.results
                        })
                    } else {
                        if (!!state.objectiveKeyResults) {
                            commit('SET_OBJECTIVE_KEY_RESULTS', data.results)
                        }
                        commit('SET_OBJECTIVE_KEY_RESULTS_IN_LIST', {
                            objectiveID: objectiveID,
                            keyResults: data.results
                        })
                        
                    }
                    resolve(data.results)
                })
                .catch((error) => { reject(error) })
        })
    }
}