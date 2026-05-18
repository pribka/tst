import Vue from 'vue'
export default {
    SET_GRID_LAYOUT(state, value) {
        state.gridlayout = value
    },
    SET_SEARCH_WIDGET(state, value) {
        state.searchWidget = value
    },
    PUSH_WIDGETS(state, value) {
        state.widgets.push({
            x: (state.widgets.length * 4) % 12,
            y: state.widgets.length + 12,
            w: value.w,
            h: value.h,
            i: state.widgets.length + 1,
            widget: value,
            maxH: value.maxH,
            maxW: value.maxW,
            minH: value.minH,
            minW: value.minW
        })
    },
    PUSH_WIDGETS_MOBILE(state, {value}) {
        state.widgets.push({
            x: (state.widgets.length * 4) % 12,
            y: state.widgets.length + 12,
            w: value.w,
            h: value.h,
            i: state.widgets.length + 1,
            widget: value,
            maxH: value.maxH,
            maxW: value.maxW,
            minH: value.minH,
            minW: value.minW,
            mobile_index: state.widgets.length,
            id: state.widgets.length ? `${state.widgets.length + 1}` : '0'
        })
    },
    UPDATE_ACTIVE_WIDGET(state, { widgetId, key, value }) {
        const index = state.widgets.findIndex(f => f.id === widgetId)
        if(index !== -1) {
            Vue.set(state.widgets[index], key, value)
        }
    },
    PUSH_WIDGETS_ANY(state, value) {
        state.widgets.push(value)
    },
    SET_CATEGORY_LIST(state, value) {
        state.categoryList = value
    },
    SET_WIDGETS_PAGE(state, value) {
        state.page = value
    },
    SET_WIDGETS_COUNT(state, value) {
        state.widgetList.count = value
    },
    SET_WIDGETS_NEXT(state, value) {
        state.widgetList.next = value
    },
    CONCAT_WIDGETS_NEXT(state, value) {
        state.widgetList.results = state.widgetList.results.concat(value)
    },
    SET_WIDGETS_EMPTY(state, value) {
        state.widgetsEmpty = value
    },
    CLEAR_WIDGETS(state) {
        state.widgetList = {
            results: [],
            next: true,
            count: 0
        }
        state.widgetsEmpty = false
        state.page = 0
    },
    SET_ACTIVE_CATEGORY(state, value) {
        state.activeCategory = value
    },
    SET_ACTIVE_WIDGETS_DEF(state, data) {
        state.widgets = data
    },
    SET_ACTIVE_WIDGETS(state, data) {
        if(data.widgets?.length) {
            state.widgets = data.widgets.map((item, index) => {
                return {
                    ...item,
                    static: item.static || false,
                    i: index,
                    showMobile: item.widget.is_mobile,
                    showDesktop: item.widget.is_desktop
                }
            })
        } else {
            state.widgets = []
        }
    },
    SET_ACTIVE_WIDGETS_MOBILE(state, data) {
        if(data.widgets?.length) {
            state.widgets = data.widgets.map((item, index) => {
                return {
                    ...item,
                    static: item.static || false,
                    i: index,
                    mobile_index: item.mobile_index,
                    showMobile: item.widget.is_mobile,
                    showDesktop: item.widget.is_desktop
                }
            })
        } else {
            state.widgets = []
        }
    },
    SET_DASHBOARD_LIST(state, value) {
        state.dashboardList = value
    },
    SPLICE_DASHBOARD_LIST(state, id) {
        const index = state.dashboardList.findIndex(f => f.id === id)
        if(index !== -1) {
            Vue.delete(state.dashboardList, index)
        }
    },
    ADD_DASHBOARD_LIST(state, value) {
        state.dashboardList.push(value)
    },
    UPDATE_DASHBOARD_LIST(state, value) {
        const index = state.dashboardList.findIndex(f => f.id === value.id)
        if(index !== -1) {
            Vue.set(state.dashboardList, index, value)
        }
    },
    SET_ACTIVE(state, value) {
        state.active = value
        if(typeof localStorage !== 'undefined') {
            localStorage.setItem('active_dashboard', value)
        }
    },
    SET_READY(state, value) {
        state.ready =value
    },
    DELETE_ACTIVE_WIDGET(state, id) {
        const index = state.widgets.findIndex(f => f.id === id)
        if(index !== -1) {
            Vue.delete(state.widgets, index)
        }
    },
    DELETE_ACTIVE_MOBILE_WIDGET(state, id) {
        const index = state.widgets.findIndex(f => f.id === id)
        if(index !== -1) {
            Vue.delete(state.widgets, index)
        }
        if(state.widgets.length) {
            const sortedList = [...state.widgets].sort((a, b) => a.mobile_index - b.mobile_index)
            sortedList.forEach((item, i) => {
                const index2 = state.widgets.findIndex(f => f.id === item.id)
                if(index2 !== -1) {
                    Vue.set(state.widgets[index2], 'mobile_index', i)
                }
            })
        }
    },
    PIN_ACTIVE_WIDGET(state, id) {
        const index = state.widgets.findIndex(f => f.id === id)
        if(index !== -1) {
            Vue.set(state.widgets[index], 'static', !state.widgets[index].static)
        }
    },
    SET_CATALOG_VISIBLE(state, value) {
        state.catalogVisible = value
    }
}
