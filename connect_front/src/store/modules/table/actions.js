import axios from '@/config/axios'
import { getDataAll } from '@/indexedDb/filter'
import { replacePath, fieldWidgetType } from '@/utils'
import { v1 as uuidv1 } from 'uuid'
import { setData, getById, updateById } from '@/utils/cacheDb.js'

export default {
    init({ commit }, { data }) {
        getDataAll()
            .then(dbData => {
                if(dbData?.length) {
                    commit('GENERATE_SORT', dbData)
                }
            })
            .catch((e) => { console.log(e) })

        let tableList = {}

        data.forEach(p => {
            if(p?.children?.length) {
                p.children.forEach(c => {
                    const { meta, name } = c

                    if(meta.pageWidget === 'PageTable' && meta.pageConfig?.tableInfo?.length) {
                        const { pageConfig } = meta

                        let tableArray = []

                        pageConfig.tableInfo.forEach(table => {
                            tableArray.push({
                                ...table,
                                name
                            })
                        })

                        tableList[name] = tableArray
                    }
                })
            }
        })

        commit('SET_ALL_TABLE_LIST', tableList)
    },
    generateTableData({ commit, state }, { key }) {
        if(!state.tableData?.[key])
            commit('GENERATE_TABLE_DATA', { key })
    },
    setupSort({ commit }, { key, sort }) {
        let sortModel = []

        if(sort?.length) {
            sort.forEach(item => {
                const ord = `${(item.sort === 'asc') ? '' : '-'}` + item.colId
                sortModel.push(ord)
            })
        }

        commit('ADD_SORT', {
            key,
            sort: sortModel
        })
    },
    getTableFlatData({ commit, state }, { key, dataPath, id, fParams, focusRow, fUpdate }) {
        return new Promise((resolve, reject) => {
            const checkData = () => {
                if(fUpdate) {
                    return false
                } else {
                    if(fParams) {
                        if(state.tableData?.[key]?.[id]?.[focusRow.id])
                            return true
                        else
                            return false
                    } else {
                        if(state.tableData?.[key]?.[id])
                            return true
                        else
                            return false
                    }
                }
            }

            if(checkData()) {
                resolve(true)
            } else {
                const path = replacePath({path: dataPath, params: { id }})
                let params = {}

                if(fParams) {
                    params['filters'] = fParams
                    params['no_pagination'] = true
                }

                axios.get(path, { params })
                    .then(({data}) => {
                        if(fParams)
                            commit('SET_TABLE_DATA_DEPENDENT', {
                                data,
                                key,
                                id,
                                focusRow
                            })
                        else
                            commit('SET_TABLE_DATA', {
                                data,
                                key,
                                id
                            })
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    flatTableDelete({ commit }, { item, key, id, dTableKey, dTable }) {
        commit('TABLE_COUNT_DECREMENT', { key, id })
        commit('FLAT_DELETE_ITEM', { key, item, id, dTableKey, dTable })
    },
    flatTableAdd({ commit }, { column, key, id, formName }) {
        let newItem = {
            newItem: true
        }

        column.forEach(col => {
            newItem[col.field] = fieldWidgetType(col)
        })

        newItem.id = uuidv1()

        commit('TABLE_COUNT_INCREMENT', { key, id })
        commit('FLAT_ADD_ITEM', {
            key,
            id,
            newItem
        })
        commit('form/ADD_TABLE_VALUES', {
            key,
            id,
            value: newItem,
            formName
        }, { root: true })
    },
    flatTableComputed({ commit }, { value, key, id, colKey, itemData, dTableKey, dTable, tableComputed, formName, params, toField }) {
        for (let fKey in tableComputed) {
            const filter = tableComputed[fKey].filter(f => f.field === colKey)
            if(filter.length) {
                let data = itemData
                data[colKey] = value

                filter.forEach(item => {
                    let fValue = item.formula

                    fValue.replace(/\<(.*?)\>/g, (match, pattern) => {
                        fValue = fValue.replace(`<${pattern}>`, data[pattern])
                        return match
                    })
                    
                    commit('UPDATE_ROW_COL_BY_KEY', {
                        value: eval(fValue), 
                        key, 
                        id, 
                        colKey: fKey, 
                        itemData, 
                        dTableKey, 
                        dTable
                    })
                    
                    let prm = {
                        ...params,
                        colDef: {
                            ...params.colDef,
                            field: fKey
                        }
                    }
                    prm.colDef.field = fKey
                    commit('form/EDIT_TABLE_VALUE', {
                        id,
                        value: eval(fValue),
                        key,
                        formName,
                        params: prm,
                        toField,
                        dTableKey,
                        dTable
                    }, { root: true })
                })
            }
        }
    },
    setTableInfo({ state, commit }, params) {
        const 
            databaseName = 'table',
            tableName = params.model + params.page_name + params.table_type
        let rowData = params.settings
        
        try {
            getById({ 
                id: tableName, 
                databaseName: databaseName
            }).then(DBData => {
                rowData = { [tableName]: rowData }
                if(DBData?.value) {
                    updateById({
                        id: tableName,
                        value: rowData,
                        databaseName: databaseName
                    })
                } else {
                    setData({
                        data: {
                            id: tableName,
                            value: rowData
                        },
                        databaseName: databaseName
                    })
                }
            })
            commit('SET_TABLE_INFO', {
                key: tableName,
                data: rowData
            })

        } catch(error) {
            console.log(error)
        } 
    },
    getTableInfo({ state, commit }, params) {  
        const 
            databaseName = 'table',
            tableName = params.model + params.page_name + params.table_type 
        
        return new Promise((resolve, reject) => {
            if(state.tablesInfo?.[tableName]?.columns?.length)
                resolve(state.tablesInfo?.[tableName])
            else {
                getById({ 
                    id: tableName, 
                    databaseName: databaseName
                })
                    .then(dbData => {
                        if(dbData?.value?.[tableName]?.columns?.length) {
                            commit('SET_TABLE_INFO', {
                                key: tableName,
                                data: dbData.value[tableName]
                            })
                            resolve(dbData.value[tableName])
                        } else {
                            // TODO
                            axios.get('/table_info/', { 
                                params: { 
                                    model: params.model,
                                    page_name: params.page_name,
                                    table_type: params.table_type
                                },
                            })
                                .then(({ data }) => {
                                    if(dbData?.value) {
                                        const val = dbData.value
                                        val[tableName] = data
                                        updateById({
                                            id: tableName,
                                            value: val,
                                            databaseName: databaseName
                                        })
                                    } else {
                                        setData({
                                            data: {
                                                id: tableName,
                                                value: {
                                                    [tableName]: data
                                                }
                                            },
                                            databaseName: databaseName
                                        })
                                    }
                                    
                                    commit('SET_TABLE_INFO', {
                                        key: tableName,
                                        data: data                                    
                                    })
                                    resolve(data)
                                })
                                .catch((error) => {
                                    reject(error)
                                })
                        }
                    })
                    .catch(error => {
                        console.error(error)
                        reject(error)
                    })
            }
        })
    },
}