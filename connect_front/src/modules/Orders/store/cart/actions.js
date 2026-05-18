import axios from '@/config/axios'
import eventBus from '@/utils/eventBus.js'

const buildTpGoodsPayload = (results = []) => (results || [])
    .filter(goods => goods?.goods?.id)
    .map(goods => ({
        goods: goods.goods.id,
        quantity: goods.quantity,
        warehouse: goods.warehouse?.id || null,
        measure_unit: goods.measure_unit?.id || null,
        coefficient: goods.coefficient || null,
        custom_price: goods.custom_price ? goods.custom_price : goods.price || goods.goods?.price || null,
        goods_for_print: goods.goods_for_print?.id || goods.goods_for_print?.goods?.id || goods.goods.id
    }))

export default {
    getOrderActions({ commit }, { id }) {
        return new Promise((resolve, reject) => {
            axios.get(`/crm/orders/${id}/action_info/`)
                .then(({data}) => {
                    if(data?.actions) {
                        commit('SET_ORDER_ACTIONS', data.actions)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getOrderTableInfo({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.orderTableInfo) {
                resolve(state.orderTableInfo)
            } else {
                axios.get('/crm/orders/table_info/')
                    .then(({data}) => {
                        if(data?.columns) {
                            commit('SET_ORDER_TABLE_INFO', data.columns)
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    getWarehouseFormInfo({ commit }, goods = null) {
        return new Promise((resolve, reject) => {
            let params = {}

            if(goods) {
                params = {
                    goods
                }
            }

            axios.get('/crm/shopping_cart/form_info/', { params })
                .then(({data}) => {
                    if (data) {
                        commit('SET_WAREHOUSE_INFO', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addToCreateOrders({ commit, state }, uid) {
        let tpGoods = []

        if(state.newOrderTPGoods?.length) {
            state.newOrderTPGoods.forEach(goods => {
                tpGoods.push({
                    goods: goods.goods.id,
                    quantity: goods.quantity,
                    warehouse: state.newOrderWarehouse || null,
                    measure_unit: goods.measure_unit?.id || null,
                    coefficient: goods.coefficient || null,
                    custom_price: goods.custom_price ? goods.custom_price : goods.price || null,
                    goods_for_print: goods.goods_for_print?.id || goods.goods.id
                })
            })
        }
        commit('ADD_TO_CREATE_ORDERS', {
            uid: uid,
            tpgoodsList: tpGoods,
        })
    },
    updateOrder({ commit, state }, form) {
        return new Promise((resolve, reject) => {
            let formData = JSON.parse(JSON.stringify(form))
            if(formData.logistic_manager?.id)
                formData.logistic_manager = formData.logistic_manager.id
            if(formData.operator?.id)
                formData.operator = formData.operator.id
            if(formData.cash_pay_recipient?.id)
                formData.cash_pay_recipient = formData.cash_pay_recipient.id
            if(formData.warehouse)
                delete formData.warehouse
            if(formData.attachments?.length) {
                formData.attachments = formData.attachments.map(file => {
                    if(file.id)
                        return file.id
                    else
                        return file
                })
            }
            if(formData.co_executors?.length) {
                formData.co_executors = formData.co_executors.map(item => {
                    return item.id
                })
            }
            formData.create_orders = state.create_orders
            formData.tp_goods = buildTpGoodsPayload(state.orderList.results)

            if(formData.oper_type === 0) {
                axios.post('/crm/orders/create_from_cart/', formData)
                    .then(({data}) => {
                        resolve({
                            ...data,
                            oper_type: 0
                        })
                    })
                    .catch((error) => { reject(error) })
            } else {
                axios.put(`/crm/orders/${formData.id}/`, formData)
                    .then(({data}) => {
                        resolve({
                            ...data,
                            oper_type: 40
                        })
                        eventBus.$emit('update_order_table', {
                            ...data,
                            oper_type: 40
                        })
                    })
                    .catch((error) => { reject(error) })
                    .finally(() => {
                        commit('CLEAR_CREATE_ORDERS')
                        commit('CLEAR_NEW_ORDER_DISPLAY_LIST')
                    })
            }
        })
    },
    createOrder({ commit, state }, form) {
        return new Promise((resolve, reject) => {
            let formData = JSON.parse(JSON.stringify(form))
            if(formData.logistic_manager?.id)
                formData.logistic_manager = formData.logistic_manager.id
            if(formData.operator?.id)
                formData.operator = formData.operator.id
            if(formData.cash_pay_recipient?.id)
                formData.cash_pay_recipient = formData.cash_pay_recipient.id
            if(formData.co_executors?.length) {
                formData.co_executors = formData.co_executors.map(item => {
                    return item.id
                })
            }
            formData.tp_goods = buildTpGoodsPayload(state.orderList.results)

            axios.post('/crm/orders/create_from_cart/', formData)
                .then(({data}) => {
                    if (data) {
                        if (form.oper_type > 0) {
                            if(form.customer_contract) {
                                commit('CLEAR_ORDER_CREATE_PAGE')
                            } else {
                                commit('CLEAR_CART_ALL')
                                commit('SET_CART_VISIBLE', false)
                                commit('products/ALL_PRODUCT_CART_REMOVED', null, {root: true})
                            }
                            commit('SET_CREATE_VISIBLE', false)
                            commit('SET_FIRST_LOADING', true)
                        }
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addCrmOrderLine({ commit }, { waList, id, formData }) {
        return new Promise(async (resolve, reject) => {
            try {
                const created = []
                for (const key in waList) {
                    if(!waList[key]) {
                        continue
                    }
                    const warehouseForm = formData?.[key] ? { ...formData[key] } : {}
                    const { data } = await axios.post('/crm/orders/build_order_line/', {
                        goods: id,
                        quantity: typeof waList[key] === 'boolean' ? 1 : waList[key],
                        warehouse: key,
                        ...warehouseForm
                    })
                    commit('PUSH_ORDER_GOODS', data)
                    created.push(data)
                }
                resolve(created)
            } catch(e) {
                reject(e)
            }
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
    addShoppingCartWarehouse({ commit }, {waList, id, formData, draft}) {
        return new Promise(async (resolve, reject) => {
            try {
                let quantity = 0
                let is_draft = false

                if(draft)
                    is_draft = draft

                for (const key in waList) {

                    let warehouseForm = {}

                    if(formData?.[key]) {
                        warehouseForm = {
                            ...formData[key]
                        }
                    }

                    const queryData = {
                        goods: id,
                        quantity: typeof waList[key] === 'boolean' ? 0 : waList[key],
                        warehouse: key,
                        is_draft,
                        ...warehouseForm
                    }
                    if(waList[key]) {
                        quantity = quantity + (typeof waList[key] === 'boolean' ? 1 : waList[key])
                        const {data} = await axios.post('/crm/shopping_cart/', queryData)
                        if(!is_draft) {
                            commit('products/PRODUCT_CART_ADDED', queryData, { root: true })
                            commit('products/DETAIL_PRODUCT_CART_ADDED', queryData, { root: true })
                        } else {
                            commit('PUSH_ORDER_GOODS', data)
                        }
                    }
                }
                if(!is_draft && quantity)
                    commit('CART_COUNT_IN', quantity)

                resolve(true)
            } catch(e) {
                reject(e)
            }
        })
    },
    addShoppingCart({ commit, rootState }, queryData) {
        return new Promise((resolve, reject) => {
            axios.post('/crm/shopping_cart/', queryData)
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

            axios.get('/crm/shopping_cart/', { params })
                .then(({ data }) => {
                    commit('SET_ORDER_LIST_RELOAD', data)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getOrderGoodsList({ commit, state }, { id }) {
        return new Promise((resolve, reject) => {
            commit('SET_ORDER_PAGE', state.orderPage+1)

            let params = {
                page: state.orderPage,
                page_size: 'all'
            }

            if(state.currentContract) {
                params.contract = state.currentContract
            }

            axios.get(`/crm/orders/${id}/goods/`, { params })
                .then(({ data }) => {
                    if(state.firstOrderLoading)
                        commit('SET_ORDER_FIRST_LOADING', false)

                    if(!data?.results?.length && state.orderPage === 1) {
                        commit('SET_ORDER_EMPTY', true)
                    } else {

                        const results = data.results.map(item => {
                            return {
                                ...item,
                                // custom_price: item.amount,
                                custom_price: item.price,
                                amount_no_discount: null,
                                goods_for_print: item.goods_for_print || item
                            }
                        })

                        if(!state.orderList?.amount)
                            commit('ORDER_SET_AMOUNT', data.amount)

                        if(state.orderEmpty)
                            commit('SET_ORDER_EMPTY', false)

                        if(!state.orderCurrency)
                            commit('SET_ORDER_CURRENCY', data.currency)

                        commit('SET_ORDER_NEXT', data.next)
                        commit('CONCAT_ORDER_LIST', results)
                        commit('SET_ORDER_LIST_COUNT', data.count)
                    }
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

            axios.get('/crm/shopping_cart/', { params })
                .then(({ data }) => {
                    if(state.firstOrderLoading)
                        commit('SET_ORDER_FIRST_LOADING', false)

                    if(!data?.results?.length && state.orderPage === 1) {
                        commit('SET_ORDER_EMPTY', true)
                        commit('SET_ORDER_NEXT', false)
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

            axios.get('/crm/shopping_cart/', { params })
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
            axios.get('/crm/shopping_cart/count/')
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
            axios.delete(`/crm/shopping_cart/${goods.id}/`)
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
            axios.post('/crm/shopping_cart/clear/')
                .then(() => {
                    commit('CLEAR_CART_ALL')
                    commit('products/ALL_PRODUCT_CART_REMOVED', null, { root: true })
                    resolve(true)
                })
                .catch((error) => { reject(error) })
        })
    },
    cartCountUpdate({ commit }, { goods, quantity, formData }) {
        return new Promise((resolve, reject) => {
            let data = {}

            if(formData) {
                data = formData
            }

            axios.put(`/crm/shopping_cart/${goods.id}/`, {
                quantity,
                ...data
            })
                .then(({data}) => {
                    if(data.goods_for_print) {
                        commit('ORDER_CART_UPDATE_FIELD', {
                            goods: goods, 
                            fieldKey: 'goods_for_print', 
                            fieldValue: data.goods_for_print
                        })
                    }
                    resolve(true)
                })
                .catch((error) => { reject(error) })
        })
    },
    getCartSummary({ commit, state }) {
        return new Promise((resolve, reject) => {
            commit('SET_CART_AMOUNT_LOADER', true)
            axios.get('/crm/shopping_cart/amount/')
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
