import Vue from 'vue'
import eventBus from '@/utils/eventBus'
import { v4 as uuidv4 } from 'uuid'
export default {
    SET_MAP_BORDERS(state, borders) {
        Vue.set(state, 'mapBorders', borders)
    },
    SET_LOCATED_TASKS_PAGE(state, page) {
        state.locatedTasksPage = page
    },
    CONCAT_LOCATED_TASKS(state, data) {
        state.locatedTasks = state.locatedTasks.concat(data.results)
        state.locatedTasksNext = data.next
    },

    SET_CONFIG(state, value) {
        state.config = value
    },
    CLEAR_ALL_STATE(state) {
        state.userPointVisible = {}
        state.selectRouting = {}
        state.logisticTask = []
        state.logisticTaskNext = true
        state.logisticTaskPage = 0
        state.taskPointVisible = {}
        state.taskPointLoader = {}
        state.userPointLoader = {}
        state.taskOpen = false
        state.removePoint = {}
        state.listEdit = false
        state.logisticUsers = []
        state.activeTab = 'task'
        state.showOrderSidebar = true
        state.orderList = []
        state.orderPage = 0
        state.orderNext = true
        state.orderListEmpty = false
        state.orderListMoved = []
        state.taskEmpty = false
        state.mapClients = []
        state.mapClientRequest = null
    },
    UPDATE_TASK_SOCKET(state, value) {
        const index = state.locatedTasks.findIndex(f => f.id === value.id)
        if(index !== -1) {
            Vue.set(state.locatedTasks, index, {
                ...state.locatedTasks[index],
                ...value
            })
        }
    },
    SET_TASK_HAS_ORDER(state, index) {
        Vue.set(state.logisticTask[index], 'has_order', true)
    },
    SET_ACTIVE_TAB(state, value) {
        state.activeTab = value
    },
    SET_MAP_CLIENT_REQUEST(state, value) {
        state.mapClientRequest = value
    },
    SET_MAP_OW_REQUEST(state, value) {
        state.mapOWRequest = value
    },
    SET_MAP_LOCATED_TASK(state, value) {
        state.mapLocatedTasks = value
    },
    SET_MAP_CLIENT(state, value) {
        state.mapClients = value
    },
    SET_MAP_OW(state, value) {
        state.mapOW = value
    },
    SET_MAP_OW_ORDER_WAREHOUSE(state, {pointIndex, orderIndex, warehouse}) {
        if(state.mapOW?.orders[pointIndex]?.orders[orderIndex]?.warehouse)
            state.mapOW.orders[pointIndex].orders[orderIndex].warehouse = warehouse
    },
    SET_LOADER_OW_ON(state) {
        state.loaderOW = true 
    },
    SET_LOADER_OW_OFF(state) {
        state.loaderOW = false 
    },
    SET_MAP_CLIENTS_SHOW(state, value) {
        state.mapClientsShow = value
        localStorage.setItem('monitor_clients', value)
    },
    SET_MAP_OW_SHOW(state, value) {
        state.mapOWShow = value
        localStorage.setItem('monitor_ow', value)
    },
    SET_MAP_TASKS_SHOW(state, value) {
        state.mapTasksShow = value
        localStorage.setItem('monitor_tasks', value)
    },
    SET_MAP_FULL(state, value) {
        state.mapFull = value
    },

    // Task
    SET_TASK_EMPTY(state, value) {
        state.taskEmpty = value
    },
    SET_TASK_FILTER_BY_KEY(state, {value, key}) {
        state.taskFilters[key] = value
    },
    SET_TASK_FILTER(state, value) {
        state.taskFilters = value
    },
    POINT_SAVE_DEFAULT(state) {
        state.listEdit = false
    },
    FILTER_HANDLER(state) {
        state.userPointVisible = {}
        state.taskPointVisible = {}
        state.taskPointLoader = {}
        state.userPointLoader = {}
        state.removePoint = {}
        state.listEdit = false
        state.taskOpen = false
        state.taskEmpty = false
    },
    CLEAR_STATE_TYPE(state, type) {
        if (type === 'task') {
            state.userPointLoader = {}
            state.logisticUsers = []
            state.userPointVisible = {}
        }
        
        state.taskPointLoader = {}
        state.logisticTask = []
        state.taskPointVisible = {}
        state.selectRouting = {}
        state.removePoint = {}
        state.listEdit = false
        state.taskEmpty = false
    },
    SET_TASK_REMOVE(state, { task }) {
        if(state.removePoint?.[task.id]?.length)
            Vue.set(state.removePoint, task.id, [])
    },
    SET_ACTIVE_ROUTING(state, {data, task}) {
        if(state.logisticTask?.length && data?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'routing', data.map((route, index) => {
                    return {
                        ...route,
                        index
                    }
                }))
                Vue.set(state.logisticTask[index], 'oldRouting', data.map((route, index) => {
                    return {
                        ...route,
                        index
                    }
                }))
                Vue.set(state.removePoint, task.id, [])
                eventBus.$emit('mapReinitPosition')
            }
        }
        if(!data?.length) {
            Vue.set(state.removePoint, task.id, [])
        }
    },
    RETURN_DRAGGED_ROUTING(state, { task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                if(state.logisticTask?.[index]?.routing?.length) {
                    const routing = JSON.parse(JSON.stringify(state.logisticTask[index].routing))
                    const newRouting = JSON.parse(JSON.stringify(state.logisticTask[index].routing)).filter(f => f.newOrder)
                    if(newRouting?.length) {
                        newRouting.forEach(point => {
                            const rIndex = routing.findIndex(f => f.id === point.id)
                            if(rIndex !== -1) {
                                this.commit('monitor/ORDER_RETURN_REMOVED', routing[rIndex])
                            }
                        })
                    }
                }
            }
        }
    },
    DELETE_ACTIVE_ROUTING(state, { task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'routing', [])
                Vue.set(state.logisticTask[index], 'oldRouting', [])

                if(!state.removePoint?.[task.id]?.length) {
                    Vue.delete(state.removePoint, task.id)
                }

                eventBus.$emit('mapReinitPosition')
            }
        }
    },
    SET_LOCATED_TASK(state, value) {
        state.locatedTaskNext = value
    },
    SET_LOCATED_TASK_PAGE(state, value) {
        state.locatedTaskPage = value
    },
    CONCAT_LOGISTIC_TASK(state, { user, results }) {
        if(state.userPointVisible?.[user.id]) {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)

            if(index !== -1)
                Vue.set(state.logisticUsers[index], 'tasks', results)

            const tasks = results.map(item => {
                return {
                    ...item,
                    routingLine: true,
                    showInMap: true,
                    showPopup: true,
                    routing: [],
                    userFilter: user.id
                }
            })

            if(tasks?.length)
                state.logisticTask = state.logisticTask.concat(tasks)
        }
    },
    SET_LOCATED_TASK(state, data) {
        state.locatedTask = data.map(item => {
            return {
                ...item,
                routingLine: true,
                showInMap: true,
                showPopup: true,
                routing: []
            }
        })
    },
    SET_VISIBILITY_LOGISTIC_TASK(state, value) {
        state.logisticTask.forEach(task => {
            Vue.set(task, 'showInMap', value)
        })
    },
    CHANGE_TASK_ROUTING(state, { task, routing }) {
        if(state.logisticTask?.length) {
            let routingData = JSON.parse(JSON.stringify(routing))

            if(routingData.filter(f => f.counter)?.length) {
                routingData.forEach((item, index) => {
                    const startId = uuidv4()
                    const endId = uuidv4()

                    if(item.start_delivery_point) {
                        Vue.set(routingData, index, {
                            ...item.start_delivery_point,
                            delivery_date: null,
                            duration: null,
                            is_start: true,
                            added: true,
                            pointOrder: item,
                            orderId: item.id,
                            newOrder: true,
                            end_point: item.delivery_point || null,
                            start_point: item.start_delivery_point,
                            id: startId,
                            startId,
                            endId,
                            orders: [
                                {
                                    ...item
                                }
                            ]
                        })
                    }
                    if(item.delivery_point) {
                        const delivery_point = {
                            ...item.delivery_point,
                            delivery_date: null,
                            duration: null,
                            is_start: false,
                            added: true,
                            pointOrder: item,
                            orderId: item.id,
                            newOrder: true,
                            end_point: item.delivery_point,
                            start_point: item.start_delivery_point || null,
                            id: endId,
                            startId,
                            endId,
                            orders: [
                                {
                                    ...item
                                }
                            ]
                        }
                        routingData.splice(index + 1, 0, delivery_point)
                    }
                })
            }

            const tIndex = state.logisticTask.findIndex(f => f.id === task.id)
            if(tIndex !== -1) {
                routingData = routingData.map((route, index) => {
                    return {
                        ...route,
                        index
                    }
                })
                Vue.set(state.logisticTask[tIndex], 'routing', routingData)
                this.commit('monitor/SET_TASK_CHANGE', {
                    task
                })

                eventBus.$emit('routingReinit')
            }
        }
    },
    CLEAR_TASK_POINT_VISIBLE(state) {
        Vue.set(state, 'taskPointVisible', {})
    },
    CLEAR_TASK_ALL_ROUTING(state) {
        if(state.logisticTask.length) {
            state.logisticTask = state.logisticTask.map(item => {
                return {
                    ...item,
                    routing: []
                }
            })
        }
    },
    SET_TASK_POINT_VISIBLE(state, { task }) {
        Vue.set(state.taskPointVisible, task.id, true)
    },
    SET_TASK_POINT_UNVISIBLE(state, { task }) {
        Vue.set(state.taskPointVisible, task.id, false)
    },
    SET_POPUP_MARKER_LOADER(state, { task, value }) {
        Vue.set(state.taskPointLoader, task.id, value)
    },
    CHANGE_ROUTING_LINE(state, { task, value }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'routingLine', value)
                eventBus.$emit('routingReinit')
            }
        }
    },
    CHANGE_TASK_IN_MAP(state, { task, value }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'showInMap', value)
                eventBus.$emit('mapReinitPosition')
            }
            if(!value) {
                let tasksOnMap = false
                state.logisticTask.forEach(task => {
                    tasksOnMap = tasksOnMap || task.showInMap
                })
                if(!tasksOnMap) {
                    this.commit('geoviewer/SET_MAP_TASKS_SHOW', false)
                }
            }
        }
    },
    CHANGE_TASK_POPUP(state, { task, value }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'showPopup', value)
            }
        }
    },
    SET_TASK_OPEN(state, value) {
        state.taskOpen = value
    },
    ROUTER_MOVED(state, { router, task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                if(state.logisticTask?.[index]?.routing?.length) {
                    const routing = state.logisticTask[index].routing,
                        rIndex = routing.findIndex(f => f.id === router.id)
                    if(rIndex !== -1) {
                        Vue.set(routing[rIndex], 'moved', true)
                        this.commit('monitor/SET_TASK_CHANGE', {
                            task
                        })
                    }

                    const routingMoved = routing.filter(f => f.moved)
                    if(routingMoved?.length) {
                        const oldRouting = state.logisticTask[index].oldRouting || []
                        routingMoved.forEach(point => {
                            const uIndex = routing.findIndex(f => f.id === point.id)
                            if(uIndex !== -1 && oldRouting?.length && oldRouting[uIndex]?.id === point.id) {
                                Vue.delete(routing[uIndex], 'moved')
                            }
                        })
                    }
                }
            }
        }
    },
    ROUTER_ADDED(state, { router, task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                if(state.logisticTask?.[index]?.routing?.length) {
                    const routing = state.logisticTask[index].routing
                    const rIndex = routing.findIndex(f => f.id === router.id)
                    if(rIndex !== -1) {
                        Vue.set(routing[rIndex], 'added', true)

                        if(state.removePoint[task.id]?.length) {
                            const find = state.removePoint[task.id].find(f => f === router.id)
                            if(find) {
                                const oldRouting = state.logisticTask[index].oldRouting || []
                                Vue.delete(routing[rIndex], 'added')

                                if(oldRouting?.length && oldRouting[rIndex]?.id === routing[rIndex]?.id) {
                                    
                                } else {
                                    Vue.set(routing[rIndex], 'moved', true)
                                }
                            }
                        }

                        this.commit('monitor/SET_TASK_CHANGE', {
                            task
                        })
                    }
                }
            }
        }
        if(state.removePoint?.[task.id]) {
            let points = state.removePoint[task.id]

            const index = points.findIndex(f => f === router.id)
            if(index !== -1) {
                points.splice(index, 1)
                Vue.set(state.removePoint, task.id, points)
            }
        }
    },
    ROUTER_REMOVED(state, { router, task }) {
        if(state.removePoint?.[task.id]) {
            let points = state.removePoint[task.id]

            const find = points.find(f => f === router.id)

            if(!find && !router.added)
                points.push(router.id)

            Vue.set(state.removePoint, task.id, points)

            this.commit('monitor/SET_TASK_CHANGE', {
                task
            })
        }
    },
    ROUTER_DELETED(state, { selectPoint, task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                if(state.logisticTask?.[index]?.routing?.length) {
                    const routing = state.logisticTask[index].routing

                    if(state.removePoint?.[task.id]) {
                        let points = state.removePoint[task.id]
            
                        selectPoint.forEach(point => {
                            const find = points.find(f => f === point)
                            const findRoute = routing.find(f => f.id === point)

                            if(!find && !findRoute?.added) {
                                points.push(point)
                            }
                        })
            
                        Vue.set(state.removePoint, task.id, points)
                    }

                    selectPoint.forEach(point => {
                        const rIndex = routing.findIndex(f => f.id === point)
                        if(rIndex !== -1) {
                            this.commit('monitor/ORDER_RETURN_REMOVED', routing[rIndex])
                            Vue.delete(routing, rIndex)
                        }
                    })
                }

                this.commit('monitor/SET_TASK_CHANGE', {
                    task
                })
            }
        }

        eventBus.$emit('routingReinit')
    },
    SET_LIST_EDIT(state, value) {
        state.listEdit = value
    },
    SET_TASK_CHANGE(state, { task }) {
        if(state.logisticTask?.length) {
            const index = state.logisticTask.findIndex(f => f.id === task.id)
            if(index !== -1) {
                Vue.set(state.logisticTask[index], 'edited', true)
            }
        }
    },
    CHECK_ALL_EDITING(state) {
        if(state.logisticTask?.length) {
            const filteredTask = state.logisticTask.filter(f => f.edited)
            if(filteredTask?.length) {
                let editedCheck = []
                filteredTask.forEach(task => {
                    const oldRouting = task.oldRouting,
                        routing = task.routing

                    if(routing?.length) {
                        // console.log(differenceBy(routing, oldRouting, 'moved'), 'differenceBy')
                    }
                })
            }
        }
    },
    SET_MAP_SHOW_ROUTING(state, value) {
        state.mapShowRouting = value
    },
    UPDATE_TASK_POINT(state, { task, data }) {
        const index = state.logisticTask.findIndex(f => f.id === task.id)
        if(index !== -1) {

            if(data.task?.next_delivery_point)
                Vue.set(state.logisticTask[index], 'next_delivery_point', data.task.next_delivery_point)

            Vue.set(state.logisticTask[index], 'has_order', data.task.has_order ? true : false)

            if(state.logisticTask[index].edited)
                Vue.delete(state.logisticTask[index], 'edited')

            const routing = state.logisticTask[index].routing

            if(routing?.length && data.delivery_points?.length) {
                routing.forEach((point, pIndex) => {
                    const find = data.delivery_points.find(f => f.front_id === point.id)
                    if(find) {
                        Vue.set(state.logisticTask[index].routing[pIndex], 'id', find.id)
                    }

                    if(state.logisticTask[index].routing[pIndex].added)
                        Vue.delete(state.logisticTask[index].routing[pIndex], 'added')
                        
                    if(state.logisticTask[index].routing[pIndex].edited)
                        Vue.delete(state.logisticTask[index].routing[pIndex], 'edited')
                })
            }
        }
    },
    CHECK_UPDATE_IN_CLOSE(state) {
        let open = []

        for(const key in state.taskPointVisible) {
            if(state.taskPointVisible[key])
                open.push(key)
        }

        if(!open.length) {
            state.removePoint = {}
            state.listEdit = false
        }
    },
    SET_TASK_LIST_REQUEST(state, value) {
        state.taskListRequest = value
    },
    SET_TASK_LIST_LOADER(state, value) {
        state.taskListLoader = value
    },

    // USER
    SET_LOGISTIC_USERS(state, data) {
        state.logisticUsers = data.map(item => {
            return {
                ...item,
                edited: false,
                routingLine: true,
                routing: []
            }
        })
    },
    SET_USER_POINT_VISIBLE(state, { user }) {
        Vue.set(state.userPointVisible, user.id, true)
    },
    SET_USER_POINT_UNVISIBLE(state, { user }) {
        if(state.userTaskRequest?.[user.id]) {
            state.userTaskRequest[user.id].cancel()
            this.commit('monitor/SET_USER_TASK_REQUEST', {
                value: null,
                id: user.id
            })
        }

        Vue.set(state.userPointVisible, user.id, false)
    },
    SET_USER_POINT_LOADER(state, { user, value }) {
        Vue.set(state.userPointLoader, user.id, value)
    },
    DELETE_ACTIVE_USER_ROUTING(state, { user }) {
        if(state.logisticUsers?.length) {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)
            if(index !== -1) {
                Vue.set(state.logisticUsers[index], 'routing', [])

                if(state.logisticUsers[index]?.tasks?.length) {
                    state.logisticUsers[index].tasks.forEach(task => {
                        const tIndex = state.logisticTask.findIndex(f => f.id === task.id)
                        if(!tIndex !== -1)
                            Vue.delete(state.logisticTask, tIndex)
                    })
                }
                Vue.delete(state.logisticUsers[index], 'tasks')

                eventBus.$emit('mapReinitPosition')
            }
        }
    },
    CHANGE_USER_ROUTING(state, { user, routing }) {
        if(state.logisticUsers?.length) {
            let routingData = JSON.parse(JSON.stringify(routing))

            if(routingData.filter(f => f.counter)?.length) {
                routingData.forEach((item, index) => {
                    const startId = uuidv4()
                    const endId = uuidv4()

                    if(item.start_delivery_point) {
                        Vue.set(routingData, index, {
                            ...item.start_delivery_point,
                            delivery_date: null,
                            duration: null,
                            is_start: true,
                            added: true,
                            pointOrder: item,
                            orderId: item.id,
                            newOrder: true,
                            end_point: item.delivery_point || null,
                            start_point: item.start_delivery_point,
                            id: startId,
                            startId,
                            endId,
                            orders: [
                                {
                                    ...item
                                }
                            ]
                        })
                    }
                    if(item.delivery_point) {
                        const delivery_point = {
                            ...item.delivery_point,
                            delivery_date: null,
                            duration: null,
                            is_start: false,
                            added: true,
                            pointOrder: item,
                            orderId: item.id,
                            newOrder: true,
                            end_point: item.delivery_point,
                            start_point: item.start_delivery_point || null,
                            id: endId,
                            startId,
                            endId,
                            orders: [
                                {
                                    ...item
                                }
                            ]
                        }
                        routingData.splice(index + 1, 0, delivery_point)
                    }
                })
            }

            const tIndex = state.logisticUsers.findIndex(f => f.id === user.id)
            if(tIndex !== -1) {
                routingData = routingData.map((route, index) => {
                    return {
                        ...route,
                        index
                    }
                })
                Vue.set(state.logisticUsers[tIndex], 'routing', routingData)
                this.commit('monitor/SET_USER_CHANGE', {
                    user
                })

                eventBus.$emit('routingReinit')
            }
        }
    },
    SET_USER_CHANGE(state, { user }) {
        if(state.logisticUsers?.length) {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)
            if(index !== -1) {
                Vue.set(state.logisticUsers[index], 'edited', true)
            }
        }
    },
    ROUTER_USER_DELETED(state, { selectPoint, user }) {
        if(state.logisticUsers?.length) {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)
            if(index !== -1) {
                if(state.logisticUsers?.[index]?.routing?.length) {
                    const routing = state.logisticUsers[index].routing

                    if(state.removePoint?.[user.id]) {
                        let points = state.removePoint[user.id]
            
                        selectPoint.forEach(point => {
                            const find = points.find(f => f === point)
                            const findRoute = routing.find(f => f.id === point)

                            if(!find && !findRoute?.added) {
                                points.push(point)
                            }
                        })
            
                        Vue.set(state.removePoint, user.id, points)
                    }

                    selectPoint.forEach(point => {
                        const rIndex = routing.findIndex(f => f.id === point)
                        if(rIndex !== -1) {
                            this.commit('monitor/ORDER_RETURN_REMOVED', routing[rIndex])
                            Vue.delete(routing, rIndex)
                        }
                    })

                    if(!state.logisticUsers[index].routing.length)
                        Vue.set(state.logisticUsers[index], 'edited', false)
                }
            }
        }

        eventBus.$emit('routingReinit')
    },
    SET_USER_TASK_REQUEST(state, { value, id }) {
        if(value) {
            Vue.set(state.userTaskRequest, id, value)
        } else {
            Vue.delete(state.userTaskRequest, id)
        }
    },
    SET_USER_LIST_LOADER(state, value) {
        state.userListLoader = value
    },
    SET_USER_LIST_REQUEST(state, value) {
        state.userListRequest = value
    },
    CLEAR_USER_ADDED(state, { user, data }) {
        const index = state.logisticUsers.findIndex(f => f.id === user.id)
        if(index !== -1) {
            Vue.set(state.logisticUsers[index], 'edited', false)
            Vue.set(state.logisticUsers[index], 'routing', [])

            const lTask = {
                ...data,
                routingLine: true,
                showInMap: true,
                showPopup: true,
                userFilter: user.id,
                routing: []
            }

            state.logisticUsers[index].tasks.push(lTask)
            state.logisticTask.unshift(lTask)
        }
    },

    // Orders
    SET_ORDER_PAGE(state, value) {
        state.orderPage = value
    },
    SET_ORDER_NEXT(state, value) {
        state.orderNext = value
    },
    CONCAT_ORDER_LIST(state, value) {
        const filter = value.filter(fil => {
            const find = state.orderListMoved.find(f => f.id === fil.id)
            return find ? false : true
        })

        state.orderList = state.orderList.concat(filter)
    },
    ORDER_CLEAR(state) {
        state.orderList = []
        state.orderPage = 0
        state.orderNext = true
        state.orderListEmpty = false
    },
    ORDER_CLEAR_ALL(state) {
        state.orderList = []
        state.orderPage = 0
        state.orderNext = true
        state.orderListEmpty = false
        state.orderListMoved = []
    },
    SET_ORDER_LIST_REQUEST(state, value) {
        state.orderListRequest = value
    },
    UPDATE_ORDER_LIST(state, value) {
        state.orderList = value
    },
    ADD_ORDER_REMOVED(state, value) {
        state.orderListMoved.unshift(value)
    },
    SET_ORDER_LIST_EMPTY(state, value) {
        state.orderListEmpty = value
    },
    CLEAR_ORDER_REMOVED(state) {
        state.orderListMoved = []
    },
    ORDER_RETURN_REMOVED(state, points) {
        if(state.orderListMoved?.length) {
            const index = state.orderListMoved.findIndex(f => f.id === points.orderId)
            if(index !== -1) {
                const order = JSON.parse(JSON.stringify(state.orderListMoved[index]))
                Vue.delete(state.orderListMoved, index)
                state.orderList.splice(order.oldIndex, 0, order)
            }
        }
    },
    ORDER_RETURN_DEFAULT(state) {
        if(state.orderListMoved?.length) {
            state.orderListMoved.forEach((order, index) => {
                state.orderList.splice(index, 0, order)
                Vue.delete(state.orderListMoved, index)
            })
        }
    },
    SET_ORDERS_FILTER_BY_KEY(state, {value, key}) {
        state.orderFilters[key] = value
    },
    SET_ORDERS_FILTER(state, value) {
        state.orderFilters = value
    },
    SET_ORDER_SIDEBAR(state, value) {
        state.showOrderSidebar = value
    },
    DELETE_ORDER_MOVED_BY_ID(state, value) {
        if(value?.formData?.orders?.length) {
            value.formData.orders.forEach(order => {
                const index = state.orderListMoved.findIndex(f => f.id === order.id)
                if(index !== -1)
                    state.orderListMoved.splice(index, 1)
            })
        }
    },
    SET_USER_LOCATIONS(state, value) {
        const loc = {
            ...value,
            disconnected: false,
            location: [value.geo[0].coords.latitude, value.geo[0].coords.longitude],
            speed: value.geo[0].coords.speed,
            sdate: new Date()
        }

        if(state.userLocation.length) {
            const index = state.userLocation.findIndex(f => f.user.uuid === loc.user.uuid)
            if(index !== -1) {
                Vue.set(state.userLocation, index, loc)
            } else {
                state.userLocation.push(loc)
            }
        } else
            state.userLocation.push(loc)
    },
    CLEAR_USER_LOCATION(state) {
        state.userLocation = []
    },
    SET_USER_LOCATION_DISCONNECT(state, value) {
        if(state.userLocation.length) {
            const index = state.userLocation.findIndex(f => f.user.uuid === value.user.uuid)
            if(index !== -1) {
                const loc = {
                    ...state.userLocation[index],
                    disconnected: true,
                    disconnectedDate: new Date()
                }
                Vue.set(state.userLocation, index, loc)
            }
        }
    },
    RETURN_DRAGGED_USER_ROUTING(state, { user }) {
        if(state.logisticUsers?.length) {
            const index = state.logisticUsers.findIndex(f => f.id === user.id)
            if(index !== -1) {
                if(state.logisticUsers?.[index]?.routing?.length) {
                    const routing = JSON.parse(JSON.stringify(state.logisticUsers[index].routing))
                    const newRouting = JSON.parse(JSON.stringify(state.logisticUsers[index].routing)).filter(f => f.newOrder)

                    if(newRouting?.length) {
                        newRouting.forEach(point => {
                            const rIndex = routing.findIndex(f => f.id === point.id)
                            if(rIndex !== -1) {
                                this.commit('monitor/ORDER_RETURN_REMOVED', routing[rIndex])
                            }
                        })
                    }
                }
            }
        }
    },
    CHANGE_WAREHOUSE_IN_ORDER_DATA(state, {orderID, warehouse}) {
        const order = state.orderList.find(f => f.id === orderID)
        if(order)
            order.warehouse = warehouse
    }
}