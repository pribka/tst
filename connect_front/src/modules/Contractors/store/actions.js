import axios from '@/config/axios'
export default {
    getContractorInfiniteList({ commit, state }, { contractorsType, params }) {
        return new Promise((resolve, reject) => {
            let url
            if(contractorsType === 'contractors')
                url = '/catalogs/contractors/detailed_list/'
            else if(contractorsType === 'leads')
                url = '/catalogs/leads/'
            
            axios.get(url, { params })
                .then(({ data }) => {
                    commit('SET_CONSTRACTORS', {
                        data: data, 
                        key: contractorsType,
                        page: params.page
                    })
                    resolve(data)
                })
                .catch()
        })
    },
    getContractorList({ commit, state }, { contractorsType, params }) {
        return new Promise((resolve, reject) => {
            let url
            if(contractorsType === 'contractors')
                url = '/catalogs/contractors/detailed_list/'
            else if(contractorsType === 'leads')
                url = '/catalogs/leads/'
            
            axios.get(url, { params })
                .then(({ data }) => {
                    commit('SET_CONSTRACTORS_TABLE', {
                        data: data, 
                        key: contractorsType,
                        page: params.page
                    })
                    resolve(data)
                })
                .catch()
        })
    },
    getGridType({ commit}) {
        return new Promise((resolve, reject) => {
            axios.get(`/app_info/contractors_list_info/`)
                .then(({ data }) => {
                    commit('SET_GRID_TYPE', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
}