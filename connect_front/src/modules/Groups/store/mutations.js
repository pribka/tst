import Vue from 'vue'
export default {
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

    SET_TABLE_PAGE_SIZE(state, {tableName, pageSize}) {
        localStorage.setItem(`workgroupTable_${tableName}`, pageSize)
    },
    SET_TABLE_COLUMNS(state, { type, value }) {
        Vue.set(state.tableColumns, type, value)
    },
    SET_FORM_INJECT(state, data) {
        state.formInject = data
    }
}