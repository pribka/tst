import axios from '@/config/axios'
import axiosMain from 'axios'
import { errorHandler } from '@/utils/index.js'
import { dateFormat } from '../utils.js'

let countTimer;
const taskListCancelSource = {
    other: null,
    activity: null,
    pinned: null
}
const ticketListCancelSource = {
    other: null,
    activity: null
}
let eventListCancelSource = null
let dayPulseListCancelSource = null
let meetingListCancelSource = null
let allDayCancelSource = null
let dayCancelSource = null
let countCancelSource = null
let intentsCancelSource = null
let reportSettingCancelSource = null
let consolidationKeyResultsCancelSource = null
let consolidationDashboardCancelSource = null
const consolidationReportSettingsCancelSource = {}
const consolidationWidgetReportCancelSource = {}

const cloneDeep = value => JSON.parse(JSON.stringify(value || null))

const getProcessedItem = ({ item, additionalFields = [] }) => {
    const processedItem = {
        name: item.name
    }

    additionalFields.forEach(field => {
        if (item[field] !== undefined)
            processedItem[field] = item[field]
    })

    return processedItem
}

const getSQLCompatibleString = (string = '') => {
    return String(string).replace(/[\s"';:,.]/g, (match) => {
        switch (match) {
        case ':': return '__COLON'
        case ';': return '__SEMICOLON'
        case ' ': return '__SPACE'
        case ',': return '__COMMA'
        case '.': return '__DOT'
        default: return match
        }
    })
}

const getFilterByName = (filters = [], name = '') => {
    return filters.find(filter => filter?.name === name) || null
}

const normalizeFilterValue = (value) => {
    if (value === null || value === undefined || value === '')
        return null
    if (Array.isArray(value))
        return value.filter(Boolean)
    return [value]
}

const isDateFilterType = (type = '') => {
    return [
        'CustomDateTimeField',
        'CustomDateField',
        'DateTimeField',
        'DateField'
    ].includes(type)
}

const applyConsolidationFilterBindings = ({
    reportSettings,
    scope,
    relatedObjectId,
    startDate,
    endDate,
    includePeriod = true,
    includeDateFilters = false
}) => {
    const preparedSettings = cloneDeep(reportSettings)
    const metadata = preparedSettings?.metadata || {}
    const filters = Array.isArray(metadata.filters) ? metadata.filters : []
    const bindings = metadata?.filter_bindings || {}
    const scopeBindings = bindings?.scope_bindings || {}
    const periodFieldName = bindings?.period_field || null
    const scopeFieldName = scopeBindings?.[scope] || null

    Object.values(scopeBindings).forEach(fieldName => {
        const filter = getFilterByName(filters, fieldName)
        if (!filter) return
        filter.active = false
        filter.value = null
    })

    if (includePeriod && periodFieldName) {
        const periodFilter = getFilterByName(filters, periodFieldName)
        if (periodFilter) {
            periodFilter.active = true
            periodFilter.value = [startDate, endDate]
        }
    }

    if (includeDateFilters) {
        filters.forEach(filter => {
            if (!isDateFilterType(filter?.type)) return
            if (!filter?.active) return
            filter.value = [startDate, endDate]
        })
    }

    if (scopeFieldName) {
        const scopeFilter = getFilterByName(filters, scopeFieldName)
        if (scopeFilter) {
            scopeFilter.active = true
            scopeFilter.value = normalizeFilterValue(relatedObjectId)
            if (Array.isArray(scopeFilter.value) && scopeFilter.value.length > 1 && scope === 'user')
                scopeFilter.comparison_type = 'in'
        }
    }

    return preparedSettings
}

const buildReportFilters = (filters = []) => {
    const activeFilters = filters.filter(item => item?.active && ![null, undefined].includes(item?.value))
    const preprocessedFilters = []

    for (let i = 0; i < activeFilters.length; i++) {
        const item = activeFilters[i]
        if (item?.type?.includes('DateTimeField') || item?.type?.includes('DateField')) {
            preprocessedFilters.push({
                name: item.name,
                comparison_type: '>=',
                value: item.value?.[0] || null,
            })
            preprocessedFilters.push({
                name: item.name,
                comparison_type: '<=',
                value: item.value?.[1] || null,
            })
        } else {
            preprocessedFilters.push(item)
        }
    }

    return preprocessedFilters.map(item => ({
        field: item.aggregate
            ? getSQLCompatibleString(item.title || item.defaultTitle || item.verbose_name || item.name)
            : item.name,
        comparison_type: item.comparison_type,
        value: item.value,
    }))
}

