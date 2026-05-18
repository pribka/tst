import Vue from 'vue'
import { setData, getDataById, updateDataById, deleteDataById } from '@/indexedDb/filter'
export default {
    GENERATE_COLS_RULES(state, { key, id, cols }) {
        if(!state.tableColsRules?.[key]?.[id]) {
            let rules = {}
            cols.forEach(col => {
                if(col?.cellEditorParams?.rulesConfig?.length) {
                    const { field, cellEditorParams: { rulesConfig } } = col
                    Vue.set(rules, field, rulesConfig)
                }
            })
            if(Object.keys(rules)?.length) {
                Vue.set(state.tableColsRules, key, {
                    [id]: rules
                })
            }
        }
    },
    CHANGE_TABLE_FOCUS_BY_ID(state, { colKey, rowIndex, key, id }) {
        if(state.focusCache?.[key]) {
            Vue.set(state.focusCache[key], id, {
                colKey,
                rowIndex
            })
        } else {
            Vue.set(state.focusCache, key, {
                [id]: {
                    colKey,
                    rowIndex
                }
            })
        }
    },
    CHANGE_TABLE_NODE_FOCUS(state, { data, key, id }) {
        if(state.tableRowFocus?.[key]) {
            Vue.set(state.tableRowFocus[key], id, data)
        } else {
            Vue.set(state.tableRowFocus, key, {
                [id]: data
            })
        }
    },
    CLEAR_FLAT_TABLE_DATA(state, { key, id }) {
        if(state.tableData?.[key]?.[id]?.results?.length)
            Vue.delete(state.tableData[key], id)
    },
    SET_TABLE_DATA_DEPENDENT(state, { data, key, id, focusRow }) {
        if(state.tableData?.[key]) {
            if(state.tableData[key]?.[id]) {
                Vue.set(state.tableData[key][id], focusRow.id, {
                    results: data,
                    count: data.length
                })
            } else {
                Vue.set(state.tableData[key], id, {
                    [focusRow.id]: {
                        results: data,
                        count: data.length
                    }
                })
            }
        } else {
            Vue.set(state.tableData, key, {
                [id]: {
                    [focusRow.id]: {
                        results: data,
                        count: data.length
                    }
                }
            })
        }
    },
    SET_TABLE_DATA(state, { data, key, id }) {
        if(state.tableData?.[key]) {
            Vue.set(state.tableData[key], id, {
                results: data,
                count: data.length
            })
        } else {
            Vue.set(state.tableData, key, {
                [id]: {
                    results: data,
                    count: data.length
                }
            })
        }
    },
    SET_TABLE_COLS(state, { value, key }) {
        state.tableCols[key] = value
    },
    SET_ALL_TABLE_LIST(state, values) {
        state.tableList = values
    },
    SET_TABLE_DATA_COUNT(state, { key, count }) {
        state.tableData[key].count = count
    },
    CLEAR_TABLE_DATA(state, key) {
        if(state.tableData?.[key])
            Vue.set(state.tableData, key, { count: 0, results: [] })
    },
    SPLICE_TABLE_DATA(state, { start, item, key }) {
        state.tableData[key].results.splice(start, 1, item)
    },
    PUSH_TABLE_DATA(state, { item, key }) {
        state.tableData[key].results.push(item)
    },
    GENERATE_TABLE_DATA(state, { key }) {
        Vue.set(state.tableData, key, { count: 0, results: [] })
    },
    ADD_FOCUS_CACHE(state, { value, key }) {
        Vue.set(state.focusCache, key, value)
    },
    REMOVE_FOCUS_CACHE(state, { key }) {
        Vue.delete(state.focusCache, key)
    },
    TABLE_DATA_UPDATE(state, { key, values, id }) {
        if(state.tableData?.[key]?.[id]?.results?.length) {
            const tableData = state.tableData[key][id].results

            values.forEach(row => {
                const index = tableData.findIndex(f => f.id === row.uid)
                if(index !== -1) {
                    Vue.set(state.tableData[key][id].results, index, row)
                }
            })
        }
    },
    TABLE_MARK_TOGGLE(state, { key, field, value, params }) {
        const { node: { rowIndex } } = params

        if(state.tableData?.[key]?.results?.length && state.tableData[key].results?.[rowIndex]) {
            Vue.set(state.tableData[key].results[rowIndex], field, value)

            if(!value && state.tableData[key].results[rowIndex]?.is_posted)
                Vue.set(state.tableData[key].results[rowIndex], 'is_posted', false)
        }
    },
    TABLE_DATA_UPDATE_FIELD(state, { key, field, value, params }) {
        const { node: { rowIndex } } = params

        if(state.tableData?.[key]?.results?.length && state.tableData[key].results?.[rowIndex]) {
            Vue.set(state.tableData[key].results[rowIndex], field, value)
        }
    },
    ADD_SORT(state, { key, sort }) {
        if(sort?.length) {
            getDataById(key)
                .then(dbData => {
                    if(dbData) {
                        updateDataById({
                            id: key,
                            value: sort
                        })
                    } else {
                        setData({
                            id: key,
                            value: sort
                        })
                    }
                })
                .catch((e) => { console.log(e) })

            Vue.set(state.sortModel, key, sort)
        } else {
            if(state.sortModel[key]) {
                getDataById(key)
                    .then(dbData => {
                        if(dbData)
                            deleteDataById(key)
                    })
                    .catch((e) => { console.log(e) })

                Vue.delete(state.sortModel, key)
            }
        }
    },
    GENERATE_SORT(state, payload) {
        payload.forEach(sortModel => {
            Vue.set(state.sortModel, sortModel.id, sortModel.value)
        })
    },
    FLAT_ADD_ITEM(state, { key, newItem, id }) {
        if(state.tableData?.[key]) {
            if(state.tableData?.[key]?.[id]?.results?.length) {
                state.tableData[key][id].results.push(newItem)
            } else {
                Vue.set(state.tableData[key], id, {
                    results: [newItem],
                    count: 1
                })
            }
        } else {
            Vue.set(state.tableData, key, {
                [id]: {
                    results: [newItem],
                    count: 1
                }
            })
        }
    },
    FLAT_DELETE_ITEM(state, { key, item, id, dTableKey, dTable }) {
        if(dTable) {
            if(state.tableData?.[key]?.[id]?.[dTableKey.id]?.results) {
                const index = state.tableData[key][id][dTableKey.id].results.findIndex(f => f.id === item.id)
                if(index !== -1)
                    state.tableData[key][id][dTableKey.id].results.splice(index, 1)
            }
        } else {
            if(state.tableData?.[key]?.[id]?.results) {
                const index = state.tableData[key][id].results.findIndex(f => f.id === item.id)
                if(index !== -1)
                    state.tableData[key][id].results.splice(index, 1)
            }
        }
    },
    TABLE_COUNT_INCREMENT_BY_KEY(state, key) {
        if(state.tableData?.[key])
            Vue.set(state.tableData[key], 'count', state.tableData[key].count + 1)
    },
    TABLE_COUNT_INCREMENT(state, { key, id }) {
        if(state.tableData?.[key]?.[id])
            state.tableData[key][id].count++
    },
    TABLE_COUNT_DECREMENT(state, { key, id }) {
        if(state.tableData?.[key]?.[id])
            state.tableData[key][id].count--
    },
    UPDATE_ROW_COL_BY_KEY(state, { value, key, id, colKey, itemData, dTableKey, dTable }) {
        if(dTable) {
            const dID = dTableKey.id

            if(state?.tableData?.[key]?.[id]?.[dID]?.results?.length) {
                const index = state.tableData[key][id][dID].results.findIndex(f => f.id === itemData.id)
    
                if(index !== -1)
                    Vue.set(state.tableData[key][id][dID].results[index], colKey, value)
            }
        } else {
            if(state?.tableData?.[key]?.[id]?.results?.length) {
                const index = state.tableData[key][id].results.findIndex(f => f.id === itemData.id)
    
                if(index !== -1)
                    Vue.set(state.tableData[key][id].results[index], colKey, value)
            }
        }
    },
    SET_TABLE_UPDATE_SELECT(state, { key, data }) {
        Vue.set(state.tableUpdateSelect[key], key, data)
    },


    SET_TABLE_INFO(state, { key, data }) {
        Vue.set(state.tablesInfo, key, data)
    },
    SET_TABLE_SIZE(state, { key, data }) {
        Vue.set(state.tablesInfo[key], 'table_size', data)
    },
}