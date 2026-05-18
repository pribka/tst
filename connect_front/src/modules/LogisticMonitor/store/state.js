const getSidebarStore = () => {
    if(typeof JSON.parse(localStorage.getItem('monitor_sidebar')) === 'boolean')
        return JSON.parse(localStorage.getItem('monitor_sidebar'))

    return true
}

const getClientsShow = () => {
    if(typeof JSON.parse(localStorage.getItem('monitor_clients')) === 'boolean')
        return JSON.parse(localStorage.getItem('monitor_clients'))

    return false
}

const getOWShow = () => {
    if(typeof JSON.parse(localStorage.getItem('monitor_ow')) === 'boolean')
        return JSON.parse(localStorage.getItem('monitor_ow'))

    return false
}

const getTasksShow = () => {
    if(typeof JSON.parse(localStorage.getItem('monitor_tasks')) === 'boolean')
        return JSON.parse(localStorage.getItem('monitor_tasts'))

    return false
}

export default () => ({
    selectRouting: {},
    logisticTask: [],
    logisticTaskNext: true,
    logisticTaskPage: 0,
    taskPointVisible: {},
    taskPointLoader: {},
    taskEmpty: false,
    taskOpen: false,
    removePoint: {},
    listEdit: false,
    mapShowRouting: true,
    logisticUsers: [],
    userPointVisible: {},
    userPointLoader: {},
    activeTab: 'task',
    userTaskRequest: {},
    taskListRequest: null,
    taskListLoader: false,
    userListLoader: false,
    userListRequest: null,
    showOrderSidebar: getSidebarStore(),
    orderFilters: {
        pickup: false,
        without_logistic_task_filter:false,
        task_delivery_point__isnull: false,
        is_daily_created_filter: false,
        is_daily_delivery_filter: false
    },
    taskFilters: {
        is_daily_filter: false,
        without_order_filter: false
    },
    config: null,
    orderList: [],
    orderPage: 0,
    orderNext: true,
    orderListRequest: null,
    orderListMoved: [],
    orderListEmpty: false,
    mapClientRequest: null,
    mapOWRequest: null,
    mapClients: [],
    mapOW: null,
    mapClientsShow: getClientsShow(),
    mapFull: false,
    userLocation: [],
    mapOWShow: getOWShow(),
    mapTasksShow: getTasksShow(),
    loaderOW: false,
    notDisplayOrders: {
        listID: [],
    },
})