const buildReportPayload = (reportSettings) => {
    const metadata = reportSettings?.metadata || {}
    const columns = Array.isArray(metadata.columns) ? metadata.columns : []
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const payload = {
        report_name: reportSettings?.name || null,
        fields: {
            groups: columns
                .filter(column => !column?.aggregate && !column?.system)
                .map(item => getProcessedItem({
                    item,
                    additionalFields: ['title', 'order', 'is_visible']
                })),
            leveling: (metadata.grouping || []).map(item => getProcessedItem({ item })),
            aggregates: columns
                .filter(column => column?.aggregate)
                .map(item => ({
                    ...item,
                    name: getSQLCompatibleString(item.title)
                })),
            system_fields: columns
                .filter(column => column?.system)
                .map(item => getProcessedItem({
                    item,
                    additionalFields: ['title', 'order', 'is_visible']
                }))
        },
        filters: buildReportFilters(metadata.filters || []),
        ordering: (metadata.ordering || [])
            .filter(item => item?.orderBy)
            .slice()
            .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
            .map(item => {
                const fieldName = item.aggregate
                    ? getSQLCompatibleString(item.name)
                    : item.name
                return (item.orderBy === 'DESC' ? '-' : '') + fieldName
            }),
        results: 'apexchart',
        id: reportSettings?.id,
        timezone
    }

    if (metadata.queryset_params)
        payload.queryset_params = metadata.queryset_params

    return payload
}

