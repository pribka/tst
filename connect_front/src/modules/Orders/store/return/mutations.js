import Vue from 'vue'
export default {
    // Cart
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
        state.cartEmpty = true
        state.cartCount = 0
        state.cartList = {
            count: 0,
            next: false,
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
    SET_ORDER_GOOD_LIST_ONLY_RELOAD(state, value) {
        state.orderList.results = value
    },
    SET_ORDER_GOOD_LIST_ONLY_RELOAD_NO_CALCULATE(state, value) {
        if(state.orderList.results?.length) {
            state.orderList.results.forEach((item, index) => {
                const find = value.find(f => f.goods.id === item.goods.id)
                if(find) {
                    delete find.warehouse
                    Vue.set(state.orderList.results, index, {
                        ...find,
                        warehouse: item.warehouse,
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

    // ReturnCart
    SET_RETURN_CART_VISIBLE(state, value) {
        state.returnCartVisible = value
    },
}