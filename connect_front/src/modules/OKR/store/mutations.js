import Vue from 'vue'

export default {
    SET_ACTIONS(state, value) {
        state.actions = value
    },
    SET_STATUSES(state, value) {
        state.statuses = value
    },
    SET_DEPARTMENTS(state, value) {
        state.departments = value
    },
    SET_DEPARTMENTS_LOADING(state, value) {
        state.departmentsLoading = value
    },
    SET_STAKEHOLDERS(state, value) {
        state.stakeholders = value
    },
    SET_STAKEHOLDERS_LOADING(state, value) {
        state.stakeholdersLoading = value
    },
    SET_OBJECTIVES(state, value) {
        state.objectives = value
        state.quarter_1 = []
        state.quarter_2 = []
        state.quarter_3 = []
        state.quarter_4 = []
        value.forEach(each => state[`quarter_${each.quarter}`].push(each))
    },
    SET_QUARTER(state, { quarter, value }) {
        state[`quarter_${quarter}`] = value
    },
    SET_OBJECTIVES_LOADING(state, value) {
        state.objectivesLoading = value
    },
    SET_OBJECTIVES_COUNT(state, value) {
        state.objectivesCount = value
    },
    SET_OBJECTIVES_COUNT_LOADING(state, value) {
        state.objectivesCountLoading = value
    },
    SET_MISSION(state, value) {
        state.mission = value
    },
    SET_MISSION_LOADING(state, value) {
        state.missionLoading = value
    },
    SET_LOADING(state, value) {
        state.loading = value
    },
    SET_REMINDERS(state, value) {
        state.reminders = value
    },
    SET_REMINDERS_LOADING(state, value) {
        state.remindersLoading = value
    },
    SET_SELECTED_REMINDER(state, value) {
        state.selectedReminder = value
    },
    SET_OBJECTIVE_DETAIL(state, value) {
        state.objectiveDetail = value
    },
    UPDATE_OBJECTIVE_DETAIL_STATUS(state, newStatus) {
        Vue.set(state.objectiveDetail, 'status', newStatus)
    },
    REMOVE_OBJECTIVE_DETAIL(state) {
        state.objectiveDetail = null
        state.objectiveKeyResults = []
    },
    SET_OBJECTIVE_DETAIL_LOADING(state, value) {
        state.objectiveDetailLoading = value
    },
    SET_COMMENT(state, comment) {
        if (state.objectiveDetail) {
            state.objectiveDetail.comment = comment
        }
    },
    SET_OBJECTIVE_KEY_RESULTS(state, value) {
        state.objectiveKeyResults = value
    },
    UNSHIFT_KEY_RESULT(state, keyResult) {
        state.objectiveKeyResults.unshift(keyResult)
    },
    UPDATE_KEY_RESULT(state, data) {
        const index = state.objectiveKeyResults.findIndex(kr => kr.id === data.id)
        if (index !== -1) {
            Vue.set(state.objectiveKeyResults, index, data)
        }
    },
    REMOVE_REY_RESULT_FROM_LIST(state, krID) {
        state.objectiveKeyResults = state.objectiveKeyResults.filter(kr => kr.id !== krID)
    },
    UPDATE_OBJECTIVE_ON_LIST(state, { objectiveID, data }) {
        const index = state[`quarter_${data.quarter}`].findIndex(item => item.id === objectiveID)
        if (index !== -1) {
            Vue.set(state[`quarter_${data.quarter}`], index, data)
        }
    },
    UPDATE_OBJECTIVE_STATUS(state, { objectiveID, newStatus }) {
        const index = state.objectives.findIndex(item => item.id === objectiveID)
        if (index !== -1) {
            Vue.set(state.objectives[index], 'status', newStatus)
        }
    },
    REMOVE_OBJECTIVE(state, objective) {
        const objectiveID = objective.id
        const quarter = objective.quarter
        const list_index = state.objectives.findIndex(item => item.id === objectiveID)
        const quarter_index = state[`quarter_${quarter}`].findIndex(item => item.id === objectiveID)
        if (list_index !== -1) {
            state.objectives.splice(list_index, 1)
        }
        if (quarter_index !== -1) {
            state[`quarter_${quarter}`].splice(quarter_index, 1)
        }
    },
    SET_VALUE_EFFORTS(state, value) {
        state.valueEfforts = value
    },
    SET_METRICS(state, value) {
        state.metrics = value
    },
    ADD_METRIC(state, metric) {
        state.metrics.unshift(metric)
    },
    SET_ADD_METRIC_LOADING(state, value) {
        state.addMetricLoading = value
    },
    UPDATE_METRIC(state, data) {
        const index = state.metrics.findIndex(item => item.id === data.id)
        if (index !== -1) {
            Vue.set(state.metrics, index, data)
        }
    },
    SET_ADD_OBJECTIVE_MODAL_VISIBLE(state, value) {
        state.addObjectiveModalVisible = value
    },
    SET_ADD_KEY_RESULT_MODAL_VISIBLE(state, value) {
        state.addKeyResultModalVisible = value
    },
    SET_OBJECTIVE_KEY_RESULTS_IN_QUARTER_LIST(state, { objectiveID, quarter, keyResults }) {
        const index = state[`quarter_${quarter}`].findIndex(item => item.id === objectiveID)
        if (index !== -1) {
            Vue.set(state[`quarter_${quarter}`][index], 'key_results', keyResults)
        }
    },
    SET_OBJECTIVE_KEY_RESULTS_IN_LIST(state, { objectiveID, keyResults }) {
        const index = state.objectives.findIndex(item => item.id === objectiveID)
        if (index !== -1) {
            Vue.set(state.objectives[index], 'key_results', keyResults)
        }
    },
    ADD_TASK(state, { keyResult, task }) {
        const index = state.objectiveKeyResults.findIndex(kr => kr.id === keyResult)
        if (index !== -1) {
            const tasks = state.objectiveKeyResults[index].tasks
            tasks.push(task)
            Vue.set(state.objectiveKeyResults[index], 'tasks', tasks)
        }
    },
    REMOVE_TASK(state, { keyResultID, taskID }) {
        const index = state.objectiveKeyResults.findIndex(kr => kr.id === keyResultID)
        if (index !== -1) {
            const tasks = state.objectiveKeyResults[index].tasks.filter(t => t.id !== taskID)
            Vue.set(state.objectiveKeyResults[index], 'tasks', tasks)
        }
    }
}