export default {
    async getConsolidationKeyResults({ state, commit }, { scope, relatedObjectId } = {}) {
        let source
        try {
            const startDate = state.employeesDateRange?.[0]
            const endDate = state.employeesDateRange?.[1]

            if (!scope || !relatedObjectId || !startDate || !endDate) {
                commit('SET_CONSOLIDATION_KEY_RESULTS', null)
                return null
            }

            if (consolidationKeyResultsCancelSource)
                consolidationKeyResultsCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            consolidationKeyResultsCancelSource = { cancel: source.cancel }

            commit('SET_CONSOLIDATION_KEY_RESULTS_LOADING', true)

            const params = {
                start: dateFormat(startDate).slice(0, 10),
                end: dateFormat(endDate).slice(0, 10),
                scope
            }

            params[scope] = relatedObjectId

            const { data } = await axios.get('/analytics/dashboard/kpi/', {
                params,
                cancelToken: source.token
            })

            commit('SET_CONSOLIDATION_KEY_RESULTS', data || null)
            return data || null
        } catch (error) {
            errorHandler({ error, show: false })
            commit('SET_CONSOLIDATION_KEY_RESULTS', null)
            return null
        } finally {
            if (consolidationKeyResultsCancelSource === source)
                consolidationKeyResultsCancelSource = null
            commit('SET_CONSOLIDATION_KEY_RESULTS_LOADING', false)
        }
    },
    async getConsolidationDashboard({ state, commit }, { scope } = {}) {
        let source
        try {
            const startDate = state.employeesDateRange?.[0]
            const endDate = state.employeesDateRange?.[1]

            if (!scope || !startDate || !endDate) {
                commit('SET_CONSOLIDATION_DASHBOARD', null)
                return null
            }

            if (consolidationDashboardCancelSource)
                consolidationDashboardCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            consolidationDashboardCancelSource = { cancel: source.cancel }

            commit('SET_CONSOLIDATION_DASHBOARD_LOADING', true)

            const params = {
                start: dateFormat(startDate).slice(0, 10),
                end: dateFormat(endDate).slice(0, 10),
                scope,
                section: 'dynamics'
            }

            const { data } = await axios.get('/analytics/dashboard/', {
                params,
                cancelToken: source.token
            })

            commit('SET_CONSOLIDATION_DASHBOARD', data || null)
            return data || null
        } catch (error) {
            errorHandler({ error, show: false })
            commit('SET_CONSOLIDATION_DASHBOARD', null)
            return null
        } finally {
            if (consolidationDashboardCancelSource === source)
                consolidationDashboardCancelSource = null
            commit('SET_CONSOLIDATION_DASHBOARD_LOADING', false)
        }
    },
    async getConsolidationReportSettings({ state, commit }, {
        reportCode,
        filterPreset = null,
        scope = null,
        force = false
    } = {}) {
        if (!reportCode) return null

        const cacheKey = [reportCode, filterPreset || '', scope || ''].join('::')

        const cachedItem = state.consolidationReportSettings?.[cacheKey]
        if (!force && cachedItem?.loaded)
            return cachedItem.data || null
        if (cachedItem?.loading)
            return cachedItem.data || null

        let source
        try {
            if (consolidationReportSettingsCancelSource[cacheKey])
                consolidationReportSettingsCancelSource[cacheKey].cancel()
            source = await axiosMain.CancelToken.source()
            consolidationReportSettingsCancelSource[cacheKey] = { cancel: source.cancel }

            commit('SET_CONSOLIDATION_REPORT_SETTINGS_ITEM', {
                key: cacheKey,
                value: {
                    ...cachedItem,
                    loading: true,
                    error: null
                }
            })

            const params = {}
            if (filterPreset)
                params.filter_preset = filterPreset

            const { data } = await axios.get(`/reports/report_settings/by_code/${reportCode}/`, {
                params,
                cancelToken: source.token
            })

            commit('SET_CONSOLIDATION_REPORT_SETTINGS_ITEM', {
                key: cacheKey,
                value: {
                    loading: false,
                    loaded: true,
                    data: (() => {
                        const preparedData = cloneDeep(data)
                        const scopeBindings = preparedData?.metadata?.filter_bindings?.scope_bindings || {}

                        if (preparedData?.metadata?.filter_bindings)
                            preparedData.metadata.filter_bindings.scope_bindings = scope && scopeBindings?.[scope]
                                ? { [scope]: scopeBindings[scope] }
                                : {}

                        return preparedData || null
                    })(),
                    error: null
                }
            })

            return state.consolidationReportSettings?.[cacheKey]?.data || null
        } catch (error) {
            errorHandler({ error, show: false })
            commit('SET_CONSOLIDATION_REPORT_SETTINGS_ITEM', {
                key: cacheKey,
                value: {
                    ...cachedItem,
                    loading: false,
                    loaded: false,
                    error
                }
            })
            return null
        } finally {
            if (consolidationReportSettingsCancelSource[cacheKey] === source)
                delete consolidationReportSettingsCancelSource[cacheKey]
        }
    },
    async getConsolidationWidgetReport({ state, commit }, {
        widgetKey,
        reportSettings,
        scope,
        relatedObjectId,
        startDate,
        endDate,
        force = false
    } = {}) {
        if (!widgetKey || !reportSettings || !scope || !startDate || !endDate)
            return null

        const cacheKey = [widgetKey, relatedObjectId || '', startDate, endDate].join('::')
        const cachedItem = state.consolidationWidgetReports?.[cacheKey]
        if (!force && cachedItem?.loaded)
            return cachedItem.data || null
        if (cachedItem?.loading)
            return cachedItem.data || null

        let source
        try {
            if (consolidationWidgetReportCancelSource[cacheKey])
                consolidationWidgetReportCancelSource[cacheKey].cancel()
            source = await axiosMain.CancelToken.source()
            consolidationWidgetReportCancelSource[cacheKey] = { cancel: source.cancel }

            commit('SET_CONSOLIDATION_WIDGET_REPORT_ITEM', {
                key: cacheKey,
                value: {
                    ...cachedItem,
                    loading: true,
                    error: null
                }
            })

            const preparedSettings = applyConsolidationFilterBindings({
                reportSettings,
                scope,
                relatedObjectId,
                startDate,
                endDate,
                includePeriod: true,
                includeDateFilters: false
            })
            const metadata = preparedSettings?.metadata || {}
            const payload = buildReportPayload(preparedSettings)
            const modelName = metadata?.modelName
            if (!modelName)
                throw new Error('empty_report_model_name')

            const { data } = await axios.post(`/reports/${modelName}/list_post/`, payload, {
                cancelToken: source.token
            })

            commit('SET_CONSOLIDATION_WIDGET_REPORT_ITEM', {
                key: cacheKey,
                value: {
                    loading: false,
                    loaded: true,
                    data: data || null,
                    error: null
                }
            })

            return data || null
        } catch (error) {
            errorHandler({ error, show: false })
            commit('SET_CONSOLIDATION_WIDGET_REPORT_ITEM', {
                key: cacheKey,
                value: {
                    ...cachedItem,
                    loading: false,
                    loaded: false,
                    error
                }
            })
            return null
        } finally {
            if (consolidationWidgetReportCancelSource[cacheKey] === source)
                delete consolidationWidgetReportCancelSource[cacheKey]
        }
    },
    async getConsolidationPreparedReportSettings({ dispatch }, {
        reportCode,
        filterPreset = null,
        scope,
        relatedObjectId,
        startDate,
        endDate,
        force = false
    } = {}) {
        if (!reportCode || !scope || !startDate || !endDate)
            return null

        const reportSettings = await dispatch('getConsolidationReportSettings', {
            reportCode,
            filterPreset,
            scope,
            force
        })

        if (!reportSettings)
            return null

        return applyConsolidationFilterBindings({
            reportSettings,
            scope,
            relatedObjectId,
            startDate,
            endDate,
            includePeriod: false,
            includeDateFilters: true
        })
    },
    async taskPinned({ state, commit }, { storeKey, list, item }) {
        try {
            const pinned = !item.pinned
            const { data } = await axios.post(`/tasks/task/${item.id}/pin/`, { pinned })
            if(data) {
                
            }
        } catch(error) {
            errorHandler({error, show: false})
        }
    },
    getTabsCount({ state, commit }, { storeKey }) {
        clearTimeout(countTimer)
        countTimer = setTimeout(async () => {
            let source;
            try {
                if(countCancelSource)
                    countCancelSource.cancel()
                source = await axiosMain.CancelToken.source()
                countCancelSource = { cancel: source.cancel }
                const params = {
                    task_type: 'task',
                    start: dateFormat(state.mainDate[storeKey][0]),
                    end: dateFormat(state.mainDate[storeKey][1])
                }
                if(state.taskSearch?.[storeKey]?.search)
                    params.search = state.taskSearch[storeKey].search
                if(state.project[storeKey])
                    params.project = state.project[storeKey].id
                if(state.role[storeKey])
                    params.role = state.role[storeKey]
                if(state.workgroup[storeKey])
                    params.workgroup = state.workgroup[storeKey].id
                if(state.user[storeKey]?.length)
                    params.user = state.user[storeKey].map(user => user.id).join(',')
                const { data } = await axios.get('/tasks/task/my_day_tasks_count/', {params, cancelToken: source.token})
                if(data)
                    commit('SET_TABS_COUNT', { storeKey, data })
            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                if(countCancelSource === source)
                    countCancelSource = null
            }
        }, 600)
    },
    async getTaskList({ state, commit }, { storeKey, list, group = 'other', loading = true, reload = false }) {
        let source;
        try {
            if(taskListCancelSource[group])
                taskListCancelSource[group].cancel()
            source = await axiosMain.CancelToken.source()
            taskListCancelSource[group] = { cancel: source.cancel }

            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: true,list})
            commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: false,list})

            const page = state[list][storeKey].page

            const params = {
                task_type: state[list][storeKey].task_type,
                page_size: state[list][storeKey].page_size,
                page,
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1]),
                group
            }
            if(state.taskSearch?.[storeKey]?.search)
                params.search = state.taskSearch[storeKey].search
            if(state.project[storeKey])
                params.project = state.project[storeKey].id
            if(state.role[storeKey])
                params.role = state.role[storeKey]
            if(state.workgroup[storeKey])
                params.workgroup = state.workgroup[storeKey].id
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')
            const { data } = await axios.get('/tasks/task/my_day/', {params, cancelToken: source.token})
            if(data) {
                if(!data.results?.length && page === 1)
                    commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: true,list})

                commit('CHANGE_LIST_FIELD', {storeKey,field: 'next',value: data.next,list})
                commit('CHANGE_LIST_FIELD', {storeKey,field: 'count',value: data.count,list})
                commit('LIST_CONCAT', {storeKey, list, data, reload})
            }
        } catch (error) {
            errorHandler({error, show: false})
        } finally {
            if (taskListCancelSource[group] === source)
                taskListCancelSource[group] = null
            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: false,list})
        }
    },
    async getEventList({ state, commit }, { storeKey }) {
        const list = 'eventList'
        let source;
        try {
            if(eventListCancelSource)
                eventListCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            eventListCancelSource = { cancel: source.cancel }

            commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: true,list})
            commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: false,list})

            const page = state[list][storeKey].page

            const params = {
                page_size: state[list][storeKey].page_size,
                page,
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1])
            }
            if(state[list]?.[storeKey]?.search)
                params.search = state[list][storeKey].search
            if(state.project[storeKey])
                params.project = state.project[storeKey].id
            if(state.workgroup[storeKey])
                params.workgroup = state.workgroup[storeKey].id
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')
            const { data } = await axios.get('/calendars/events/my_day/', {params, cancelToken: source.token})
            if(data) {
                if(!data.results?.length && page === 1)
                    commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: true,list})

                commit('CHANGE_LIST_FIELD', {storeKey,field: 'next',value: data.next,list})
                commit('CHANGE_LIST_FIELD', {storeKey,field: 'count',value: data.count,list})
                commit('LIST_CONCAT', {storeKey, list, data})
            }
        } catch (error) {
            errorHandler({error, show: false})
        } finally {
            if (eventListCancelSource === source)
                eventListCancelSource = null
            commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: false,list})
        }
    },
    async getDayPulseList({ state, commit }, { storeKey, list = 'dayPulseList', loading = true, reload = false }) {
        let source;
        try {
            if(dayPulseListCancelSource)
                dayPulseListCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            dayPulseListCancelSource = { cancel: source.cancel }

            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'loading', value: true, list})
            commit('CHANGE_LIST_FIELD', {storeKey, field: 'empty', value: false, list})

            const page = state[list][storeKey].page
            const params = {
                page_size: state[list][storeKey].page_size,
                page,
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1])
            }
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')

            const { data } = await axios.get('/day_summary/note/', { params, cancelToken: source.token })
            if(data) {
                const results = Array.isArray(data.results) ? data.results : []
                if(!results.length && page === 1)
                    commit('CHANGE_LIST_FIELD', {storeKey, field: 'empty', value: true, list})

                commit('CHANGE_LIST_FIELD', {storeKey, field: 'next', value: data.next, list})
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'count', value: data.count || 0, list})
                commit('LIST_CONCAT', {storeKey, list, data: { results }, reload})
            }
        } catch(error) {
            errorHandler({error, show: false})
        } finally {
            if(dayPulseListCancelSource === source)
                dayPulseListCancelSource = null
            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'loading', value: false, list})
        }
    },
    async getDayPulseCategories({ state, commit }, { force = false } = {}) {
        if(!force && state.dayPulseCategories?.loaded)
            return state.dayPulseCategories.results || []
        if(state.dayPulseCategories?.loading)
            return state.dayPulseCategories.results || []

        try {
            commit('SET_DAY_PULSE_CATEGORIES_LOADING', { value: true })
            const { data } = await axios.get('/day_summary/categories/')
            const results = Array.isArray(data) ? data : []
            commit('SET_DAY_PULSE_CATEGORIES', { results, loaded: true })
            return results
        } catch(error) {
            errorHandler({error, show: false})
            commit('SET_DAY_PULSE_CATEGORIES', { results: state.dayPulseCategories?.results || [], loaded: false })
            return state.dayPulseCategories?.results || []
        } finally {
            commit('SET_DAY_PULSE_CATEGORIES_LOADING', { value: false })
        }
    },
    async saveDayPulseNote({ commit }, { storeKey, list = 'dayPulseList', note, edit = false }) {
        if(!note) return null
        try {
            const isEdit = edit === true
            if(isEdit) {
                const { data } = await axios.put(`/day_summary/note/${note.id}/`, note)
                if(data) {
                    commit('DAY_PULSE_UPDATE', {
                        storeKey,
                        list,
                        item: data
                    })
                }
                return data || null
            } else {
                const { data } = await axios.post('/day_summary/note/', note)
                if(data) {
                    commit('DAY_PULSE_CREATE', {
                        storeKey,
                        list,
                        item: data
                    })
                }
                return data || null
            }
        } catch(error) {
            errorHandler({ error, show: false })
            throw error
        }
    },
    async deleteDayPulseNote({ commit }, { storeKey, list = 'dayPulseList', id }) {
        if(!id) return
        await axios.post('/table_actions/update_is_active/', [{
            id,
            is_active: false
        }])
        commit('DAY_PULSE_REMOVE', {
            storeKey,
            list,
            id
        })
    },
    async updateDayPulseVisors({ commit }, { storeKey, list = 'dayPulseList', id, note = null, visors = [] }) {
        if(!id) return null
        try {
            const payload = {
                visors: Array.isArray(visors) ? visors.map(user => user.id).filter(Boolean) : []
            }
            const { data } = await axios.put(`/day_summary/note/${id}/update_visors/`, payload)

            let item = null
            if(data?.id) {
                item = data
            } else if(note?.id) {
                item = {
                    ...note,
                    visors: Array.isArray(data?.visors) ? data.visors : payload.visors
                }
            }

            if(item?.id) {
                commit('DAY_PULSE_UPDATE', {
                    storeKey,
                    list,
                    item
                })
            }
            return data || item
        } catch(error) {
            errorHandler({ error, show: false })
            throw error
        }
    },
    async getMeetingList({ state, commit }, { storeKey }) {
        const list = 'meetingList'
        let source;
        try {
            if(meetingListCancelSource)
                meetingListCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            meetingListCancelSource = { cancel: source.cancel }

            commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: true, list})
            commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: false, list})

            const page = state[list][storeKey].page
            const params = {
                page_size: state[list][storeKey].page_size,
                page,
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1])
            }
            if(state[list]?.[storeKey]?.search)
                params.search = state[list][storeKey].search
            if(state.project[storeKey])
                params.project = state.project[storeKey].id
            if(state.workgroup[storeKey])
                params.workgroup = state.workgroup[storeKey].id
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')
            const { data } = await axios.get('/meetings/sections/my_day/', {params, cancelToken: source.token})
            if(data) {
                if(!data.results?.length && page === 1)
                    commit('CHANGE_LIST_FIELD', {storeKey,field: 'empty',value: true, list})

                commit('CHANGE_LIST_FIELD', {storeKey,field: 'next',value: data.next, list})
                commit('CHANGE_LIST_FIELD', {storeKey,field: 'count',value: data.count, list})
                commit('LIST_CONCAT', {storeKey, list, data})
            }
        } catch (error) {
            errorHandler({error, show: false})
        } finally {
            if(meetingListCancelSource === source)
                meetingListCancelSource = null
            commit('CHANGE_LIST_FIELD', {storeKey,field: 'loading',value: false, list})
        }
    },
    async getTicketList({ state, commit }, { storeKey, list, group = 'other', loading = true, reload = false }) {
        let source;
        try {
            if(ticketListCancelSource[group])
                ticketListCancelSource[group].cancel()
            source = await axiosMain.CancelToken.source()
            ticketListCancelSource[group] = { cancel: source.cancel }

            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'loading', value: true, list})
            commit('CHANGE_LIST_FIELD', {storeKey, field: 'empty', value: false, list})

            const page = state[list][storeKey].page
            const params = {
                page_size: state[list][storeKey].page_size,
                page,
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1]),
                group
            }
            if(state[list]?.[storeKey]?.search)
                params.search = state[list][storeKey].search
            if(state.project[storeKey])
                params.project = state.project[storeKey].id
            if(state.ticketRole?.[storeKey])
                params.role = state.ticketRole[storeKey]
            if(state.workgroup[storeKey])
                params.workgroup = state.workgroup[storeKey].id
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')

            const { data } = await axios.get('/help_desk/tickets/my_day/', { params, cancelToken: source.token })
            if(data) {
                if(!data.results?.length && page === 1)
                    commit('CHANGE_LIST_FIELD', {storeKey, field: 'empty', value: true, list})

                commit('CHANGE_LIST_FIELD', {storeKey, field: 'next', value: data.next, list})
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'count', value: data.count, list})
                commit('LIST_CONCAT', {storeKey, list, data, reload})
            }
        } catch(error) {
            errorHandler({error, show: false})
        } finally {
            if(ticketListCancelSource[group] === source)
                ticketListCancelSource[group] = null
            if(loading)
                commit('CHANGE_LIST_FIELD', {storeKey, field: 'loading', value: false, list})
        }
    },
    async getActions({ commit }, { storeKey, list, item }) {
        if(item.actions) return
        try {
            const { data } = await axios.get(`/tasks/${item.id}/action_info/`)
            if(data) {
                commit('SET_ACTION_INFO', {
                    data,
                    storeKey,
                    list,
                    item
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        }
    },
    async getEventActions({ commit }, { storeKey, list, item }) {
        if(item.actions) return
        try {
            const { data } = await axios.get(`/calendars/events/${item.id}/action_info/`)
            if(data) {
                commit('SET_ACTION_INFO', {
                    data,
                    storeKey,
                    list,
                    item
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        }
    },
    async getMeetingsActions({ commit }, { storeKey, list, item }) {
        try {
            const { data } = await axios.get(`/meetings/sections/${item.id}/action_info/`)
            if(data) {
                commit('SET_ACTION_INFO', {
                    data,
                    storeKey,
                    list,
                    item
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        }
    },
    async getTicketActions({ commit }, { storeKey, list, item, force = false }) {
        if(item.actions && !force) return
        try {
            const { data } = await axios.get(`/help_desk/tickets/${item.id}/action_info/`)
            if(data) {
                commit('SET_ACTION_INFO', {
                    data,
                    storeKey,
                    list,
                    item
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        }
    },
    reloadList({ commit, state, dispatch }, { list }) {
        commit('CLEAR_LIST_ALL', { list })
        if(list === 'eventList') {
            for(const storeKey in state[list]) {
                dispatch('getEventList', { storeKey })
            }
        }
        if(list === 'taskList') {
            for(const storeKey in state[list]) {
                dispatch('getTaskList', { storeKey, list, group: 'activity' })
            }
            for(const storeKey in state['taskFocusList']) {
                dispatch('getTaskList', { storeKey, list: 'taskFocusList', group: 'pinned' })
            }
            for(const storeKey in state['taskOtherList']) {
                dispatch('getTaskList', { storeKey, list: 'taskOtherList', group: 'other' })
            }
        }
        if(list === 'ticketList') {
            for(const storeKey in state[list]) {
                dispatch('getTicketList', { storeKey, list, group: 'activity' })
            }
            for(const storeKey in state['ticketOtherList']) {
                dispatch('getTicketList', { storeKey, list: 'ticketOtherList', group: 'other' })
            }
        }
        for(const storeKey in state.tabsCount) {
            dispatch('getTabsCount', { storeKey })
        }
        dispatch('getAllDayStatistics')
    },
    async deleteItem({ commit, state }, { list, item }) {
        const allList = state[list]
        if(!list || !item || !item.id || !allList) return
        let hasMatch = false
        const deletions = []

        for(const [key, val] of Object.entries(allList)) {
            if(!val || !Array.isArray(val.results)) continue
            const indices = []
            val.results.forEach((r, i) => {
                if(r && r.id === item.id) indices.push(i)
            })
            if(indices.length) {
                hasMatch = true
                deletions.push({ key, indices })
            }
        }

        if(!hasMatch) return

        commit('DELETE_LIST_ITEMS', { list, deletions })
        for(const storeKey in state.tabsCount) {
            dispatch('getTabsCount', { storeKey })
        }
        dispatch('getAllDayStatistics')
    },
    async updateItem({ commit, state, dispatch }, { list, item, notAllReload = false }) {
        const allList = state[list]
        if(list === 'meetingList' && item.id) {
            let hasMatch = false

            for(const val of Object.values(allList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r.meeting && r.meeting.id === item.id || r && r.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }

            if(!hasMatch) return

            try {
                const { data } = await axios.get('/meetings/sections/my_day/', {
                    params: {
                        meeting: item.id
                    }
                })
                if(data?.results?.length) {
                    const found = []

                    for(const backendItem of data.results) {
                        for(const [key, val] of Object.entries(allList)) {
                            if(!val || !Array.isArray(val.results)) continue

                            const idx = (() => {
                                const byId = val.results.findIndex(r => r && backendItem && r.id === backendItem.id)
                                if(byId !== -1) return byId

                                return val.results.findIndex(r => {
                                    if(!r || !backendItem) return false
                                    if(!r.meeting || !backendItem.meeting) return false
                                    return r.meeting.id === backendItem.meeting.id
                                })
                            })()

                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                const newItem = backendItem

                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...newItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions,
                                        tab: oldItem.tab || 'summary'
                                    }
                                })
                            }
                        }
                    }
                    if(found?.length) {
                        commit('UPDATE_LIST', {
                            list,
                            items: found
                        })
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
        if(list === 'eventList' && item.id) {
            let hasMatch = false

            for(const val of Object.values(allList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }

            if(!hasMatch) return

            try {
                const { data } = await axios.get('/calendars/events/my_day/', {
                    params: {
                        id: item.id
                    }
                })
                if(data?.results?.length) {
                    const found = []

                    for(const backendItem of data.results) {
                        for(const [key, val] of Object.entries(allList)) {
                            if(!val || !Array.isArray(val.results)) continue

                            const idx = val.results.findIndex(r => {
                                if(!r) return false
                                if(r && backendItem) {
                                    return r.id === backendItem.id
                                }
                                return false
                            })

                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                const newItem = backendItem

                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...newItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                    }

                    if(found?.length) {
                        commit('UPDATE_LIST', {
                            list,
                            items: found
                        })
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
        if(list === 'taskList' && item.id) {
            let hasMatch = false

            const taskFocusList = state['taskFocusList']
            const taskOtherList = state['taskOtherList']

            for(const val of Object.values(allList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }
            for(const val of Object.values(taskFocusList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }
            for(const val of Object.values(taskOtherList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }

            if(!hasMatch) return

            try {
                const { data } = await axios.get('/tasks/task/my_day/', {
                    params: {
                        id: item.id
                    }
                })
                if(data?.results?.length) {
                    const found = []

                    for(const backendItem of data.results) {
                        for(const [key, val] of Object.entries(allList)) {
                            if(!val || !Array.isArray(val.results)) continue

                            const idx = val.results.findIndex(r => {
                                if(!r) return false
                                if(r && backendItem) {
                                    return r.id === backendItem.id
                                }
                                return false
                            })

                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                const newItem = backendItem

                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...newItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                        for(const [key, val] of Object.entries(taskFocusList)) {
                            if(!val || !Array.isArray(val.results)) continue

                            const idx = val.results.findIndex(r => {
                                if(!r) return false
                                if(r && backendItem) {
                                    return r.id === backendItem.id
                                }
                                return false
                            })

                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                const newItem = backendItem

                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...newItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                        for(const [key, val] of Object.entries(taskOtherList)) {
                            if(!val || !Array.isArray(val.results)) continue

                            const idx = val.results.findIndex(r => {
                                if(!r) return false
                                if(r && backendItem) {
                                    return r.id === backendItem.id
                                }
                                return false
                            })

                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                const newItem = backendItem

                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...newItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                    }

                    if(found?.length) {
                        /*for(const sKey in state['taskList']) {
                            dispatch('getTaskList', { storeKey: sKey, list: 'taskList', group: 'activity', loading: false, reload: true })
                        }
                        for(const sKey in state['taskFocusList']) {
                            dispatch('getTaskList', { storeKey: sKey, list: 'taskFocusList', group: 'pinned', loading: false, reload: true })
                        }
                        for(const sKey in state['taskOtherList']) {
                            dispatch('getTaskList', { storeKey: sKey, list: 'taskOtherList', group: 'other', loading: false, reload: true })
                        }*/

                        commit('UPDATE_LIST', {
                            list,
                            items: found
                        })
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
        if(list === 'ticketList' && item.id) {
            let hasMatch = false
            const ticketOtherList = state['ticketOtherList']

            for(const val of Object.values(allList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }
            for(const val of Object.values(ticketOtherList)) {
                if(!val || !Array.isArray(val.results)) continue
                for(const r of val.results) {
                    if(r?.id === item.id) {
                        hasMatch = true
                        break
                    }
                }
                if(hasMatch) break
            }

            if(!hasMatch) return

            try {
                const { data } = await axios.get('/help_desk/tickets/my_day/', {
                    params: {
                        id: item.id
                    }
                })
                if(data?.results?.length) {
                    const found = []
                    let hasExpandedCard = false

                    for(const backendItem of data.results) {
                        for(const [key, val] of Object.entries(allList)) {
                            if(!val || !Array.isArray(val.results)) continue
                            const idx = val.results.findIndex(r => r?.id === backendItem?.id)
                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                if(oldItem?.collapse) hasExpandedCard = true
                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...backendItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                        for(const [key, val] of Object.entries(ticketOtherList)) {
                            if(!val || !Array.isArray(val.results)) continue
                            const idx = val.results.findIndex(r => r?.id === backendItem?.id)
                            if(idx !== -1) {
                                const oldItem = val.results[idx]
                                if(oldItem?.collapse) hasExpandedCard = true
                                found.push({
                                    key,
                                    index: idx,
                                    oldItem,
                                    newItem: {
                                        ...backendItem,
                                        collapse: oldItem.collapse,
                                        actions: oldItem.actions
                                    }
                                })
                            }
                        }
                    }

                    let actualActions = null
                    if(hasExpandedCard) {
                        try {
                            const { data: actionInfo } = await axios.get(`/help_desk/tickets/${item.id}/action_info/`)
                            if(actionInfo?.actions)
                                actualActions = actionInfo.actions
                        } catch(error) {
                            errorHandler({error, show: false})
                        }
                    }
                    if(actualActions) {
                        for(const foundItem of found) {
                            foundItem.newItem.actions = actualActions
                        }
                    }

                    if(found.length) {
                        commit('UPDATE_LIST', {
                            list,
                            items: found
                        })
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
        dispatch('getAllDayStatistics')
    },
    async getAllDayStatistics({ commit, state }) {
        for(const key in state.day_statistics) {
            let source
            try {
                if(allDayCancelSource)
                    allDayCancelSource.cancel()
                source = await axiosMain.CancelToken.source()
                allDayCancelSource = { cancel: source.cancel }

                commit('STAT_LOADING', { storeKey: key, value: true })
                const params = {
                    start: dateFormat(state.mainDate[key][0]),
                    end: dateFormat(state.mainDate[key][1])
                }
                if(state.project[key])
                    params.project = state.project[key].id
                if(state.role[key])
                    params.role = state.role[key]
                if(state.workgroup[key])
                    params.workgroup = state.workgroup[key].id
                if(state.user[key]?.length)
                    params.user = state.user[key].map(user => user.id).join(',')
                const { data } = await axios.get('/estimates/accumulation_register/my_day_statistics/', {params, cancelToken: source.token})
                if(data) {
                    commit('SET_STAT', {
                        storeKey: key,
                        data
                    })
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                if(allDayCancelSource = source)
                    allDayCancelSource = null
                commit('STAT_LOADING', { storeKey: key, value: false })
            }
        }
    },
    async getDayStatistics({ commit, state }, { storeKey }) {
        let source;
        try {
            if(dayCancelSource)
                dayCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            dayCancelSource = { cancel: source.cancel }

            commit('STAT_LOADING', { storeKey, value: true })
            const params = {
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1])
            }
            if(state.project[storeKey])
                params.project = state.project[storeKey].id
            if(state.role[storeKey])
                params.role = state.role[storeKey]
            if(state.workgroup[storeKey])
                params.workgroup = state.workgroup[storeKey].id
            if(state.user[storeKey]?.length)
                params.user = state.user[storeKey].map(user => user.id).join(',')
            const { data } = await axios.get('/estimates/accumulation_register/my_day_statistics/', {params, cancelToken: source.token})
            if(data) {
                commit('SET_STAT', {
                    storeKey,
                    data
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        } finally {
            if(dayCancelSource === source)
                dayCancelSource = null
            commit('STAT_LOADING', { storeKey, value: false })
        }
    },
    async getWorkHoursSummaryReportSetting({ commit }, { storeKey }) {
        let source
        try {
            if(reportSettingCancelSource)
                reportSettingCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            reportSettingCancelSource = { cancel: source.cancel }

            const params = {
                filters: JSON.stringify({
                    code: 'work_hours_summary'
                })
            }
            const { data } = await axios.get('/reports/report_settings/', { params, cancelToken: source.token })
            const reportSetting = data?.results?.[0] || null

            commit('CHANGE_FIELD', {
                storeKey,
                field: 'reportSettings',
                value: reportSetting
            })
        } catch(error) {
            errorHandler({error, show: false})
        } finally {
            if(reportSettingCancelSource === source)
                reportSettingCancelSource = null
        }
    },
    async getAIIntents({ commit, state }, { storeKey }) {
        let source;
        try {
            if(intentsCancelSource)
                intentsCancelSource.cancel()
            source = await axiosMain.CancelToken.source()
            intentsCancelSource = { cancel: source.cancel }

            commit('STAT_AI_LOADING', { storeKey, value: true })
            const params = {
                start: dateFormat(state.mainDate[storeKey][0]),
                end: dateFormat(state.mainDate[storeKey][1])
            }
            const { data } = await axios.get('/meetings/sections/my_day_intents_statistics/', {params, cancelToken: source.token})
            if(data) {
                commit('SET_AI_INTENTS', {
                    storeKey,
                    data
                })
            }
        } catch(error) {
            errorHandler({error, show: false})
        } finally {
            if(intentsCancelSource === source)
                intentsCancelSource = null
            commit('STAT_AI_LOADING', { storeKey, value: false })
        }
    }
}
