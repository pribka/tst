export default {
    info: state => state.workgroupData,
    loading: state => state.loading,
    projects: state => state.listProjects,
    groups: state => state.listGroups,

    getTablePageSize: state => tableName => {
        const pageSize = Number(localStorage.getItem(`workgroupTable_${tableName}`))
        return pageSize 
    },
    tableColumns: state => type => {
        if(state.tableColumns?.[type]?.length) {
            return state.tableColumns[type]
        } else
            return []
    }
}