import axios from '@/config/axios'
export default {
    createOrder({ commit }, form) {
        return new Promise((resolve, reject) => {
            let formData = JSON.parse(JSON.stringify(form))
            if(formData.logistic_manager?.id)
                formData.logistic_manager = formData.logistic_manager.id

            axios.post('/crm/orders/create_from_cart/', formData)
                .then(({data}) => {
                    if (data) {
                        if (form.oper_type > 0) {
                            commit('CLEAR_CART_ALL')
                            commit('SET_CART_VISIBLE', false)
                            commit('SET_CREATE_VISIBLE', false)
                            commit('products/ALL_PRODUCT_CART_REMOVED', null, {root: true})
                        }
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    checkCart({ state }) {
        return new Promise((resolve, reject) => {
            if(state.cartList?.results?.length) {
                let emptyElem = []

                state.cartList.results.forEach(item => {
                    if(!item.goods.available_count) {
                        emptyElem.push(item.id)
                    }
                })

                if(emptyElem?.length) {
                    resolve(false)
                } else {
                    resolve(true)
                }
            } else
                resolve(false)
        })
    },
    addShoppingCartWarehouse({ commit }, {waList, id}) {
        return new Promise(async (resolve, reject) => {
            try {
                let quantity = 0
                for (const key in waList) {
                    const queryData = {
                        goods: id,
                        quantity: typeof waList[key] === 'boolean' ? 0 : waList[key],
                        warehouse: key
                    }
                    if(waList[key]) {
                        quantity = quantity + (typeof waList[key] === 'boolean' ? 1 : waList[key])
                        await axios.post('/crm/return_cart/', queryData)
                        commit('products/PRODUCT_CART_ADDED', queryData, { root: true })
                        commit('products/DETAIL_PRODUCT_CART_ADDED', queryData, { root: true })
                    }
                }
                if(quantity)
                    commit('CART_COUNT_IN', quantity)

                resolve(true)
            } catch(e) {
                reject(e)
            }
        })
    },
    addShoppingCart({ commit, rootState }, queryData) {
        return new Promise((resolve, reject) => {
            axios.post('/crm/return_cart/', queryData)
                .then(({ data }) => {
                    const config = rootState.config.config,
                        minCart = config?.order_setting?.min_product_count === 0 ? 0 : 1;

                    let qData = JSON.parse(JSON.stringify(queryData))

                    if(minCart <= 0)
                        qData.quantity = 1

                    commit('CART_COUNT_IN', qData.quantity)
                    commit('products/PRODUCT_CART_ADDED', qData, { root: true })
                    commit('products/DETAIL_PRODUCT_CART_ADDED', qData, { root: true })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getOrderListReload({ commit, state }) {
        return new Promise((resolve, reject) => {
            commit('SET_ORDER_PAGE', 1)

            let params = {
                page: state.orderPage,
                page_size: 15
            }

            if(state.currentContract) {
                params.contract = state.currentContract
            }

            axios.get('/crm/return_cart/', { params })
                .then(({ data }) => {
                    commit('SET_ORDER_LIST_RELOAD', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getOrderList({ commit, state }) {
        return new Promise((resolve, reject) => {
            commit('SET_ORDER_PAGE', state.orderPage+1)

            let params = {
                page: state.orderPage,
                page_size: 15
            }

            if(state.currentContract) {
                params.contract = state.currentContract
            }

            axios.get('/crm/return_cart/', { params })
                .then(({ data }) => {
                    if(state.firstOrderLoading)
                        commit('SET_ORDER_FIRST_LOADING', false)

                    if(!data?.results?.length && state.orderPage === 1) {
                        commit('SET_ORDER_EMPTY', true)
                    } else {
                        if(!state.orderList?.amount)
                            commit('ORDER_SET_AMOUNT', data.amount)

                        if(state.orderEmpty)
                            commit('SET_ORDER_EMPTY', false)

                        if(!state.orderCurrency)
                            commit('SET_ORDER_CURRENCY', data.currency)

                        commit('SET_ORDER_NEXT', data.next)
                        commit('CONCAT_ORDER_LIST', data.results)
                        commit('SET_ORDER_LIST_COUNT', data.count)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getCartList({ commit, state }) {
        return new Promise((resolve, reject) => {
            commit('SET_CART_PAGE', state.cartPage+1)

            let params = {
                page: state.cartPage,
                page_size: 30
            }

            axios.get('/crm/return_cart/', { params })
                .then(({ data }) => {
                    if(state.firstLoading)
                        commit('SET_FIRST_LOADING', false)

                    if(!data?.results?.length && state.cartPage === 1) {
                        commit('SET_CART_EMPTY', true)
                    } else {
                        if(!state.cartList?.amount)
                            commit('CART_SET_AMOUNT', data.amount)

                        if(state.goodsEmpty)
                            commit('SET_CART_EMPTY', false)

                        if(!state.cartCurrency)
                            commit('SET_CART_CURRENCY', data.currency)

                        commit('SET_CART_NEXT', data.next)
                        commit('CONCAT_CART_LIST', data.results)
                        commit('SET_CART_LIST_COUNT', data.count)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getCartCount({ commit }) {
        return new Promise((resolve, reject) => {
            axios.get('/crm/return_cart/count/')
                .then(({ data }) => {
                    if(data.count) {
                        commit('SET_CART_COUNT', data.count)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    deleteProductCart({ commit, dispatch }, {goods, count}) {
        return new Promise((resolve, reject) => {
            axios.delete(`/crm/return_cart/${goods.id}/`)
                .then(async () => {
                    commit('DELETE_ITEM_CARD', goods.id)
                    commit('products/PRODUCT_CART_REMOVED', goods.goods.id, { root: true })
                    commit('CART_COUN_M', count)
                    commit('SET_CART_LIST_COUNT_M')
                    commit('CHECK_CART_EMPTY')
                    resolve(true)
                })
                .catch((error) => { reject(error) })
        })
    },
    clearCart({ commit }) {
        return new Promise((resolve, reject) => {
            axios.post('/crm/return_cart/clear/')
                .then(() => {
                    commit('CLEAR_CART_ALL')
                    commit('products/ALL_PRODUCT_CART_REMOVED', null, { root: true })
                    resolve(true)
                })
                .catch((error) => { reject(error) })
        })
    },
    cartCountUpdate({ dispatch }, { goods, quantity }) {
        return new Promise((resolve, reject) => {
            axios.put(`/crm/return_cart/${goods.id}/`, {
                quantity
            })
                .then(() => {
                    resolve(true)
                })
                .catch((error) => { reject(error) })
        })
    },
    getCartSummary({ commit, state }) {
        return new Promise((resolve, reject) => {
            commit('SET_CART_AMOUNT_LOADER', true)
            axios.get('/crm/return_cart/amount/')
                .then(({ data }) => {
                    commit('SET_CART_AMOUNT_LOADER', false)
                    if(data.amount) {
                        commit('CART_SET_AMOUNT', data.amount)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    }
}