export default () => ({
    cartCount: 0,
    cartVisible: false,
    cartList: {
        count: 0,
        next: true,
        amount: 0,
        results: []
    },
    cartPage: 0,
    firstLoading: true,
    cartEmpty: false,
    cartCurrency: null,
    cartAmountLoader: false,
    createVisible: false,
    orderList: {
        count: 0,
        next: true,
        amount: 0,
        results: []
    },
    orderPage: 0,
    orderCurrency: null,
    firstOrderLoading: true,
    orderEmpty: false,
    currentContract: null,
    warehouseFormInfo: null,
    warehouseFormLoading: false,
    orderTableInfo: null,
    orderActions: null,
    createEmptyOrder: false,
    isEmptyOrder: false,
    newOrderWarehouse: '',
    newOrderTPGoods: [],
    create_orders: {},
    newOrderDisplayList: [],
    deliveryWarehouses: []
})