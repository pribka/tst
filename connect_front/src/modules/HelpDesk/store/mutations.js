import Vue from 'vue'
import eventBus from '@/utils/eventBus'
export default {
    SET_SPRINT_ADD_TASK_SHOW(state, value) {
        state.sprintAddTaskShow = value
    },
    SET_PAGE_NAME(state, { pageName }) {
        state.pageName = pageName
    },
    SET_TASK_TYPE_ACTIVE_TAB(state, {task_type, code}) {
        Vue.set(state.taskTypeActiveTab, task_type, code)
    },
    SET_FORM_INFO_INIT(state, data) {
        Vue.set(state, 'formInfo', data)
    },
    SET_FORM_INFO(state, {data, task_type}) {
        Vue.set(state.formInfo, task_type, data)
    },
    SET_GANT_ACTIVE_FILTER(state, {type, page_name}) {
        Vue.set(state.gantActiveFilter, page_name, type)
    },
    SET_TASK_DRAWER_OPTIONS(state, value) {
        state.taskDrawerOptions = value
    },
    SET_ASIDE_STAT(state, {task, part, data}) {
        if(state.taskAsideStat?.[task.id]) {
            Vue.set(state.taskAsideStat[task.id], part, data)
        } else {
            Vue.set(state.taskAsideStat, task.id, {
                [part]: data
            })
        }
    },
    UPDATE_SHOW_TASK_SOCKET(state, data) {
        if(state.task && state.task.id === data.id) {
            Vue.set(state, 'task', {
                ...state.task,
                ...data
            })
        }
    },
    UPDATE_TASK_SOCKET(state, data) {
        const checkChildren = (item) => {
            if(item.children?.length) {
                const cIndex = item.children.findIndex(f => f.id === data.id)
                if(cIndex !== -1) {
                    Vue.set(item.children, cIndex, data)
                }

                item.children.forEach(cItem => {
                    checkChildren(cItem)
                })
            }
        }

        if(Object.keys(state.taskList)?.length) {
            for(const key in state.taskList) {
                const index = state.taskList[key].findIndex(f => f.id === data.id)
                if(index !== -1) {
                    Vue.set(state.taskList[key], index, data)
                }

                state.taskList[key].forEach(item => {
                    checkChildren(item)
                })
            }
        }

        if(state.taskCalendarEmpty?.length) {
            const index = state.taskCalendarEmpty.findIndex(f => f.id === data.id)
            if(index !== -1) [
                Vue.set(state.taskCalendarEmpty, index, {
                    ...data,
                    id: data.id,
                    title: data.name,
                    date: data.dead_line,
                    dead_line: data.dead_line,
                    date_start_plan: data.date_start_plan,
                    project: data.project,
                    parent: data.parent,
                    operator: data.operator,
                    counter: data.counter,
                    author: data.author,
                    owner: data.owner,
                    description: data.description,
                    priority: data.priority,
                    status: data.status,
                    is_auction: data.is_auction ? data.is_auction : false
                })
            ]
        }
        if(state.taskCalendar?.length) {
            const index = state.taskCalendar.findIndex(f => f.id === data.id)
            if(index !== -1) {
                Vue.set(state.taskCalendar, index, {
                    ...data,
                    title: data.name,
                    counter: data.counter,
                    date: data.dead_line,
                    dead_line: data.dead_line,
                    date_start_plan: data.date_start_plan,
                    operator: data.operator,
                    project: data.project,
                    parent: data.parent,
                    author: data.author,
                    owner: data.owner,
                    description: data.description,
                    priority: data.priority,
                    status: data.status,
                    is_auction: data.is_auction ? data.is_auction : false
                })
            }
        }
    },
    UPDATE_SHOW_TASK(state, data) {
        if(state.task) {
            Vue.set(state, 'task', {
                ...state.task,
                ...data
            })
        }
    },
    ADD_UNIVERSAL_TAB_LIST_DATA(state, {data, task, part}) {
        if(state.universalTabsList?.[task.id]?.[part]) {
            state.universalTabsList[task.id][part].results.unshift(data)
            state.universalTabsList[task.id][part].count += 1
        }
    },
    SET_UNIVERSAL_TAB_LIST(state, {data, task, part}) {
        if(state.universalTabsList?.[task.id]) {
            Vue.set(state.universalTabsList[task.id], part, data)
        } else {
            Vue.set(state.universalTabsList, task.id, {
                [part]: data
            })
        }
    },
    GENERATE_UNIVERSAL_TAB_LIST(state, {task, part}) {
        if(state.universalTabsList?.[task.id]) {
            Vue.set(state.universalTabsList[task.id], part, {
                count: 0,
                next: true,
                results: []
            })
        } else {
            Vue.set(state.universalTabsList, task.id, {
                [part]: {
                    count: 0,
                    next: true,
                    results: []
                }
            })
        }
    },
    SET_UNIVERSAL_TAB(state, {data, task, part}) {
        if(state.universalTabs?.[task.id]) {
            Vue.set(state.universalTabs[task.id], [part], data)
            if(data.columns?.formInfo?.form) {
                if (!state.universalTabsForm?.[task.id]) {
                    Vue.set(state.universalTabsForm, task.id, null)
                }
                Vue.set(state.universalTabsForm[task.id], [part], JSON.parse(JSON.stringify(data.columns.formInfo.form)))
            }
        } else {
            Vue.set(state.universalTabs, task.id, {
                [part]: data.columns
            })
            if(data.columns?.formInfo?.form) {
                Vue.set(state.universalTabsForm, task.id, {
                    [part]: JSON.parse(JSON.stringify(data.columns.formInfo.form))
                })
            }
        }
    },
    CLEAR_UNIVERSAL_TAB_FORM(state,{task, part}) {
        if(state.universalTabs?.[task.id]?.[part]) {
            const form = JSON.parse(JSON.stringify(state.universalTabs[task.id][part].formInfo.form))
            Vue.set(state.universalTabsForm[task.id], part, form)
        }
    },
    SET_UNIVERSAL_TAB_FORM(state,{value, task, part}) {
        Vue.set(state.universalTabsForm, task.id, {
            [part]: value
        })
    },
    SET_STATUS_LOADER(state, value) {
        state.statusLoader = value
    },
    SET_STATUS_LIST(state, {data, task_type}) {
        Vue.set(state.statusList, task_type, data)
    },
    SET_TASK_ACTIONS(state, {data, task_type, id}) {
        if(state.taskActions[task_type]) {
            Vue.set(state.taskActions[task_type], id, data)
        } else {
            const newData = {
                [id]: data
            }
            Vue.set(state.taskActions, task_type, newData)
        }
    },
    CLEAR_TASK_ACTIONS(state, { task_type, id }) {
        if(state.taskActions[task_type]?.[id]) {
            Vue.delete(state.taskActions[task_type], id)
        }
    },
    SET_WORK_TIME_SETTINGS(state, {data, task_type}) {
        let config = data

        if(config.formInfo?.length) {
            config.form = {}
            config.formInfo.forEach(item => {
                config.form[item] = true
            })
        }

        Vue.set(state.workTimeSettings, task_type, config)
    },
    SET_TASK_TABLE(state, {data, task_type}) {
        Vue.set(state.taskTable, task_type, data)
    },
    SET_TASK_DRAWER_ZINDEX(state, value) {
        state.taskDrawerZIndex = value
    },
    SET_SPRINT_DRAWER_ZINDEX(state, value) {
        state.sprintDrawerZIndex = value
    },
    SET_MAIN_KEY(state, key) {
        state.mainKey = key
    },
    CHANGE_EMDED_TASK_SHOW(state, value) {
        if (!value)
            state.taskDrawerZIndex = 1000

        state.emdedTaskShow = value
    },
    CHANGE_TASK_SHOW(state, value) {
        if (!value)
            state.taskDrawerZIndex = 1000

        state.taskShow = value
    },
    CHANGE_SPRINT_SHOW(state, value) {
        if (!value)
            state.taskDrawerZIndex = 1000

        state.sprintShow = value
    },
    SET_EDIT_DRAWER(state, value) {
        if (!value)
            state.taskDrawerZIndex = 1000

        state.editDrawer = value
    },
    SET_HARD_INDEX(state, value) {
        state.hardZIndex = value
    },
    SET_FORM_DEFAULT(state, payload) {
        state.formDefault = payload
    },
    SET_TASK(state, value) {
        state.task = value
        if(value?.lead_source?.id) {
            state.task.lead_source = value.lead_source.id
        }
    },
    CLEAR_CALENDAR_TASK(state) {
        state.taskCount = {}
        state.taskCalendar = []
    },
    ADD_TASK_CALENDAR(state, el) {
        const obj = {
            id: el.id,
            title: el.name,
            date: el.dead_line,
            dead_line: el.dead_line,
            date_start_plan: el.date_start_plan,
            project: el.project,
            parent: el.parent,
            counter: el.counter,
            operator: el.operator,
            author: el.author,
            owner: el.owner,
            description: el.description,
            priority: el.priority,
            status: el.status,
            is_auction: el.is_auction ? el.is_auction : false

        }
        if (obj.date !== null) {
            state.taskCalendar.push(obj)
        } else {
            state.taskCalendarEmpty.unshift(obj)
        }
    },
    CONCAT_TASK_LIST(state, { data, key }) {
        if (!state.taskList[key])
            Vue.set(state.taskList, key, [])

        state.taskList[key] = state.taskList[key].concat(data.results)
        Vue.set(state.next, key, data.next)
    },
    SET_TABLE_EMPTY(state, { key, data }) {
        Vue.set(state.tableEmpty, key, data)
    },
    SET_TASK_LIST(state, { data, key }) {
        if (data.results) {
            Vue.set(state.taskList, key, data.results)
            if (data.count)
                Vue.set(state.taskCount, key, data.count)

            Vue.set(state.next, key, data.next)
        } else {
            Vue.set(state.taskList, key, [])
        }
    },
    SET_TASK_CALENDAR(state, { data, key }) {
        const newData = data.results.map(el => {
            return {
                id: el.id,
                title: el.name,
                counter: el.counter,
                date: el.dead_line,
                dead_line: el.dead_line,
                date_start_plan: el.date_start_plan,
                operator: el.operator,
                project: el.project,
                parent: el.parent,
                author: el.author,
                owner: el.owner,
                description: el.description,
                priority: el.priority,
                status: el.status,
                is_auction: el.is_auction ? el.is_auction : false
            }
        })
        state.taskCalendar = newData
    },
    TASK_CLEAR_CHILD(state, task) {
        Vue.delete(task, 'children')
    },
    TASK_UPDATE_CHILD(state, { task, data }) {
        Vue.set(task, 'children', data.results)
    },
    UPDATE_TASK_CALENDAR(state, { data }) {
        state.taskCalendarEmpty = state.taskCalendarEmpty.filter(el => el.id !== data.id)
        state.taskCalendar = state.taskCalendar.filter(el => el.id !== data.id)
        const obj = {
            id: data.id,
            title: data.name,
            date: data.dead_line,
            dead_line: data.dead_line,
            date_start_plan: data.date_start_plan,
            project: data.project,
            parent: data.parent,
            counter: data.counter,
            operator: data.operator,
            author: data.author,
            owner: data.owner,
            description: data.description,
            priority: data.priority,
            status: data.status,
            is_auction: data.is_auction ? data.is_auction : false
        }
        state.taskCalendar.push(obj)
    },
    CONCAT_TASK_NODEADLINE(state, { data }) {
        const newData = data.results.map(el => {
            return {
                id: el.id,
                title: el.name,
                date: el.dead_line,
                dead_line: el.dead_line,
                date_start_plan: el.date_start_plan,
                project: el.project,
                parent: el.parent,
                operator: el.operator,
                counter: el.counter,
                author: el.author,
                owner: el.owner,
                description: el.description,
                priority: el.priority,
                status: el.status,
                is_auction: el.is_auction ? el.is_auction : false
            }
        })
        state.taskCalendarEmpty = state.taskCalendarEmpty.concat(newData)
    },
    SET_TASK_NODEADLINE(state, { data }) {
        const newData = data.results.map(el => {
            return {
                id: el.id,
                title: el.name,
                date: el.dead_line,
                dead_line: el.dead_line,
                date_start_plan: el.date_start_plan,
                operator: el.operator,
                counter: el.counter,
                project: el.project,
                parent: el.parent,
                author: el.author,
                owner: el.owner,
                description: el.description,
                priority: el.priority,
                status: el.staus,
                is_auction: el.is_auction ? el.is_auction : false
            }
        })
        state.taskCalendarEmpty = newData
    },
    CLEAR_CALENDAR(state) {
        state.taskCalendarEmpty = []
        state.taskEmptyNext = true
    },
    TASK_UPDATE_FILES(state, value) {
        Vue.set(state.task, 'attachments', value)
    },
    SET_EMPTY_NEXT(state, value) {
        state.taskEmptyNext = value
    },
    SET_TASK_TYPE(state, value) {
        state.taskType = value
    },
    SET_CURRENT_TASK_LIST_PAGE(state, { page, key }) {
        if (!state.taskPages[key])
            Vue.set(state.taskPages, key, page)
        else
            state.taskPages[key] = page
    },
    SET_TABLE_PAGE_SIZE(state, {tableName, pageSize}) {
        localStorage.setItem(`taskTable_${tableName}`, pageSize)
    },

    // Точки для задач
    SET_TASK_POINT_LIST(state, list) {
        state.taskPointsList = list
    },
    RESET_POINT_FORM_DATA(state) {
        state.pointFormData = {
            name: '',
            lat: null,
            lon: null,
            address: ''
        }
    },
    ADD_TO_TASK_POINT_LIST(state, point) {
        state.taskPointsList.unshift(point)
        this.commit('task/RESET_POINT_FORM_DATA')
    },
    DELETE_FROM_TASK_POINT_LIST(state, point) {
        const index = state.taskPointsList.findIndex(f => f === point)
        if(index !== -1) {
            state.taskPointsList.splice(index, 1)
        }
    },
    SET_MARKED_POINT(state, value) {
        state.markedPoint = {...value}
    },
    SET_SEARCH_MARKER(state, value) {
        state.searchMarker = {...value}
    },
    SET_MARKERS_LIST(state, pointList) {
        pointList.forEach(point => {
            state.markersList.push([point.lat, point.lon])
        })
    },
    RESET_MARKERS_LIST(state) {
        state.markersList = []
    },
    SET_MAP_CONFIG(state, config) {
        state.mapConfig = config
    },
    SET_LEAD_SOURCES(state, data) {
        state.leadSources = data
    },
    SET_LEAD_SOURCES_LOADER(state, data) {
        state.leadSourcesLoader = data
    },
    SET_REJECTION_REASON_LIST(state, data) {
        state.rejectionReasonList = data
    },
    SET_REJECTION_REASON_LIST_LOADER(state, data) {
        state.rejectionReasonListLoader = data
    },
    SET_NEW_REJECTION_REASON(state, {task_index, reason}) {
        state.taskList['interest-interest'][task_index]['rejection_reason'] = reason
    },

    // KANBAN SLIDER
    SET_MOBILE_SLIDE_INDEX(state, {slideIndex, pageName}) {
        localStorage.setItem(`task_mobile_slide_index_${pageName}`, slideIndex)
        Vue.set(state.mobileSlideIndex, pageName, slideIndex)
    },
    INIT_MOBILE_SLIDE_INDEX(state, pageName) {
        const slideIndex = localStorage.getItem(`task_mobile_slide_index_${pageName}`) || 0
        Vue.set(state.mobileSlideIndex, pageName, slideIndex)
    },
}