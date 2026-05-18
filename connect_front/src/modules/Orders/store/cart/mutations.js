import Vue from 'vue'
export default {
    SET_CREATE_EMPTY_ORDER(state, value) {
        state.createEmptyOrder = value
    },
    SET_IS_EMPTY_ORDER(state, value) {
        state.isEmptyOrder = value
    },
    SET_ORDER_ACTIONS(state, value) {
        state.orderActions = value
    },
    SET_ORDER_TABLE_INFO(state, value) {
        state.orderTableInfo = value
    },
    SET_WAREHOUSE_LOADING(state, value) {
        state.warehouseFormLoading = value
    },
    SET_WAREHOUSE_INFO(state, value) {
        state.warehouseFormInfo = value
    },
    SET_CART_COUNT(state, value) {
        state.cartCount = value
    },
    CART_COUNT_IN(state, value) {
        state.cartCount = state.cartCount + Number(value)
    },
    CART_COUN_M(state, value) {
        state.cartCount = state.cartCount - Number(value)
    },
    SET_CART_VISIBLE(state, value) {
        state.cartVisible = value
    },
    SET_CART_NEXT(state, value) {
        state.cartList.next = value
    },
    SET_ORDER_NEXT(state, value) {
        state.orderList.next = value
    },
    CONCAT_CART_LIST(state, value) {
        state.cartList.results = state.cartList.results.concat(value)
    },
    CONCAT_ORDER_LIST(state, value) {
        state.orderList.results = state.orderList.results.concat(value)
    },
    SET_CART_EMPTY(state, value) {
        state.cartEmpty = value
    },
    SET_CART_PAGE(state, value) {
        state.cartPage = value
    },
    SET_ORDER_PAGE(state, value) {
        state.orderPage = value
    },
    CLEAR_STORE(state) {
        state.cartList = {
            count: 0,
            next: true,
            amount: 0,
            results: []
        },
        state.cartPage = 0
        state.cartEmpty = false
    },
    CART_SET_AMOUNT(state, value) {
        state.cartList.amount = value
    },
    ORDER_SET_AMOUNT(state, value) {
        state.orderList.amount = value
    },
    DELETE_ITEM_CARD(state, id) {
        const index = state.cartList.results.findIndex(f => f.id === id)
        if(index !== -1) {
            state.cartList.results.splice(index, 1)
        }
    },
    SET_FIRST_LOADING(state, value) {
        state.firstLoading = value
    },
    SET_CART_LIST_COUNT(state, value) {
        state.cartList.count = value
    },
    SET_ORDER_LIST_COUNT(state, value) {
        state.orderList.count = value
    },
    SET_CART_LIST_COUNT_M(state) {
        state.cartList.count = state.cartList.count - 1
    },
    CHECK_CART_EMPTY(state) {
        if(state.cartList.count === 0)
            state.cartEmpty = true
    },
    CLEAR_CART_ALL(state) {
        state.cartEmpty = false
        state.cartCount = 0
        state.cartPage = 0
        state.cartList = {
            count: 0,
            next: true,
            amount: 0,
            results: []
        }
    },
    SET_CART_CURRENCY(state, value) {
        state.cartCurrency = value
    },
    SET_ORDER_CURRENCY(state, value) {
        state.orderCurrency = value
    },
    SET_CART_AMOUNT_LOADER(state, value) {
        state.cartAmountLoader = value
    },
    SET_CREATE_VISIBLE(state, value) {
        state.createVisible = value
    },
    CLEAR_ORDER_CREATE_PAGE(state) {
        state.orderCurrency = null
        state.orderPage = 0
        state.orderList = {
            count: 0,
            next: true,
            amount: 0,
            results: []
        }
        state.firstOrderLoading = true
        state.orderEmpty = false
    },
    SET_ORDER_LIST_RELOAD(state, value) {
        state.orderList = value
    },
    SET_ORDER_SOURCE_LINES(state, value) {
        const lines = Array.isArray(value) ? value : []
        state.orderList = {
            count: lines.length,
            next: false,
            amount: lines.reduce((sum, item) => {
                const price = Number(item.custom_price || item.price || item.goods?.price || 0)
                const quantity = Number(item.quantity || 0)
                return sum + (price * quantity)
            }, 0),
            results: lines
        }
        state.orderPage = 1
        state.orderEmpty = !lines.length
        state.firstOrderLoading = false
        if(lines[0]?.goods?.currency) {
            state.orderCurrency = lines[0].goods.currency
        }
    },
    SET_ORDER_GOOD_LIST_ONLY_RELOAD(state, value) {
        state.orderList.results = value
    },
    SET_ORDER_GOOD_LIST_ONLY_RELOAD_NO_CALCULATE(state, value) {
        if(state.orderList.results?.length) {
            state.orderList.results.forEach((item, index) => {
                const find = value.find(f => f.goods.id === item.goods.id)
                if(find) {
                    Vue.set(state.orderList.results, index, {
                        ...find,
                        id: item.id,
                        warehouse: find.warehouse,
                        amount: find.amount,
                        amount_no_discount: find.amount_no_discount
                    })
                }
            })
        } else
            state.orderList.results = value
    },
    SET_ORDER_FIRST_LOADING(state, value) {
        state.firstOrderLoading = value
    },
    SET_ORDER_EMPTY(state, value) {
        state.orderEmpty = value
    },
    SET_CURRENT_CONTRCAT(state, value) {
        state.currentContract = value
    },
    CHANGE_CART_ITEM_PRICE(state, {id, price, type}) {
        if(state?.[type]?.results?.length) {
            const index = state[type].results.findIndex(f => f.id === id)
            if(index !== -1) {
                Vue.set(state[type].results[index], 'custom_price', price)
            }
        }
    },
    DELETE_ORDER_GOODS(state, item) {
        if(state.orderList.results.length) {
            const index = state.orderList.results.findIndex(f => f.id === item.id)
            if(index !== -1)
                state.orderList.results.splice(index, 1)
        }
    },
    PUSH_ORDER_GOODS(state, value) {
        if(value) {
            state.orderList.results.push({
                ...value,
                in_cart: true
            })
            state.orderList.count += 1
        }
    },
    ORDER_GOODS_UPDATE_COUNT(state, { quantity, goods }) {
        const index = state.orderList.results.findIndex(f => f.id === goods.id)
        if(index !== -1) {
            Vue.set(state.orderList.results[index], 'quantity', quantity)
        }
    },
    ORDER_CART_UPDATE_FIELD(state, { goods, fieldKey, fieldValue }) {
        const index = state.orderList.results.findIndex(f => f.id === goods.id)
        if(index !== -1) {
            Vue.set(state.orderList.results[index], fieldKey, fieldValue)
        }
    },
    SET_NEW_ORDER_WAREHOUSE(state, value) {
        state.newOrderWarehouse = value
    },
    SET_NEW_ORDER_TPGOODG(state, value) {
        state.newOrderTPGoods = value
    },
    ADD_TO_CREATE_ORDERS(state, {uid, tpgoodsList}) {
        state.create_orders[uid] = {
            "warehouse": state.newOrderWarehouse,
            "tp_goods": tpgoodsList
        }
        state.newOrderTPGoods = []
        state.newOrderWarehouse = ''
    },
    CLEAR_CREATE_ORDERS(state) {
        state.create_orders = {}
        state.newOrderTPGoods = []
        state.newOrderWarehouse = ''
    },
    CLEAR_NEW_ORDER_DISPLAY_LIST(state) {
        state.newOrderDisplayList = []
    },
    RESET_NEW_ORDER(state, {tpGoods, uid}) {
        state.orderList.results.push(...tpGoods)
        delete state.create_orders[uid]
    },
    PUSH_TO_NEW_ORDER_DISPLAY_LIST(state, {displayText, tpGoods, uid}) {
        state.newOrderDisplayList.push({
            displayText: displayText,
            tpGoods: tpGoods,
            uid: uid
        })
    },
    REMOVE_ITEM_FROM_ORDER_DISPLAY_LIST(state, index) {
        if(index !== -1) {
            state.newOrderDisplayList.splice(index, 1)
        }
    },
    CLEAR_ORDER_DISPLAY_LIST(state) {
        state.newOrderDisplayList = []
    },
    SET_WAREHOUSE(state, warehouse) {
        state.orderList.results.forEach((tpGoods) => {
            tpGoods.warehouse = warehouse
        })
    },
    SET_DELIVERY_WAREHOUSES(state, deliveryWarehouses) {
        state.deliveryWarehouses = deliveryWarehouses
    },
    RESET_DELIVERY_WAREHOUSES(state) {
        state.deliveryWarehouses = []
    },
    SET_GOODG_FOR_PRINT_TO_ALL(state, value) {
        state.orderList.results.forEach((tpGood) => {
            tpGood.goods_for_print = value
        })
    }
}
