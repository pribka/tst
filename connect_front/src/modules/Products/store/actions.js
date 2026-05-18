import axios from '@/config/axios'
import { getById } from '../utils/productDb'
export default {
    getGridType({ commit}) {
        return new Promise((resolve, reject) => {
            axios.get(`/app_info/products_list_info/`)
                .then(({ data }) => {
                    commit('SET_GRID_TYPE', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getGoodsHistory({ commit, state, rootState }) {
        return new Promise((resolve, reject) => {
            if(state.historyGoods.length) {
                resolve(state.historyGoods)
            } else {
                const user = rootState.user.user,
                    id = `history_${user.id}`,
                    databaseName = 'products';

                getById({ 
                    id, 
                    databaseName
                })
                    .then(data => {
                        if(data?.value?.length) {
                            commit('SET_HISTORY', data.value)
                        }
                    })
                    .catch(error => {
                        reject(error)
                    })
            }
        })
    },
    getDetailGoods({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`catalogs/goods/${id}/`)
                .then(({ data }) => {
                    if (data) {
                        commit('SET_DETAIL', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getGoods({ commit, state }, { page_name }) {
        return new Promise((resolve, reject) => {
            const newPage = state.goodsPage[page_name] + 1
            commit('SET_GOODS_PAGE', {value: newPage, page_name})
            let endpoint = '/catalogs/goods/'
            let params = {
                page_size: 12,
                page: state.goodsPage[page_name],
                page_name
            }

            if (state.goodsSearch?.length) {
                // params['text'] = state.goodsSearch
                endpoint = '/catalogs/goods/search/'
            }

            if (state.goodsCategory)
                params['category'] = state.goodsCategory

            axios.get(endpoint, { params })
                .then(({ data }) => {
                    if (!data?.results?.length && state.goodsPage === 1)
                        commit('SET_GOODS_EMPTY', {page_name, value: true})
                    else {
                        if (state.goodsEmpty)
                            commit('SET_GOODS_EMPTY', {page_name, value: false})

                        commit('SET_GOODS_NEXT', {value: data.next, page_name})
                        commit('CONCAT_GOODS_LIST', {value: data.results, page_name})
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    }
}