import Vue from 'vue'
import { v1 as uuidv1 } from 'uuid'

function getActionRow(record=null) {
    return {
        id: 'add_'+uuidv1(), 
        is_action: true,
        parent: record?.id,
        parentTaskType: record?.task_type,
        indent: record?.indent || 0

    }
}
function findRecord(recordTree, id) {
    for (let i = 0; i < recordTree.length; i++) {
        const record = recordTree[i]
        if (record.id === id) { return { recordTree, index: i } }
        if (record?.children?.length) {
            const found = findRecord(record.children, id);
            if (found) return found;
        }
    }
    return null;
}

export default {
    UPDATE_TABLE_ROW(state, { record, tableKey }) {
        if (!state.tables?.[tableKey]) { return; }
        const found = findRecord(state.tables[tableKey].results, record.id)
        if (found) {
            Vue.set(found.recordTree, found.index, {
                ...record,
                children: found.recordTree[found.index].children,
            })
        }
    },
    DELETE_TABLE_ROW(state, { record, tableKey }) {
        if (!state.tables?.[tableKey]) { return; }
        const found = findRecord(state.tables[tableKey].results, record.id)
        if (found) {
            found.recordTree.splice(found.index, 1)
        }
    },
    ADD_TABLE_ROW(state, { record, tableKey }) {
        if (!state.tables?.[tableKey]) { return; }
        if (record?.parent?.id && state.tables?.[tableKey]?.results) {
            const found = findRecord(state.tables[tableKey].results, record.parent.id)
            if (record.task_type !== 'milestone') {
                Vue.set(record, 'children', [getActionRow(record)])
            }
            
            const recordTree = found?.recordTree?.[found?.index]
            if (recordTree) {
                recordTree?.children?.splice(0, 0, record)
            }
        } else {
            state.tables[tableKey].results.splice(1, 0, record)
        }
    },

    SET_TABLE_ROW_CHILDREN(state, { tableKey, data, parent }) {
        const found = findRecord(state.tables?.[tableKey].results, parent)
        Vue.set(found.recordTree[found.index], 'children', data.results)
    },
    SET_TABLE(state, { tableKey, data }) {
        Vue.set(state.tables, tableKey, data)
    },
    DROP_LIST(state, { tableKey }) {
        delete state.lists[tableKey]
    },
    SET_LIST(state, { tableKey, data }) {
        if (state.lists[tableKey]?.results) {
            state.lists[tableKey].results.push(...data.results)
        } else {
            Vue.set(state.lists, tableKey, data)
        }
    },
    MOVE_TEMPLATE_TASK(state, { id, direction }) {
        const found = findRecord(state.templateTable.results, id)
        const adjacentIndex = direction === 'up' ? found.index - 1 : found.index + 1
        const adjacentRecord = found.recordTree[adjacentIndex]
        if ((direction === 'up' && found.index === 0) 
            || (direction === 'down' && found.index === found.recordTree.length - 1)
            || adjacentRecord.is_action) {
            return;
        }
        const recordInList = found.recordTree.splice(found.index, 1)
        found.recordTree.splice(adjacentIndex, 0, ...recordInList)
    },
    SET_EDIT_TEMPLATE_TABLE_ROW(state, { id }) {
        const found = findRecord(state.templateTable.results, id)
        if (found) {
            Vue.set(found.recordTree[found.index], 'is_action', true)
            Vue.set(found.recordTree[found.index], 'edit_only', true)
        }
    },
    // Создание задачи из строки добавления
    UPDATE_TEMPLATE_TABLE_ROW(state, { value, id, indent }) {
        const found = findRecord(state.templateTable.results, id)
        if (found) {
            if (value.task_type !== 'milestone') {
                console.log('value', value)
                value.children = [{
                    id: 'add_' + uuidv1(),
                    is_action: true,
                    parent: value.id,
                    parentTaskType: value.task_type,
                    indent: indent
                }]
            }

            Vue.set(found.recordTree, found.index, value)
            // Если в таблице до этого не было записей, то добавляем снизу строку добавления
            if (state.templateTable.results.length === 2) {
                state.templateTable.results.push({
                    id: 'add_'+uuidv1(),  
                    is_action: true 
                })
            }
        }
    },
    EDIT_TEMPLATE_TABLE_ROW(state, { value, id }) {
        const found = findRecord(state.templateTable.results, id)

        if (found) {
            Vue.set(found.recordTree, found.index, {
                ...found.recordTree[found.index],
                ...value,
                edit_only: false,
                is_action: false,
            })
        }
    },
    ADD_TEMPLATE_TABLE_ROW(state, { task_type, record }) {
        const found = findRecord(state.templateTable.results, record.id)
        if (found) {
            const actionRecord = {
                id: 'add_' + uuidv1(),
                is_action: true,
                parent: record.parent,
                parentTaskType: record.task_type,
                indent: record.indent
            }
            if (record.id === state.templateTable.results[0].id) {
                found.recordTree.unshift(actionRecord)
            } else {
                found.recordTree.push(actionRecord)
            }
        }
    },
    REMOVE_TEMPLATE_TABLE_ROW(state, { id }) {
        const found = findRecord(state.templateTable.results, id)
        found.recordTree.splice(found.index, 1)
        // Если после удаления остались только верхняя и нижняя строки добавления, 
        // то убираем второую строку
        if (state.templateTable.results.length === 2) {
            state.templateTable.results.splice(1, 1)
        }
    },
    clearGroups(state) {
        state.listGroups = []
    },
    clearProjects(state) {
        state.listProjects = []
    },
    setLoading(state, value) {
        state.loading = value
    },
    SET_INFO(state, value) {
        state.workgroupData = value

    },
    SET_LIST_GROUPS(state, values) {
        state.listGroups = state.listGroups.concat(values.results)
    },
    SET_LIST_PROJECTS(state, values) {
        values.results.forEach((el) => {
            state.listProjects.push(el);
        });
    },
    UP_USER_DRAWER_PAGE(state) {
        state.userDrawer.page += 1
    },
    SET_USER_NEXT(state, value) {
        state.userDrawer.next = value
    },
    USER_CONCAT(state, value) {
        state.userDrawer.results = state.userDrawer.results.concat(value)
    },
    CLEAR_USER_LIST(state) {
        state.userDrawer = {
            results: [],
            next: true,
            count: 0,
            page: 0
        }
    },
    SET_GROUP_NEXT(state, value) {
        state.groupNext = value
    },
    // UPDATE_NEWS_LIST(state, value) {
    //     if(state.newsList?.results?.length) {
    //         const index = state.newsList.results.findIndex(f => f.id === value.id)
    //         if(index !== -1)
    //             Vue.set(state.newsList.results, index, value)
    //     }
    // },

    SET_TABLE_PAGE_SIZE(state, { tableName, pageSize }) {
        localStorage.setItem(`workgroupTable_${tableName}`, pageSize)
    },
    SET_TABLE_COLUMNS(state, { type, value }) {
        Vue.set(state.tableColumns, type, value)
    },
    SET_FORM_INJECT(state, data) {
        state.formInject = data
    }
}