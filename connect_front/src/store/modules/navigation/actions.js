import axios from '@/config/axios'
import { errorHandler } from '@/utils/index.js'

export default {
    /*init({commit}, {data}) {
        commit('SET_MENU', data)
        commit('PAGE_ROUTE_GENERATE', data)
        commit('FORM_ROUTE_GENERATE', data)
    },*/
    getRouteActions({ commit, state }, { name }) {
        return new Promise((resolve, reject) => {
            if(state.routeActions?.[name] || name === 'dashboard') {
                resolve(true)
            } else {
                let qName = name
                if(qName === 'projects-list')
                    qName = 'projects'
                axios.get('/app_info/routes/meta/', {
                    params: {
                        name: qName
                    }
                })
                    .then(({ data }) => {
                        commit('SET_ROUTE_ACTIONS', {
                            data,
                            name
                        })
                        resolve(true)
                    })
                    .catch(e => {
                        console.log(e, 'getRouteActions')
                        reject(e)
                    })
            }
        })
    },
    routeInit({ commit, state, rootState }) {
        return new Promise((resolve, reject) => {
            if(state.routerList?.length)
                resolve(true)
            else {
                const params = {
                    ver: 'alt'
                }
                if(!rootState.isMobile) {
                    params.view = 'desktop'
                }
                axios.get('/app_info/routes/', {params})
                    .then(({ data }) => {
                        if(data)
                            commit('SET_ROUTER_INIT', {data, rootState})

                        resolve(true)
                    })
                    .catch(e => {
                        console.log(e, 'route init')
                        reject(e)
                    })
            }
        })
    },
    changeMobileRouteList({state}) {
        return new Promise((resolve, reject) => {
            const newRouteOrder = {}
            state.routerMobile.forEach((route, index) => {
                newRouteOrder[route.name] = {
                    isFooter: route.isFooter,
                    isShow: route.isShow,
                    isShowMobile: route.isShowMobile,
                    mobileOrder: index,
                    descOrder: route.descOrder
                }
            })

            axios.post('/app_info/routes/custom/', newRouteOrder)
                .then(({ data }) => {
                    resolve(true)
                })
                .catch(error => {
                    errorHandler({error})
                    reject(e)
                })
        })
    },
    changeRouterList({ commit }, value) {
        return new Promise((resolve, reject) => {
            const newRouteOrder = {}
            value.forEach((route, index) => {
                newRouteOrder[route.name] = {
                    isFooter: route.isFooter,
                    isShow: route.isShow,
                    isShowMobile: route.isShowMobile,
                    mobileOrder: route.mobileOrder,
                    descOrder: index
                }
            })

            commit('CHANGE_ROUTER_LIST', value)
            axios.post('/app_info/routes/custom/', newRouteOrder)
                .then(({ data }) => {
                    resolve(true)
                })
                .catch(error => {
                    errorHandler({error})
                    reject(e)
                })
        })
    },
    getRouterInfo({ commit }, { name }) {
        return new Promise((resolve, reject) => {
            const params = {
                name
            }
            if(params.name === 'projects-list' || params.name === 'projects-gant')
                params.name = 'projects'
            axios.get('app_info/routes/meta/', { params }).
                then(({ data }) => {
                    if(Object.keys(data)?.length) {
                        commit('SET_ROUTE_INFO', data)
                    }
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    }
}