export default {
    calendarTasks: s => s.taskCalendar,
    calendarEmptyTasks: s => s.taskCalendarEmpty,
    taskActions: state => (task_type = null, id = null) => {
        if(task_type && id && state.taskActions?.[task_type]?.[id])
            return state.taskActions[task_type][id]
        else
            return null
    },
    getTab: state => (id, part) => {
        return Object.keys(state.universalTabs).length && state.universalTabs?.[id]?.[part] ? state.universalTabs[id][part] : null
    },
    getTabForm: state => (id, part) => {
        return state.universalTabsForm?.[id]?.[part] ? state.universalTabsForm[id][part] : {}
    },
    getTabFormAccess: state => (id, part) => {
        return Object.keys(state.universalTabs).length && state.universalTabs?.[id]?.[part]?.accessRules ? state.universalTabs[id][part]?.accessRules : null
    },
    getTabTable: state => (id, part) => {
        return state.universalTabs?.[id]?.[part]?.tableInfo ? state.universalTabs[id][part].tableInfo : null
    },
    getTabList: state => (id, part) => {
        return state.universalTabsList?.[id]?.[part] ? state.universalTabsList[id][part] : null
    },
    getAsideStat: state => (id, part) => {
        return state.taskAsideStat?.[id]?.[part] ? state.taskAsideStat[id][part] : null
    },
    getGantActiveFilter: state => page_name => {
        return state.gantActiveFilter[page_name] ? state.gantActiveFilter[page_name] : 'mounth'
    },
    getTablePageSize: state => tableName => {
        const pageSize = Number(localStorage.getItem(`taskTable_${tableName}`))
        return pageSize 
    },
    getFormInfoByType: state => task_type => {
        return state.formInfo?.[task_type] || null
    }
}