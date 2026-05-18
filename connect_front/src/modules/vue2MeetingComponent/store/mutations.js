export default {
    SET_EDIT_DRAWER(state, { show, model }) {
        state.showEdit = {
            show,
            model
        }
    },
    SET_EDIT_MODAL(state, { show, model }) {
        state.showEditModal = {
            show,
            model
        }
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
    SET_USERS(state, values) {
        let res = values
        res.results = res.results.map(el => { return el.user })
        console.log("RES", res)
        state.userDrawer = res

    },

    SET_TABLE_PAGE_SIZE(state, {tableName, pageSize}) {
        localStorage.setItem(`meetingTable_${tableName}`, pageSize)
    },
}