export default {
    getTableHead: (state) => (key) => state.tableCols[key],
    getTableList: (state) => (key) => state.tableList[key],
    getTable: (state) => ({key, name}) => {
        if(state.tableList[name]) {
            const find = state.tableList[name].find(f => f.key === key)
            return find ? find : null
        } else
            return null
    },
    getTableUpdate: state => key => {
        if(state.tableUpdate?.[key])
            return state.tableUpdate[key]
        else
            return null
    },
    getTableData: (state) => (key) => {
        if(state.tableData?.[key])
            return state.tableData[key]
        else
            return null
    },
    getTableDataById: (state) => (key, id, dep = null) => {
        if(dep) {
            if(state.tableData?.[key]?.[id]?.[dep.id])
                return state.tableData[key][id][dep.id]
            else
                return []
        } else {
            if(state.tableData?.[key]?.[id])
                return state.tableData[key][id]
            else
                return []
        }
    },
    getTableFocus: (state) => (key) => state.focusCache[key],
    getTableFocusById: (state) => (key, id) => {
        if(state.focusCache?.[key]?.[id])
            return state.focusCache[key][id]
        else
            return null
    },
    getSortModel: (state) => (key) => {
        if(state.sortModel?.[key]?.length)
            return state.sortModel[key]
        else
            return null
    },
    getFocusRow: state => (key, id, tableKey) => {
        if(state.tableRowFocus?.[key]?.[id])
            return state.tableRowFocus[key][id]
        else
            return null
    },
    getPinnedBottomRowData: state => ({key, id, columns}) => {
        const filters = columns.filter(f => f.cellRendererParams.fComputed),
            rowData = (row, data) => {
                const find = filters.find(f => f.field === row.field)
                if(find) {
                    let res = 0
                    data.forEach(item => {
                        if(item[row.field])
                            res = res + Number(item[row.field])
                    })

                    return res
                } else
                    return null
            }
        
        if(filters.length) {
            if(state.tableData?.[key]?.[id]?.results?.length) {
                const data = state.tableData[key][id].results
                let pinnedColumn = {}

                for (let col in columns) {
                    pinnedColumn[columns[col].field] = rowData(columns[col], data)
                }

                return [pinnedColumn]
            } else
                return null
        } else
            return null
    },
    getTableInfoByPageName: state => (pageName) => {
        return state.tablesInfo?.[pageName]
    },
    getTablePageSize: state => (tableName) => {
        // console.log(state.tablesInfo, [tableName])
        // if(state.tablesInfo?.[tableName]?.page_size)
        //     return state.tablesInfo[tableName].page_size
        return null
    }
}