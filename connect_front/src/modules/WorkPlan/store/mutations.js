import Vue from 'vue'
import { task_type, page_size, taskModel } from '../utils.js'
import moment from 'moment'

const listModel = {
    loading: false,
    empty: false,
    task_type: task_type,
    page_size: page_size,
    page: 1,
    next: true,
    count: 0,
    results: [],
    search: ""
}

export default {
    INIT_WORK_PLAN_BY_KEY(state, { storeKey }) {
        Vue.set(state.activeTab, storeKey, 'tasks')
        Vue.set(state.day_statistics, storeKey, {
            loading: false,
            data: null
        })
        Vue.set(state.reportSettings, storeKey, null)
        Vue.set(state.ai_intents, storeKey, {
            loading: false,
            data: null
        })
        Vue.set(state.user, storeKey, [])
        Vue.set(state.tabsCount, storeKey, null)
        Vue.set(state.mainDate, storeKey, [moment().clone().startOf('day'), moment().clone().endOf('day')])
        Vue.set(state.ticketRole, storeKey, null)
        Vue.set(state.taskSearch, storeKey, {
            search: ""
        })
        Vue.set(state.taskList, storeKey, {...taskModel})
        Vue.set(state.taskFocusList, storeKey, {...taskModel})
        Vue.set(state.taskOtherList, storeKey, {...taskModel})
        Vue.set(state.eventList, storeKey, {
            loading: false,
            empty: false,
            task_type: task_type,
            page_size: page_size,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        })
        Vue.set(state.dayPulseList, storeKey, {
            loading: false,
            empty: false,
            page_size: 15,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        })
        Vue.set(state.meetingList, storeKey, {
            loading: false,
            empty: false,
            task_type: task_type,
            page_size: page_size,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        })
        Vue.set(state.ticketList, storeKey, {
            loading: false,
            empty: false,
            task_type: task_type,
            page_size: page_size,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        })
        Vue.set(state.ticketOtherList, storeKey, {
            loading: false,
            empty: false,
            task_type: task_type,
            page_size: page_size,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        })
    },
    SET_TABS_COUNT(state, { storeKey, data }) {
        Vue.set(state.tabsCount, storeKey, data)
    },
    CHANGE_ACTIVE_TAB(state, { storeKey, value }) {
        Vue.set(state.activeTab, storeKey, value)
    },
    SET_AI_INTENTS(state, { storeKey, data }) {
        Vue.set(state.ai_intents[storeKey], 'data', data)
    },
    STAT_AI_LOADING(state, { storeKey, value }) {
        Vue.set(state.ai_intents[storeKey], 'loading', value)
    },
    SET_STAT(state, { storeKey, data }) {
        Vue.set(state.day_statistics[storeKey], 'data', data)
    },
    STAT_LOADING(state, { storeKey, value }) {
        Vue.set(state.day_statistics[storeKey], 'loading', value)
    },
    CHANGE_FIELD(state, {field, value, storeKey}) {
        Vue.set(state[field], storeKey, value)
    },
    SET_EMPLOYEES_DATE_RANGE(state, value) {
        Vue.set(state, 'employeesDateRange', value)
    },
    SET_CONSOLIDATION_FILTERS(state, { scope = null, relatedObject = null } = {}) {
        Vue.set(state, 'consolidationFilters', {
            scope,
            relatedObject
        })
    },
    SET_CONSOLIDATION_KEY_RESULTS_LOADING(state, value) {
        Vue.set(state.consolidationKeyResults, 'loading', value)
    },
    SET_CONSOLIDATION_KEY_RESULTS(state, data) {
        Vue.set(state.consolidationKeyResults, 'data', data)
    },
    SET_CONSOLIDATION_DASHBOARD_LOADING(state, value) {
        Vue.set(state.consolidationDashboard, 'loading', value)
    },
    SET_CONSOLIDATION_DASHBOARD(state, data) {
        Vue.set(state.consolidationDashboard, 'data', data)
    },
    SET_CONSOLIDATION_REPORT_SETTINGS_ITEM(state, { key, value }) {
        Vue.set(state.consolidationReportSettings, key, {
            loading: false,
            loaded: false,
            data: null,
            error: null,
            ...value
        })
    },
    SET_CONSOLIDATION_WIDGET_REPORT_ITEM(state, { key, value }) {
        Vue.set(state.consolidationWidgetReports, key, {
            loading: false,
            loaded: false,
            data: null,
            error: null,
            ...value
        })
    },
    CHANGE_MEETING_NAME(state, { value, storeKey, list, item }) {
        if(state[list]?.[storeKey]?.results?.length) {
            const index = state[list][storeKey].results.findIndex(f => f.id === item)
            if(index !== -1)
                Vue.set(state[list][storeKey].results[index], 'name', value)
        }
    },
    CHANGE_LIST_FIELD(state, {field, value, storeKey, list}) {
        Vue.set(state[list][storeKey], field, value)
    },
    CLEAR_LIST(state, { storeKey, list }) {
        const search = state[list]?.[storeKey]?.search || ""
        const count = state[list]?.[storeKey]?.count || ""
        Vue.set(state[list], storeKey, {
            ...listModel,
            search,
            count
        })
    },
    CLEAR_LIST_ALL(state, { list }) {
        for(const key in state[list]) {
            const search = state[list]?.[key]?.search || ""
            const count = state[list]?.[key]?.count || ""
            Vue.set(state[list], key, {
                ...listModel,
                search,
                count
            })
        }
        if(list === 'taskList') {
            const focusList = 'taskFocusList'
            for(const key in state[focusList]) {
                const search = state[focusList]?.[key]?.search || ""
                const count = state[focusList]?.[key]?.count || ""
                Vue.set(state[focusList], key, {
                    ...listModel,
                    search,
                    count
                })
            }
            const otherList = 'taskOtherList'
            for(const key in state[otherList]) {
                const search = state[otherList]?.[key]?.search || ""
                const count = state[otherList]?.[key]?.count || ""
                Vue.set(state[otherList], key, {
                    ...listModel,
                    search,
                    count
                })
            }
        }
        if(list === 'ticketList') {
            const otherList = 'ticketOtherList'
            for(const key in state[otherList]) {
                const search = state[otherList]?.[key]?.search || ""
                const count = state[otherList]?.[key]?.count || ""
                Vue.set(state[otherList], key, {
                    ...listModel,
                    search,
                    count
                })
            }
        }
    },
    LIST_CONCAT(state, {list, data, storeKey, reload = false}) {
        const newResults = data.results.map(item => {
            const find = state[list][storeKey].results.find(f => f.id === item.id)
            const itemData = {
                ...item,
                collapse: find?.collapse || false,
                actions: find?.actions || item?.actions || null,
                intentsCollapse: find?.intentsCollapse || false
            }
            if(list === 'meetingList')
                itemData.tab = 'summary'
            return itemData
        })
        if(reload) {
            state[list][storeKey].results = newResults
        } else
            state[list][storeKey].results = state[list][storeKey].results.concat(newResults)
    },
    CHANGE_COLLAPSE(state, {list, value, storeKey, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'collapse', value)
    },
    CHANGE_INTENTS_COLLAPSE(state, {list, value, storeKey, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'intentsCollapse', value)
    },
    CHANGE_TAB(state, {list, value, storeKey, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'tab', value)
    },
    SET_ACTION_INFO(state, {list, data, storeKey, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'actions', data.actions)
    },
    SET_IS_ATTENDING(state, {list, storeKey, value, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'is_attending', value)
    },
    TOGGLE_NEW_COMMENT(state, {list, storeKey, value, item}) {
        const index = state[list][storeKey].results.findIndex(f => f.id === item.id)
        if(index !== -1)
            Vue.set(state[list][storeKey].results[index], 'has_new_comments', value)
    },
    DELETE_LIST_ITEMS(state, { list, deletions }) {
        if(!list || !Array.isArray(deletions) || !state[list]) return
        for(const { key, indices } of deletions) {
            if(!key || !Array.isArray(indices)) continue
            const section = state[list][key]
            if(!section || !Array.isArray(section.results)) continue
            const sorted = indices.slice().sort((a, b) => b - a)
            for(const idx of sorted) {
                if(idx >= 0 && idx < section.results.length) {
                    section.results.splice(idx, 1)
                }
            }
            const removedCount = sorted.length
            if(typeof section.count === 'number') {
                section.count = Math.max(0, section.count - removedCount)
            }
            section.empty = !section.results.length
        }
    },
    UPDATE_LIST(state, { list, items }) {
        if(!Array.isArray(items) || !items.length) return

        const updateSectionById = (section, newItem, oldItem) => {
            if(!section || !Array.isArray(section.results)) return
            if(!newItem?.id && !oldItem?.id) return

            const id = newItem?.id ?? oldItem?.id
            const index = section.results.findIndex(i => i?.id === id)
            if(index === -1) return

            const payload = {
                ...section.results[index],
                ...oldItem,
                ...newItem
            }

            if(payload.id === undefined) return

            Vue.set(section.results, index, payload)
        }

        if(list === 'taskList') {
            if(state.taskFocusList) {
                for(const it of items) {
                    const { key, newItem, oldItem } = it
                    if(!key) continue
                    const section = state.taskFocusList[key]
                    updateSectionById(section, newItem, oldItem)
                }
            }

            if(state.taskOtherList) {
                for(const it of items) {
                    const { key, newItem, oldItem } = it
                    if(!key) continue
                    const section = state.taskOtherList[key]
                    updateSectionById(section, newItem, oldItem)
                }
            }
        }
        if(list === 'ticketList') {
            if(state.ticketOtherList) {
                for(const it of items) {
                    const { key, newItem, oldItem } = it
                    if(!key) continue
                    const section = state.ticketOtherList[key]
                    updateSectionById(section, newItem, oldItem)
                }
            }
        }

        if(!state[list]) return

        for(const it of items) {
            const { key, newItem, oldItem } = it
            if(!key) continue
            const section = state[list]?.[key]
            updateSectionById(section, newItem, oldItem)
        }
    },
    UPDATE_SEARCH_VALUE(state, { storeKey, value }) {
        Vue.set(state.taskSearch[storeKey], 'search', value)
    },
    SET_DAY_PULSE_CATEGORIES_LOADING(state, { value }) {
        Vue.set(state.dayPulseCategories, 'loading', value)
    },
    SET_DAY_PULSE_CATEGORIES(state, { results = [], loaded = true }) {
        Vue.set(state.dayPulseCategories, 'results', Array.isArray(results) ? results : [])
        Vue.set(state.dayPulseCategories, 'loaded', loaded)
    },
    DAY_PULSE_CREATE(state, { storeKey, list = 'dayPulseList', item }) {
        if(!item || !item.id || !state[list]?.[storeKey]) return
        state[list][storeKey].results.unshift(item)
        state[list][storeKey].count = (state[list][storeKey].count || 0) + 1
        state[list][storeKey].empty = !state[list][storeKey].results.length
    },
    DAY_PULSE_UPDATE(state, { storeKey, list = 'dayPulseList', item }) {
        if(!item || !item.id || !state[list]?.[storeKey]) return
        const section = state[list][storeKey]
        const index = section.results.findIndex(i => i.id === item.id)
        if(index === -1) return

        Vue.set(section.results, index, item)
        section.empty = !section.results.length
    },
    DAY_PULSE_REMOVE(state, { storeKey, list = 'dayPulseList', id }) {
        if(!id || !state[list]?.[storeKey]) return
        const section = state[list][storeKey]
        const index = section.results.findIndex(i => i.id === id)
        if(index !== -1) {
            section.results.splice(index, 1)
            if(typeof section.count === 'number')
                section.count = Math.max(0, section.count - 1)
        }
        section.empty = !section.results.length
    }
}
