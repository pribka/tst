import axios from '@/config/axios'
export default {
    getUserDrawer({ state, commit }, { search }) {
        return new Promise((resolve, reject) => {
            commit('UP_USER_DRAWER_PAGE')

            let url = '/user/list/'
            let params = {
                page: state.userDrawer.page,
                page_size: 20
            }

            if (search?.length) {
                params['fullname'] = search
                url = '/users/search/'
            }

            axios.get(url, { params })
                .then(({ data }) => {
                    commit('SET_USER_NEXT', data.next)
                    commit('USER_CONCAT', data.results)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getUsersMeeting({ commit }, id) {
        return new Promise((resolve, reject) => {


            axios.get('/meetings/members/', { params: { meeting: id, page_size: 999 } })
                .then(({ data }) => {
                    // commit('SET_USERS', data)

                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

}