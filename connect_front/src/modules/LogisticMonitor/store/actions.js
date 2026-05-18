import axios from '@/config/axios'
import defAxios from 'axios'
export default {
    getConfig({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.config)
                resolve(state.config)

            else
                axios.get('/crm/logistic_monitor/page_info/')
                    .then(({data}) => {
                        if(data) {
                            commit('SET_CONFIG', data)
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
        })
    },
    getDeliveryPoints({ commit }, { task, showPoint }) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/${task.id}/delivery_points/`)
                .then(({data}) => {
                    commit('SET_ACTIVE_ROUTING', {
                        data,
                        task
                    })
                    if(showPoint) {
                        commit('SET_TASK_POINT_VISIBLE', {
                            task
                        })
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getLogisticTask({ commit }, filters = {}) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()

            commit('SET_TASK_LIST_LOADER', true)
            commit('SET_TASK_LIST_REQUEST', { cancel: axiosSource.cancel })

            axios.get('/tasks/task/list/', {
                cancelToken: axiosSource.token,
                params: {
                    task_type: 'logistic',
                    page_name: 'page_list_logistic_task.TaskModel',
                    page_size: 'all',
                    filters: {
                        ...filters,
                        // status_id__in: ['new', 'in_work']
                    }
                }
            })
                .then(({data}) => {
                    commit('SET_TASK_LIST_LOADER', false)
                    commit('SET_TASK_LIST_REQUEST', null)
                    commit('SET_LOGISTIC_TASK', data.results)
                    commit('SET_MAP_TASKS_SHOW', true)

                    if(!data.results.length) {
                        commit('SET_TASK_EMPTY', true)
                    }

                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getLogisticUserTask({ commit }, { user }) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()
            const filters = {
                operator: user.id,
                status__in: ["new", "in_work"]
            }

            commit('SET_USER_TASK_REQUEST', {
                value: { cancel: axiosSource.cancel },
                id: user.id
            })
            axios.get('/tasks/task/list/', {
                cancelToken: axiosSource.token,
                params: {
                    task_type: 'logistic',
                    page_name: `page_list_logistic_task.TaskModel_user_tab`,
                    page_size: 'all',
                    filters
                }
            })
                .then(({data}) => {
                    commit('SET_USER_TASK_REQUEST', {
                        value: null,
                        id: user.id
                    })
                    commit('CONCAT_LOGISTIC_TASK', {
                        results: data.results,
                        user
                    })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    async updateRouting({ commit, state }) {
        try {
            if(state.logisticTask.length) {
                const filteredTask = state.logisticTask.filter(f => f.edited)
                if(filteredTask?.length) {
                    for(const index in filteredTask) {
                        const task = filteredTask[index]
                        const routing = filteredTask[index].routing

                        let taskChange = {
                            add: [],
                            edit: [],
                            delete: []
                        }

                        const added = filteredTask[index].routing?.length && routing.filter(f => f.added),
                            moved = routing.filter(f => f.moved)
                        let removed = []

                        if(state.removePoint?.[task.id]) {
                            removed = state.removePoint[task.id].map(item => {
                                return {
                                    id: item
                                }
                            })
                        }

                        if(added.length) {
                            const newOrder = added.filter(f => f.newOrder)
                            let orderPoint = []

                            if(newOrder?.length) {
                                newOrder.forEach(point => {
                                    const find = orderPoint.find(f => f.order === point.orderId)
                                    if(!find) {
                                        orderPoint.push({
                                            order: point.orderId,
                                            delivery_point: point.end_point?.id || null,
                                            start_delivery_point: point.start_point?.id || null,
                                            start_front_id: point.startId || null,
                                            end_front_id: point.endId || null
                                        })
                                    }
                                })
                            }

                            taskChange.add = [
                                ...orderPoint
                            ]
                        }
                        if(removed.length) {
                            taskChange.delete = removed
                        }

                        if(taskChange.add?.length || taskChange.delete?.length) {
                            const { data } = await axios.post(`tasks/${task.id}/delivery_points/update/`, taskChange)
                            if(data) {
                                commit('UPDATE_TASK_POINT', {
                                    task,
                                    data
                                })
                                if(taskChange.delete?.length) {
                                    commit('SET_TASK_REMOVE', { task })
                                }

                                const tIndex = state.logisticTask.findIndex(f => f.id === task.id)
                                if(tIndex !== -1) {
                                    const newRouting = state.logisticTask[tIndex].routing
                                    await axios.put(`tasks/task/${task.id}/sort_delivery_points/`, {
                                        delivery_points: newRouting.map(item => item.id)
                                    })
                                }
                            }
                        } else {
                            for(const index in filteredTask) {
                                const task = filteredTask[index]
                                const routing = filteredTask[index].routing
                                await axios.put(`tasks/task/${task.id}/sort_delivery_points/`, {
                                    delivery_points: routing.map(item => item.id)
                                })
                            }
                        }
                    }

                    commit('CLEAR_ORDER_REMOVED')
                    commit('POINT_SAVE_DEFAULT')
                }
            }

            return {
                status: true
            }
        } catch(error) {
            console.log(error, 'updateRouting')
            return {
                status: false,
                error
            }
        }
    },
    getUserList({ commit }, { page_name }) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()

            commit('SET_USER_LIST_LOADER', true)
            commit('SET_USER_LIST_REQUEST', { cancel: axiosSource.cancel })

            axios.get('/tasks/drivers/', {
                cancelToken: axiosSource.token,
                params: {
                    page_size: 'all',
                    page_name
                }
            })
                .then(({data}) => {
                    commit('SET_USER_LIST_LOADER', false)
                    commit('SET_USER_LIST_REQUEST', null)
                    commit('SET_LOGISTIC_USERS', data.results)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getUserPoint({ commit }, { user }) {
        return new Promise((resolve, reject) => {
            commit('SET_USER_POINT_VISIBLE', {
                user
            })
            resolve(true)
        })
    },
    createUserTask({ state, dispatch }, { user }) {
        try {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)
            if(index !== -1) {
                if(state.logisticUsers[index]?.routing?.length) {
                    const newOrder = state.logisticUsers[index].routing.filter(f => f.added)
                    if(newOrder?.length) {
                        let orderPoint = []
                        newOrder.forEach(point => {
                            const find = orderPoint.find(f => f.id === point.orderId)
                            if(!find) {

                                const start = newOrder.find(f => f.orderId === point.orderId && f.is_start)
                                const end = newOrder.find(f => f.orderId === point.orderId && !f.is_start)

                                orderPoint.push({
                                    id: point.orderId,
                                    delivery_point: {
                                        id: point.end_point?.id || null,
                                        sort: end?.index || 0
                                    },
                                    start_delivery_point: {
                                        id: point.start_point?.id || null,
                                        sort: start?.index || 0
                                    }
                                })
                            }
                        }) 

                        if(orderPoint?.length) {
                            const taskData = {
                                orders: orderPoint,
                                task_type: "logistic",
                                create_handler: user.id,
                                operator: {
                                    ...user
                                }
                            }

                            dispatch('task/sidebarOpen', taskData, {root:true})
                        }
                    }
                }
            }
        } catch(e) {
            console.log(e)
        }
    },
    getOrderList({ commit, state }, { page_name }) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()

            commit('SET_ORDER_LIST_REQUEST', { cancel: axiosSource.cancel })
            commit('SET_ORDER_PAGE', state.orderPage + 1)

            axios.get('/crm/orders/', {
                cancelToken: axiosSource.token,
                params: {
                    page_size: 15,
                    page_name,
                    page: state.orderPage,
                    ordering: 'delivery_date_plan_gte,number_1c'
                }
            })
                .then(({data}) => {
                    if(data) {
                        if(!data.results.length && state.orderPage === 1) {
                            commit('SET_ORDER_LIST_EMPTY', true)
                        }

                        commit('SET_ORDER_NEXT', data.next)
                        commit('CONCAT_ORDER_LIST', data.results)
                    }
                    commit('SET_ORDER_LIST_REQUEST', null)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getMapClients({ commit }, { lat__gte, lat__lte, lon__gte, lon__lte }) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()

            commit('SET_MAP_CLIENT_REQUEST', { cancel: axiosSource.cancel })

            axios.get('/catalogs/contractors/delivery_points/', {
                cancelToken: axiosSource.token,
                params: {
                    lat__gte,
                    lat__lte,
                    lon__gte,
                    lon__lte
                }
            })
                .then(({data}) => {
                    if(data) {
                        commit('SET_MAP_CLIENT', data)
                    }
                    commit('SET_MAP_CLIENT_REQUEST', null)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getMapOrderAndWarehouse({ commit, state }, { lat__gte, lat__lte, lon__gte, lon__lte }) {
        return new Promise((resolve, reject) => {
            const axiosSource = defAxios.CancelToken.source()

            commit('SET_MAP_OW_REQUEST', { cancel: axiosSource.cancel })

            axios.get('/crm/orders/delivery_points/', {
                cancelToken: axiosSource.token,
                params: {
                    lat__gte,
                    lat__lte,
                    lon__gte,
                    lon__lte
                }
            })
                .then(({data}) => {
                    if(data) {
                        for(let point of data.orders) {
                            for(let i=0; i < point.orders.length; i++) {
                                if(state?.notDisplayOrders?.listID.includes(point.orders[i].id)) {
                                    point.orders.splice(i, 1)
                                    i--
                                }
                            }
                        }
                        commit('SET_MAP_OW', data)
                    }
                    commit('SET_MAP_OW_REQUEST', null)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    }
}