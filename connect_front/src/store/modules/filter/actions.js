import axios from '@/config/axios'
import Axios from 'axios'
import eventBus from '@/utils/eventBus'

const chosenFiltersCancels = {}

export default {
    async getFiltersByKey({ commit, state }, { name, page_name, params, excludeFields }) {
        return await new Promise((resolve, reject) => {
            axios.get('app_info/active_filters/', { params: { model: name, page_name, ...params }, })
                .then(({ data }) => {
                    if (!state.filterData[page_name])
                        commit('GENERATE_FILTER_DATA', { name: page_name, model: name })

                    if (!state.filterSelected[page_name])
                        commit('GENERATE_FILTER_SELECTED', { name: page_name, model: name })

                    if (!state.filterShowSearch[page_name])
                        commit('SET_FILTER_SEARCH_INPUT', { name: page_name, data })

                    if (!state.filterTags[page_name])
                        commit('GENERATE_FILTER_TAGS', { name: page_name, model: name })

                    if (!state.filterActive[page_name])
                        commit('GENERATE_FILTER_ACTIVE', { name: page_name, model: name })

                    if (!state.filterExclude[page_name])
                        commit('GENERATE_FILTER_EXCLUDE', { name: page_name, model: name })
                    
                    if(data?.search?.length)
                        commit('SET_FILTERS_SEARCH', { name: page_name, value: data.search })

                    if(data?.ordering?.length)
                        commit('SET_FILTERS_ORDERING', { name: page_name, value: data.ordering })
                        
                    commit('FILTER_GENERATE', { name: page_name, data, excludeFields, model: name })

                    if(data.others)
                        eventBus.$emit(`filter_others_${page_name}`, data.others)
                    eventBus.$emit(`filter_active_${page_name}`, data.activeFilters)

                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    sendFilters({state}, data) {
        return new Promise((resolve, reject) => {
            let filterData = data
            const pageName = data.page_name

            if(state.filtersSearch?.[data.page_name]?.length)
                filterData['search'] =  state.filtersSearch[data.page_name]

            if(state.filterOrdering?.[data.page_name]?.length)
                filterData['ordering'] =  state.filterOrdering[data.page_name]

            if (pageName && chosenFiltersCancels[pageName]) {
                chosenFiltersCancels[pageName].cancel('Canceled stale chosen_filters request')
                delete chosenFiltersCancels[pageName]
            }

            const cancelSource = Axios.CancelToken.source()
            if (pageName) {
                chosenFiltersCancels[pageName] = cancelSource
            }

            axios.post(`app_info/chosen_filters/`, filterData, {
                cancelToken: cancelSource.token
            })
                .then(() => {
                    if (pageName && chosenFiltersCancels[pageName] === cancelSource) {
                        delete chosenFiltersCancels[pageName]
                    }
                    eventBus.$emit(`update_filter_${data.key}`, data.key)
                    eventBus.$emit(`update_filter_data_${data.page_name}`, filterData)
                    if(data.page_name)
                        eventBus.$emit(`update_filter_${data.key}_${data.page_name}`, data.key)
                    resolve()
                })
                .catch((error) => {
                    if (pageName && chosenFiltersCancels[pageName] === cancelSource) {
                        delete chosenFiltersCancels[pageName]
                    }
                    if (Axios.isCancel(error)) {
                        resolve()
                        return
                    }
                    reject(error)
                })
        })
    },

    // Данные для селектов

    getFilterUserSelectDataDrawer({ commit }, { model, name, filterName, page_size, page, search, selected, param }) {
        return new Promise((resolve, reject) => {
            let params = {
                model,
                page_size,
                page,
                selected,
            }

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('user/list/', { params })
                .then(({ data }) => {
                    commit('UPDATE_FILETR_DATA_DRAWER', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    getFilterSelectScrollData({ commit }, { model, name, filterName, page_size, page, search, param, filters, page_name, prefix, model_label, injectSelectParams }) {
        return new Promise((resolve, reject) => {

            let injectParams = {}
            if(injectSelectParams && Object.keys(injectSelectParams)?.length) {
                injectParams = injectSelectParams
            }

            let params = {
                model,
                page_size,
                page,
                filters,
                field: filterName,
                page_name,
                ...injectParams
            }

            if(prefix)
                params.prefix = prefix
            if(model_label)
                params.model_label = model_label

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('app_info/filtered_select_list/', { params })
                .then(({ data }) => {
                    commit('CONCAT_FILTER_DATA_SELECT', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getFilterSelectData({ commit }, { model, name, filterName, page_size, page, search, param, filters, page_name, prefix, model_label, injectSelectParams }) {
        return new Promise((resolve, reject) => {
            let injectParams = {}
            if(injectSelectParams && Object.keys(injectSelectParams)?.length) {
                injectParams = injectSelectParams
            }
            let params = {
                model,
                page_size,
                page,
                filters,
                field: filterName,
                page_name,
                ...injectParams
            }

            if(prefix)
                params.prefix = prefix
            if(model_label)
                params.model_label = model_label

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('app_info/filtered_select_list/', { params })
                .then(({ data }) => {
                    commit('UPDATE_FILETR_DATA_SELECT', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getTreeFilterSelectData({ commit }, { model, name, filterName, search, filters, param, page_name, prefix, model_label, injectSelectParams }) {
        return new Promise((resolve, reject) => {
            const injectParams = {}
            if(injectSelectParams && Object.keys(injectSelectParams)?.length) {
                injectParams = injectSelectParams
            }
            const params = {
                model,
                filters,
                field: filterName,
                page_name,
                ...injectParams
            }

            if(prefix)
                params.prefix = prefix
            if(model_label)
                params.model_label = model_label

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('app_info/filtered_select_list/', { params })
                .then(({ data }) => {
                    commit('UPDATE_TREE_FILTER_DATA_SELECT', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getFilterSelectUserScrollData({ commit }, { model, name, filterName, page_size, page, search,selected, param, filters, prefix, model_label }) {
        return new Promise((resolve, reject) => {

            let params = {
                model,
                page_size,
                page,selected,
                filters,
            }

            if(prefix)
                params.prefix = prefix
            if(model_label)
                params.model_label = model_label

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('user/list/', { params })
                .then(({ data }) => {
                    commit('CONCAT_FILTER_DATA', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getFilterUserSelectData({ commit }, { model, name, filterName, page_size, page, search, selected, param, prefix, model_label }) {
        return new Promise((resolve, reject) => {
            let params = {
                model,
                page_size,
                page,
                selected,
            }

            if(prefix)
                params.prefix = prefix
            if(model_label)
                params.model_label = model_label

            if (param)
                params.param = param

            if (search.length)
                params.search = search

            axios.get('user/list/', { params })
                .then(({ data }) => {
                    commit('UPDATE_FILETR_DATA', { name, filterName, data })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    }
}
