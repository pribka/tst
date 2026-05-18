import axios from '@/config/axios'
import { setData, getById, updateById } from '../utils/indexedDB.js'
import Vue from 'vue'
// import { message } from 'ant-design-vue'

const key = 'update_dashboard'

export default {
    getCategory({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.categoryList.length) {
                resolve(state.categoryList)
            } else {
                axios.get('/widgets/widget_categories/')
                    .then(({ data }) => {
                        if (data) {
                            commit('SET_CATEGORY_LIST', data)
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    getWidgets({ commit, state, rootState }) {
        return new Promise((resolve, reject) => {
            commit('SET_WIDGETS_PAGE', state.page + 1)

            const params = {
                page: state.page,
                page_size: 15,
                category: null
            }

            if(rootState.isMobile) {
                params.is_mobile = true
            } else {
                params.is_desktop = true
            }

            if(state.activeCategory && state.activeCategory !== 'all')
                params.category = state.activeCategory
            if(state.searchWidget.length)
                params.name = state.searchWidget

            axios.get('/widgets/widgets/', {params})
                .then(({ data }) => {
                    if (data) {
                        if(data) {
                            commit('SET_WIDGETS_COUNT', data.count)
                            commit('SET_WIDGETS_NEXT', data.next)
                        }

                        if(state.page === 1 && !data?.results?.length)
                            commit('SET_WIDGETS_EMPTY', true)
    
                        if(data?.results?.length)
                            commit('CONCAT_WIDGETS_NEXT', data.results)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getActiveWidgets({ commit, state, dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get(`/widgets/user_desktops/${state.active}/`, {
                params: {
                    is_desktop: true
                }
            })
                .then(({ data }) => {
                    if (data) {
                        commit('SET_ACTIVE_WIDGETS', data)
                        commit('SET_READY', true)
                    }
                    resolve(data)
                })
                .catch((error) => { 
                    if(error?.detail && error.detail.includes("Страница не найдена.")) {
                        if(state.dashboardList.length) {
                            commit('SET_ACTIVE', state.dashboardList[0].id)
                            dispatch('getActiveWidgets')
                        }
                    }
                    reject(error) 
                })
        })
    },
    getActiveWidgetsMobile({ commit, state, dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get(`/widgets/user_desktops/${state.active}/`, {
                params: {
                    is_mobile: true
                }
            })
                .then(({ data }) => {
                    if (data) {
                        commit('SET_ACTIVE_WIDGETS_MOBILE', data)
                        commit('SET_READY', true)
                    }
                    resolve(data)
                })
                .catch((error) => { 
                    if(error?.detail && error.detail.includes("Страница не найдена.")) {
                        if(state.dashboardList.length) {
                            commit('SET_ACTIVE', state.dashboardList[0].id)
                            dispatch('getActiveWidgetsMobile')
                        }
                    }
                    reject(error) 
                })
        })
    },
    getDashboardList({ commit }) {
        return new Promise((resolve, reject) => {
            axios.get('/widgets/user_desktops/')
                .then(({ data }) => {
                    if (data?.length) {
                        commit('SET_DASHBOARD_LIST', data)
                        const activeDashboard = localStorage.getItem('active_dashboard')
                        if(activeDashboard) {
                            commit('SET_ACTIVE', activeDashboard)
                        } else {
                            commit('SET_ACTIVE', data[0].id)
                        }
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    deleteDashboard({ commit }, { id }) {
        return new Promise((resolve, reject) => {
            axios.delete(`/widgets/user_desktops/${id}/`)
                .then(({ data }) => {
                    commit('SPLICE_DASHBOARD_LIST', id)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addDashboard({ commit }, { form }) {
        return new Promise((resolve, reject) => {
            axios.post('/widgets/user_desktops/', form)
                .then(({ data }) => {
                    if(data) {
                        commit('ADD_DASHBOARD_LIST', data)
                        commit('SET_ACTIVE', data.id)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updateDashboard({ commit }, { form }) {
        return new Promise((resolve, reject) => {
            axios.put(`/widgets/user_desktops/${form.id}/`, form)
                .then(({ data }) => {
                    if(data) {
                        commit('UPDATE_DASHBOARD_LIST', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updateDashboardWidgets({ commit, state }, { widgets }) {
        return new Promise((resolve, reject) => {
            const widgetsList = widgets.map((item, i) => {
                return {
                    x: item.x,
                    y: item.y,
                    h: item.h,
                    w: item.w,
                    static: item.static,
                    widget_catalog_id: null,
                    i,
                    id: item.id,
                    is_desktop: item.is_desktop,
                    is_mobile: item.is_mobile,
                    mobile_index: item.mobile_index
                }
            })
            axios.put(`/widgets/user_desktops/${state.active}/location/`, {
                widgets: widgetsList
            })
                .then(({ data }) => {
                    if(data?.widgets?.length) {
                        commit('SET_ACTIVE_WIDGETS', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updatedState({ commit, dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get('/widgets/user_desktops/')
                .then(async ({ data }) => {
                    if (data?.length) {
                        commit('SET_DASHBOARD_LIST', data)
                        await dispatch('getActiveWidgets')
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updatedStateMobile({ commit, dispatch }) {
        return new Promise((resolve, reject) => {
            axios.get('/widgets/user_desktops/')
                .then(async ({ data }) => {
                    if (data?.length) {
                        commit('SET_DASHBOARD_LIST', data)
                        await dispatch('getActiveWidgetsMobile')
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    deleteActiveWidget({ commit, state, dispatch }, { id }) {
        return new Promise(async(resolve, reject) => {
            if(state.widgets?.length) {
                commit('DELETE_ACTIVE_WIDGET', id)
                await dispatch('updateDashboardWidgets', {
                    widgets: state.widgets
                })
                resolve()
            } else {
                reject()
            }
        })
    },
    pinActiveWidget({ commit, state, dispatch }, { id }) {
        return new Promise(async(resolve, reject) => {
            if(state.widgets?.length) {
                commit('PIN_ACTIVE_WIDGET', id)
                await dispatch('updateDashboardWidgets', {
                    widgets: state.widgets
                })
                resolve()
            } else {
                reject()
            }
        })
    },
    updateDashboardPosition({ commit, state }, value) {
        return new Promise(async(resolve, reject) => {
            // message.loading({content: 'Обновление', key})
            commit('SET_DASHBOARD_LIST', value)
            const desktops = state.dashboardList.map(item => {
                return item.id
            })
            axios.put('/widgets/user_desktops/sort_list/', { desktops })
                .then(({ data }) => {
                    if (data?.desktops?.length) {
                        // message.success({content: 'Обновлено', key})
                    }
                    resolve(data)
                })
                .catch((error) => { 
                    // message.error({content: 'Ошибка обновления', key})
                    reject(error)
                })
        })
    },
    addWidgetButton({ commit, state }, { widget }) {
        return new Promise((resolve, reject) => {
            commit('PUSH_WIDGETS', widget)
            const widgetsList = state.widgets.map((item, i) => {
                if(item.widget?.added) {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        widget_catalog_id: item.widget.id,
                        id: null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.is_desktop || item.widget.is_desktop,
                        is_mobile: item.is_mobile || item.widget.is_mobile
                    }
                } else {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        id: item.id || null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.is_desktop || item.widget.is_desktop,
                        is_mobile: item.is_mobile || item.widget.is_mobile
                    }
                }
            })
            if(widgetsList?.length) {
                axios.put(`/widgets/user_desktops/${state.active}/location/`, {
                    widgets: widgetsList
                })
                    .then(({ data }) => {
                        if(data?.widgets?.length) {
                            commit('SET_ACTIVE_WIDGETS', data)
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
            
            resolve(true)
        })
    },
    addWidgetMobile({ commit, state }, { widget }) {
        return new Promise((resolve, reject) => {
            commit('PUSH_WIDGETS_MOBILE', {value: widget})
            const widgetsList = state.widgets.map((item, i) => {
                if(item.widget?.added) {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        widget_catalog_id: item.widget.id,
                        id: null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.widget.is_desktop,
                        is_mobile: item.widget.is_mobile,
                        mobile_index: item.mobile_index
                    }
                } else {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        id: item.id || null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.widget.is_desktop,
                        is_mobile: item.widget.is_mobile,
                        mobile_index: item.mobile_index
                    }
                }
            })
            if(widgetsList?.length) {
                axios.put(`/widgets/user_desktops/${state.active}/location/`, {
                    widgets: widgetsList
                })
                    .then(({ data }) => {
                        if(data?.widgets?.length) {
                            commit('SET_ACTIVE_WIDGETS_MOBILE', data)
                            window.scrollTo({ left: 0, top: document.body.scrollHeight + 1000 || document.documentElement.scrollHeight + 1000, behavior: "smooth" })
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
            
            resolve(true)
        })
    },
    addWidgetDrag({ commit, state }) {
        return new Promise(async(resolve, reject) => {
            // message.loading({content: 'Обновление', key})
            const widgetsList = state.widgets.map((item, i) => {
                if(item.added) {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        widget_catalog_id: item.widget.id,
                        id: null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.is_desktop,
                        is_mobile: item.is_mobile
                    }
                } else {
                    return {
                        x: item.x,
                        y: item.y,
                        h: item.h,
                        w: item.w,
                        static: item.static || false,
                        i,
                        id: item.id || null,
                        maxH: item.maxH,
                        maxW: item.maxW,
                        minH: item.minH,
                        minW: item.minW,
                        is_desktop: item.is_desktop,
                        is_mobile: item.is_mobile
                    }
                }
            })

            if(widgetsList?.length) {
                axios.put(`/widgets/user_desktops/${state.active}/location/`, {
                    widgets: widgetsList
                })
                    .then(({ data }) => {
                        if(data?.widgets?.length) {
                            commit('SET_ACTIVE_WIDGETS', data)
                            // message.success({content: 'Обновлено', key})
                        }
                        resolve(data)
                    })
                    .catch((error) => { 
                        // message.error({content: 'Ошибка обновления', key})
                        reject(error) 
                    })
            } else {
                // message.success({content: 'Обновлено', key})
                resolve(true)
            }
        })
    },
    moveActiveWidget({ state, commit, dispatch }, { widget, type }) {
        return new Promise(async(resolve, reject) => {
            const index = state.widgets.findIndex(f => f.id === widget.id)
            if(index !== -1) {
                if(type === 'down') {
                    const newIndex = widget.mobile_index + 1,
                        find = [...state.widgets].find(f => f.mobile_index === newIndex)
                    commit('UPDATE_ACTIVE_WIDGET', {
                        widgetId: widget.id, 
                        key: 'mobile_index', 
                        value: newIndex
                    })
                    if(find) {
                        commit('UPDATE_ACTIVE_WIDGET', {
                            widgetId: find.id, 
                            key: 'mobile_index', 
                            value: find.mobile_index - 1
                        })
                    }
                }
                if(type === 'up') {
                    const newIndex = widget.mobile_index - 1,
                        find = [...state.widgets].find(f => f.mobile_index === newIndex)
                    commit('UPDATE_ACTIVE_WIDGET', {
                        widgetId: widget.id, 
                        key: 'mobile_index', 
                        value: newIndex
                    })
                    if(find) {
                        commit('UPDATE_ACTIVE_WIDGET', {
                            widgetId: find.id, 
                            key: 'mobile_index', 
                            value: find.mobile_index + 1
                        })
                    }
                }
                await dispatch('updateDashboardWidgets', {
                    widgets: state.widgets
                })
                resolve()
            } else {
                reject()
            }
        })
    },
    deleteMobileActiveWidget({ commit, state, dispatch }, { id }) {
        return new Promise(async(resolve, reject) => {
            if(state.widgets?.length) {
                commit('DELETE_ACTIVE_MOBILE_WIDGET', id)
                await dispatch('updateDashboardWidgets', {
                    widgets: state.widgets
                })
                resolve()
            } else {
                reject()
            }
        })
    },
}