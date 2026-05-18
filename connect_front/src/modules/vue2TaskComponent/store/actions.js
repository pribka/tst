import axios from '@/config/axios'
import eventBus from '@/utils/eventBus'
import { setData, getById, updateById } from '../utils/indexedDB.js'
import state from './state.js'

const updateTaskMultipleFields = ({data, task, commit}) => {
    if(data?.update_fields) {
        for (let key in data.update_fields) {
            commit('TASK_CHANGE_FIELD', { 
                task, 
                key: key, 
                value: data.update_fields[key] 
            })
        }
    }
}

export default {
    initFormInfo({ commit }) {
        return new Promise((resolve, reject) => {
            getById({ 
                id: 'task_edit', 
                databaseName: 'task'
            })
                .then(dbData => {
                    if(dbData?.value) {
                        commit('SET_FORM_INFO_INIT', dbData.value)
                    }
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    getFormInfo({ commit, state }, {task_type}) {
        return new Promise((resolve, reject) => {
            if(state.formInfo?.[task_type]) {
                resolve(state.formInfo[task_type])
            } else {
                getById({ 
                    id: 'task_edit', 
                    databaseName: 'task'
                })
                    .then(dbData => {
                        if(dbData?.value?.[task_type]) {
                            commit('SET_FORM_INFO', {
                                data: dbData.value[task_type],
                                task_type
                            })
                            resolve(dbData.value[task_type])
                        } else {
                            axios.get('/tasks/form_info/', {
                                params: {
                                    task_type
                                }
                            })
                                .then(({ data }) => {
                                    commit('SET_FORM_INFO', {
                                        data,
                                        task_type
                                    })

                                    if(dbData?.value && Object.keys(dbData.value).length) {
                                        const newData = dbData.value
                                        newData[task_type] = data

                                        updateById({
                                            id: 'task_edit',
                                            value: newData,
                                            databaseName: 'task'
                                        })
                                    } else {
                                        setData({
                                            data: {
                                                id: 'task_edit',
                                                value: {
                                                    [task_type]: data
                                                }
                                            },
                                            databaseName: 'task'
                                        })
                                    }
                                    
                                    resolve(data)
                                })
                                .catch((error) => { reject(error) })
                        }
                    })
                    .catch(error => {
                        reject(error)
                    })
            }
        })
    },
    getCompleteStatus({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.completeStatus?.length) {
                resolve(state.completeStatus)
            } else {
                axios.get('/app_info/filtered_select_list/', {
                    params: {
                        model: 'tasks.TaskStatusModel',
                        page_size: 10,
                        page: 1,
                        filters: JSON.stringify({"task_status_type__task_type":"task", "task_status_type__is_complete":true})
                    }
                })
                    .then(({ data }) => {
                        if(data?.filteredSelectList?.length)
                            commit('SET_COMPLETE_STATUS', data.filteredSelectList)
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    savePoints({ commit }, {points, task}) {
        return new Promise((resolve, reject) => {
            axios.put(`/tasks/task/${task.id}/sort_delivery_points/`, {
                delivery_points: points.map(item => item.id)
            })
                .then(({ data }) => {
                    updateTaskMultipleFields({data, task: task ? task : state.task, commit})
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getAsideStat({ commit }, {part, task}) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/${part}/aggregate/`, {
                params: {
                    obj: task.id
                }
            })
                .then(({ data }) => {
                    commit('SET_ASIDE_STAT', {
                        data,
                        task,
                        part
                    })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getTabInfo({ commit, state }, {part, task}) {
        return new Promise((resolve, reject) => {
            if(state?.universalTabs?.[task.id]?.[part])
                resolve(state.universalTabs[task.id][part])
            else {
                const ver = this.state.isMobile ? 'mobile' : ''
                axios.get('/tasks/table_info/', {
                    params: {
                        part,
                        task_type: task?.task_type ? task.task_type : 'task',
                        ver: ver
                    }
                })
                    .then(({ data }) => {
                        commit('GENERATE_UNIVERSAL_TAB_LIST', {
                            task,
                            part
                        })
                        commit('SET_UNIVERSAL_TAB', {
                            data,
                            task,
                            part
                        })
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            }
        })
    },
    getTabList({ commit }, {task, code}) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/${code}/`, {
                params: {
                    task: task.id
                }
            })
                .then(({ data }) => {
                    commit('SET_UNIVERSAL_TAB_LIST', {
                        task,
                        data,
                        part: code
                    })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    deleteTabData({ state, dispatch }, { task, code, id }) {
        return new Promise((resolve, reject) => {
            if(state.universalTabsForm[task.id]?.[code]) {
                axios.post('/table_actions/update_is_active/', {
                    id,
                    is_active: false
                })
                    .then(({ data }) => {
                        eventBus.$emit(`universal_tab_delete_${task.id}_${code}`, id)
                        dispatch('getAsideStat', {
                            part: code, 
                            task
                        })
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            } else
                reject('form empty')
        })
    },
    cretaeTabData({ state, dispatch }, { task, code }) {
        return new Promise((resolve, reject) => {
            if(state.universalTabsForm[task.id]?.[code]) {
                axios.post(`/tasks/${code}/`, {
                    ...state.universalTabsForm[task.id][code],
                    task: task.id
                })
                    .then(({ data }) => {
                        eventBus.$emit(`universal_tab_add_${task.id}_${code}`, data)
                        dispatch('getAsideStat', {
                            part: code, 
                            task
                        })
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            } else
                reject('form empty')
        })
    },
    updateTabData({ state, dispatch }, { task, code }) {
        return new Promise((resolve, reject) => {
            if(state.universalTabsForm[task.id]?.[code]) {
                axios.put(`/tasks/${code}/${state.universalTabsForm[task.id][code].id}/`, {
                    ...state.universalTabsForm[task.id][code],
                    task: task.id
                })
                    .then(({ data }) => {
                        eventBus.$emit(`universal_tab_update_${task.id}_${code}`, data)
                        dispatch('getAsideStat', {
                            part: code, 
                            task
                        })
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            } else
                reject('form empty')
        })
    },
    getTaskActions({ commit }, { task_type, id }) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/${id}/action_info/`)
                .then(({ data }) => {
                    commit('SET_TASK_ACTIONS', {
                        data,
                        id,
                        task_type
                    })
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    async getWorkTimeSettings({ commit, state }, { task_type }) {
        try {
            if(state.workTimeSettings?.[task_type]?.length)
                return state.workTimeSettings[task_type]
            else {
                await axios.get('/tasks/time_tracking/table_info/', {
                    params: {
                        task_type
                    }
                })
                    .then(({ data }) => {
                        commit('SET_WORK_TIME_SETTINGS', {
                            data,
                            task_type
                        })
                    })
                    .catch((error) => { reject(error) })
            }
        } catch(e) {
            console.log(e, 'getWorkTimeSettings')
        }
    },
    getTaskTable({ state, commit }, { task_type, isDrop=false }) {

        return new Promise((resolve, reject) => {
            if(state.taskTable?.[task_type]?.columns?.length && !isDrop)
                resolve(state.taskTable[task_type])
            else {
                getById({ 
                    id: 'table', 
                    databaseName: 'task'
                })
                    .then(dbData => {
                        if(dbData?.value?.[task_type]?.columns?.length && !isDrop) {
                            commit('SET_TASK_TABLE', {
                                data: dbData.value[task_type],
                                task_type
                            })
                            resolve(dbData.value[task_type])
                        } else {
                            axios.get('/tasks/table_info/', { 
                                params: {
                                    task_type
                                } 
                            })
                                .then(({ data }) => {
                                    if(dbData?.value && !isDrop) {
                                        const val = dbData.value
                                        val[task_type] = data
                                        updateById({
                                            id: 'table',
                                            value: val,
                                            databaseName: 'task'
                                        })
                                    } else {
                                        setData({
                                            data: {
                                                id: 'table',
                                                value: {
                                                    [task_type]: data
                                                }
                                            },
                                            databaseName: 'task'
                                        })
                                    }
                                    
                                    commit('SET_TASK_TABLE', {
                                        data,
                                        task_type
                                    })
                                    resolve(data)
                                })
                                .catch((error) => {
                                    reject(error)
                                })
                        }
                    })
                    .catch(error => {
                        reject(error)
                    })
            }
        })
    },
    async setTableInfo({ state, commit }, { task_type, value }) {
        try {
            getById({ 
                id: 'table', 
                databaseName: 'task'
            }).then(DBData => {
                
                value = { [task_type]: value }
                if(DBData?.value) {
                    updateById({
                        id: 'table',
                        value: value,
                        databaseName: 'task'
                    })
    
                }
                else {
                    setData({
                        data: {
                            id: 'table',
                            value: value
                        },
                        databaseName: 'task'
                    })
                }
            })
        } catch(error) {
            console.log(error)
        } 
    },
    async getStatusList({ commit, state }, { task_type }) {
        try {
            commit('SET_STATUS_LOADER', true)
            if(state.statusList?.[task_type]?.length) {
                return state.statusList[task_type]
            } else {
                const {data} = await axios.get('/tasks/task_status/', {
                    params: {
                        task_type
                    }
                })
                commit('SET_STATUS_LIST', {
                    data,
                    task_type
                })
            }
        } catch(e) {
            console.log(e, 'getStatusList')
        } finally {
            commit('SET_STATUS_LOADER', false)
        }
    },
    updateTaskFiles({ commit, state }, file) {
        return new Promise((resolve, reject) => {
            let attachments = file.map(f => f.id),
                files = file

            if(state.task?.attachments?.length) {
                let oldFiles = state.task.attachments.map(f => f.id)
                attachments = oldFiles.concat(attachments)

                let oldFilesList = JSON.parse(JSON.stringify(state.task.attachments))
                
                files = oldFilesList.concat(files)
            }

            axios.patch(`/tasks/task/${state.task.id}/update/`, {attachments})
                .then(({ data }) => {
                    if (data) {
                        commit('TASK_UPDATE_FILES', files)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    sidebarOpen({ commit, dispatch }, payload) {
        if (payload)
            commit('SET_FORM_DEFAULT', payload)

        commit('SET_EDIT_DRAWER', true)
        dispatch('getLeadSources')
        dispatch('getRejectionReasons')
    },
    getChildren({ commit }, { task, childParams }) {
        return new Promise((resolve, reject) => {
            const params = {
                parent: task.id,
                ...(childParams || {})
            }

            axios.get('/tasks/task/list/', { params })
                .then(({ data }) => {
                    if (data) {
                        commit('TASK_UPDATE_CHILD', { task, data })
                    }
                    resolve(data)
                })
                .catch(reject)
        })
    },
    getFullTask({ commit, dispatch }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`/tasks/task/${id}/`)
                .then(({ data }) => {
                    if (data) {
                        if(data.task_points.length) {
                            commit('SET_TASK_POINT_LIST', data.task_points)
                        }
                        commit('SET_TASK', data)
                        dispatch('getLeadSources')
                        dispatch('getStatusList', {
                            task_type: data.task_type
                        })
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updateStatus({ commit, state }, { status, task = null }) {
        const taskData = task ? task : state.task
        eventBus.$emit('STATUS_TASK_KANBAN', { 
            task: taskData, 
            status 
        })
        eventBus.$emit('STATUS_TASK_H', { 
            task: taskData, 
            status 
        })
        eventBus.$emit('STATUS_TASK_H_INJECT', { 
            task: taskData, 
            status 
        })
        eventBus.$emit('STATUS_GANT_CHNAGE', { 
            task: taskData, 
            status 
        })
        commit('TASK_CHANGE_FIELD', { 
            task: taskData, 
            key: 'status', 
            value: status 
        })
        updateTaskMultipleFields({status, task: taskData, commit})
        eventBus.$emit('TASK_WIDGET_UPDATE', {
            ...taskData,
            status
        })
        eventBus.$emit(`task_update_actions_${taskData?.id}`)
        eventBus.$emit('global_timer_sync_required', {
            entity: 'task',
            entityId: taskData?.id,
            action: 'status_changed',
            status: status?.code || null
        })
    },
    changeStatus({ commit, state }, { status, task = null }) {
        return new Promise((resolve, reject) => {
            axios.put(`/tasks/task/${task ? task.id : state.task.id}/status/`, { 
                status: status.code 
            })
                .then(({ data }) => {
                    if (data) {
                        const taskData = task ? task : state.task
                        eventBus.$emit('STATUS_TASK_KANBAN', { 
                            task: taskData, 
                            status 
                        })
                        eventBus.$emit('STATUS_TASK_H', { 
                            task: taskData, 
                            status 
                        })
                        eventBus.$emit('STATUS_TASK_H_INJECT', { 
                            task: taskData, 
                            status 
                        })
                        eventBus.$emit('STATUS_GANT_CHNAGE', { 
                            task: taskData, 
                            status 
                        })
                        commit('TASK_CHANGE_FIELD', { 
                            task: taskData, 
                            key: 'status', 
                            value: status 
                        })
                        updateTaskMultipleFields({data, task: taskData, commit})
                        eventBus.$emit('TASK_WIDGET_UPDATE', {
                            ...taskData,
                            ...data,
                            status
                        })
                        eventBus.$emit(`task_update_actions_${taskData?.id}`)
                        eventBus.$emit('global_timer_sync_required', {
                            entity: 'task',
                            entityId: taskData?.id,
                            action: 'status_changed',
                            status: status?.code || null
                        })
                    }
                    resolve(task)
                })
                .catch((error) => { reject(error) })
        })
    },
    deleteTask({ commit }, task) {
        return new Promise((resolve, reject) => {
            axios.put('/tasks/task/delete/', { id: task.id })
                .then(({ data }) => {
                    if (data) {
                        commit('DELETE_TASK', task)
                        eventBus.$emit('TASK_WIDGET_DELETE', task)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    editDrawer({ commit }, value) {
        commit('SET_EDIT_DRAWER', value)
    },
    getTas({ commit, state, dispatch }, { 
        params, 
        infinite = false, 
        key, 
        page_name, 
        task_type, 
        apiUrl = null,
        endpoint = '' 
    }) {
        return new Promise((resolve, reject) => {
            let queryParams = {
                ...params,
                task_type: 'task'
            }

            if(apiUrl) {
                apiU = apiUrl
            }

            if(task_type)
                queryParams.task_type = task_type

            params.page_name ? queryParams['page_name'] = params.page_name : queryParams['page_name'] = `page_list_${task_type}_task.TaskModel` // page_calendar_tasks.TaskModel 
            const url = endpoint || '/tasks/task/list/'
            axios.get(url, { params: queryParams })
                .then(({ data }) => {
                    if (infinite){
                        commit('SET_CURRENT_TASK_LIST_PAGE', { page: params.page, key })
                        commit('CONCAT_TASK_LIST', { data, key })
                    } else {
                        if (data && data.results.length) {
                            if (state.tableEmpty)
                                commit('SET_TABLE_EMPTY', { data: false, key })

                            commit('SET_TASK_LIST', { data, key })
                        }
                        if (data && !data.results.length) {
                            commit('SET_TABLE_EMPTY', { data: true, key })
                            commit('SET_TASK_LIST', { data, key })
                        } else
                            commit('SET_TASK_LIST', { data, key })
                    }
                    
                    // ------------- УДАЛИТЬ -------------
                    dispatch('getStatusList', {
                        task_type: queryParams.task_type
                    })

                    resolve(data)
                })
                .catch((error) => {
                    commit('SET_TABLE_EMPTY', { data: true, key })
                    commit('SET_TASK_LIST', { data, key })
                    reject(error)
                })
        })
    },
    getTasCalendar({ commit, state, dispatch }, { params, infinite = false, key, page_name, task_type, apiUrl = null }) {
        return new Promise((resolve, reject) => {
            let queryParams = {
                ...params,
                task_type: 'task'
            }
            let apiU = '/tasks/task/list/'

            if(apiUrl) {
                apiU = apiUrl
            }

            if(task_type)
                queryParams.task_type = task_type

            params.page_name ? queryParams['page_name'] = params.page_name : queryParams['page_name'] = `page_list_${task_type}_task.TaskModel` // page_calendar_tasks.TaskModel 

            axios.get('/tasks/task/list/', { params: queryParams })
                .then(({ data }) => {
                    commit('SET_TASK_CALENDAR', { data, key })
                    
                    // ------------- УДАЛИТЬ -------------
                    dispatch('getStatusList', {
                        task_type: queryParams.task_type
                    })

                    resolve(data)
                })
                .catch((error) => {
                    commit('SET_TABLE_EMPTY', { data: true, key })
                    commit('SET_TASK_LIST', { data, key })
                    reject(error)
                })
        })
    },
    updateDeadline({ commit }, payload) {
        return new Promise((resolve, reject) => {
            const query = {
                ...payload
            }

            if(query.dead_line) {
                query.is_indefinite = false
            } else {
                query.is_indefinite = true
            }

            axios.patch(`/tasks/task/${payload.id}/update/`, query)
                .then(({ data }) => {
                    commit('UPDATE_TASK_CALENDAR', { data })
                    commit('UPDATE_TASK_CALENDAR_ACTIONS', data)

                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addTask({ commit, rootState, state }, payload) {
        return new Promise((resolve, reject) => {
            let form = Object.assign({}, payload),
                user = rootState.user.user
            if (form.dead_line)
                form.is_indefinite = false
            else
                form.is_indefinite = true

            if (form.task_type === 'milestone') {
                form.date_start_plan = form.dead_line
            }

            const idFields = ['parent', 'operator', 'owner', 'contractor', 'project', 'organization', 'workgroup', 'contract', 'customer_card']
            idFields.forEach(key => {
                if (!form[key]) return
                if (typeof form[key] === 'object') form[key] = form[key].id
            })

            if (form.visors.length) {
                form.visors = form.visors.map(item => item.id)
            }

            if (form.cooperators.length) {
                form.cooperators = form.cooperators.map(item => item.id)
            }
            
            if (form.attachments?.length) {
                let files = []
                form.attachments.forEach(file => {
                    if (file.path)
                        files.push(file.id)
                    else
                        files.push(file)
                })
                form.attachments = files
            }

            form.task_points = state.taskPointsList

            // return 0
            if(form.reason_model === 'order') {
                axios.post('/tasks/task/create_from_order/', 
                    {
                        task: form,
                        delivery_point: form.delivery_point,
                        order: form.reason_id,
                        start_point: form.start_point
                    })
                    .then(({ data }) => {
                        if (data) {
                            commit('ADD_TASK', { data, user })
                        }
                        resolve(data)
                    })
                    .catch((error) => { reject(error) })
            } else
                axios.post('/tasks/task/create/', form)
                    .then(({ data }) => {
                        if (data) {
                            commit('ADD_TASK', { data, user })
                        }
                        resolve(data)
                        commit('SET_TASK_POINT_LIST', [])
                    })
                    .catch((error) => { reject(error) })
        })
    },
    updateTask({ commit, state }, payload) {
        return new Promise((resolve, reject) => {
            const form = JSON.parse(JSON.stringify(payload))

            if (form.attachments?.length) {
                let attachments = []
                form.attachments.forEach(file => {
                    if (file.path)
                        attachments.push(file.id)
                    else
                        attachments.push(file)
                })
                form.attachments = attachments
            }

            if (form.dead_line)
                form.is_indefinite = false
            else
                form.is_indefinite = true


            const idFields = ['parent', 'operator', 'owner', 'contractor', 'project', 'organization', 'workgroup', 'contract', 'customer_card']
            idFields.forEach(key => {
                if (!form[key]) return
                if (typeof form[key] === 'object') form[key] = form[key].id
            })

            if (form.visors.length) {
                form.visors = form.visors.map(item => item.id)
            }

            if (form.cooperators.length) {
                form.cooperators = form.cooperators.map(item => item.id)
            }

            if (form.children && form.children.length)
                delete form.children

            form.task_points = state.taskPointsList

            if(form.task_type === 'milestone')
                form.date_start_plan = form.dead_line

            axios.put(`/tasks/task/${form.id}/update/`, form)
                .then(({ data }) => {
                    if (data) {
                        commit('UPDATE_TASK', data)
                        commit('SET_TASK_POINT_LIST', [])
                        eventBus.$emit('TASK_WIDGET_UPDATE', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getTaskNoDeadline({ commit }, { params }) {
        return new Promise((resolve, reject) => {
            axios.get('/tasks/task/calendar/', { params })
                .then(({ data }) => {
                    commit('SET_EMPTY_NEXT', data.next)
                    commit("CONCAT_TASK_NODEADLINE", { data })
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    takeAuctionTask({ commit }, { task }) {
        return new Promise((resolve, reject) => {
            axios.put(`tasks/task/${ task.id }/take/`)
                .then(({ data }) => {
                    commit('UPDATE_TASK', data)
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    getDeliveryPoints({ commit }, { taskId }) {
        return new Promise((resolve, reject) => {
            axios.get(`tasks/${taskId}/delivery_points/`)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    getDeliveryGoods({ commit }, { taskId }) {
        return new Promise((resolve, reject) => {
            axios.get(`tasks/${taskId}/goods/`)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    getMapConfig({commit}) {
        return new Promise((resolve, reject) => {
            axios.get('tasks/form_info/points/')
                .then((result) => {
                    if(result.status === 200) {
                        commit('SET_MAP_CONFIG', result.data)
                        resolve()
                    }
                })
                .catch((error) => {
                    reject(error)
                })
        })
    },
    getLeadSources({commit, state}) {
        if(state.taskType === 'interest' && state.leadSources.length === 0) {
            commit('SET_LEAD_SOURCES_LOADER', true)
            axios.get('tasks/form_info/lead_sources/')
                .then((result) => {
                    if(result.status === 200) {
                        commit('SET_LEAD_SOURCES', result.data)
                    }
                })
                .catch((error) => {
                    console.log(error)
                    reject(error)
                })
                .finally(() => {
                    commit('SET_LEAD_SOURCES_LOADER', false)
                })

        }
    },
    getRejectionReasons({commit, state}) {
        if(state.taskType === 'interest' && state.rejectionReasonList.length === 0) {
            commit('SET_REJECTION_REASON_LIST_LOADER', true)
            axios.get('tasks/form_info/rejection_reason/')
                .then((result) => {
                    if(result.status === 200) {
                        commit('SET_REJECTION_REASON_LIST', result.data)
                    }
                })
                .catch((error) => {
                    console.log(error)
                    reject(error)
                })
                .finally(() => {
                    commit('SET_REJECTION_REASON_LIST_LOADER', false)
                })

        }
    },
    changeRejectionReason({ commit, state }, { task, reason }) {
        return new Promise((resolve, reject) => {
            axios.put(`/tasks/task/${task ? task.id : state.task.id}/set_rejection_reason/`, { 
                rejection_reason: reason.id
            })
                .then(({ data}) => {
                    if (data) {
                        const reason_index = state.rejectionReasonList.findIndex(f => f.id === reason.id)
                        let new_reason
                        if(reason_index !== -1) {
                            new_reason = state.rejectionReasonList[reason_index]
                        } else {
                            reject()
                        }
                        const index = state.taskList['interest-interest'].findIndex(f => f.id === task.id)
                        if(index !== -1) {
                            commit('SET_NEW_REJECTION_REASON', {
                                task_index: index,
                                reason: new_reason
                            })
                            resolve()
                        } else {
                            reject()
                        }
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    }
}
