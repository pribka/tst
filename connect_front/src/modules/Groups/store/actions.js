import axios from '@/config/axios'
const URL = "work_groups/"

export default {
    //  LIST PAGE
    // Поулчить мои группы
    getUserDrawer({ state, commit, rootState }, { search }) {
        return new Promise((resolve, reject) => {
            const user = rootState.user.user
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
                    let users = data.results
                    commit('SET_USER_NEXT', data.next)

                    if (users?.length) {
                        const index = users.findIndex(f => f.id === user.id)
                        if (index !== -1)
                            users.splice(index, 1)
                    }

                    commit('USER_CONCAT', users)
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getMyGroups({ commit }, { page = 1, is_project = 0, page_name }) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups/`, {
                params: {
                    is_project: is_project,
                    page,
                    page_size: 9,
                    page_name
                }
            })
                .then(({ data }) => {

                    if (is_project === 0) {
                        commit("SET_LIST_GROUPS", data)
                        commit('SET_GROUP_NEXT', data.next)
                    } else {
                        commit("SET_LIST_PROJECTS", data)
                    }
                    resolve(data)
                    // console.log("LiST GROUPS", data.results[0])
                })
                .catch((error) => { reject(error) })
        })
    },

    // getGroupTable({ state, commit }) {
    //     return new Promise((resolve, reject) => {
    //         axios.get('/workgroup/table_info/', { 
    //             params: {
    //                 group_type: 'project'
    //             } 
    //         })
    //             .catch(error => {
    //                 reject(error)
    //             })
    //     })
    // },

    // CREATE 
    // Типы групп
    getGroupTypes({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups_types/`)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Тип соц сетей 
    getSocialTypes({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`social_web_types/`)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Создание группы
    createGroup({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.post(`${URL}workgroups/`, data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    updateGroup({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.put(`${URL}workgroups/${data.id}/`, data.data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addNewChat({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.patch(`${URL}workgroups/${data.id}/add_new_chat/`, data.data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    finishedDate({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.patch(`${URL}workgroups/${data.id}/add_finished_date/`, { finished_date: data.date })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Вступить в группу
    joinGroup({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.post(`${URL}workgroups/${data.id}/join_workgroups/`, { member_visible: data.member_visible })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    // Загрузка соц сети
    postSocialLink({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.post(`social_links/`, data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },


    // MAIN PAGE
    // Информация о группе
    getInfo({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups/${id}/`)
                .then(({ data }) => {
                    resolve(data)
                    commit("SET_INFO", data)
                    // console.log(" GROUPS BY ID", data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Список участников
    getPartisipants({ }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups/${id}/get_workgroups_members/ `)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Роли в группе
    getRoles({ }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups/${id}/my_role/`)
                .then(({ data }) => {
                    resolve(data)
                    // console.log("ROLES", data)
                })
                .catch((error) => { reject(error) })
        })
    },
    //  Пригласить участника 
    postInvite({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.post(`${URL}workgroups/${data.id}/send_invitations/`, { profile_id: data.data })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // добавить изображения в галерею
    postImageGalery({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.put(`${URL}workgroups/${data.id}/upload_gallery_files/`, { files: data.files })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Получить галерею
    getGalery({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}workgroups/${id}/get_gallery_files/`)
                .then(({ data }) => {
                    resolve(data)

                })
                .catch((error) => { reject(error) })
        })
    },
    // Удаление изобажения из галереии
    deleteImageGalery({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.delete(`${URL}workgroups/${data.id}/delete_gallery_files/`, { data: { files: data.files } })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    //  Все новости
    getAllNews({ }, data) {
        return new Promise((resolve, reject) => {
            axios.get(`${URL}news/`, { params: data })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    // Добавить новость
    postNews({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.post(`${URL}news/`, data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    updateNews({ commit }, {newsId, data}) {
        // console.log(newsId, data)
        return new Promise((resolve, reject) => {
            axios.put(`${URL}news/${newsId}/update/`, data )
                .then(({ data }) => {
                    if (data) {
                        // if(state.detailNews)
                        //     commit('SET_DETAIL_NEWS', data)

                        // commit('UPDATE_NEWS_LIST', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    deleteNews({ commit }, {newsId}) {
        console.log(newsId)
        return 0
        return new Promise((resolve, reject) => {
            axios.put(`${URL}news/${newsId}/update/`, data )
                .then(({ data }) => {
                    if (data) {
                        // if(state.detailNews)
                        //     commit('SET_DETAIL_NEWS', data)

                        // commit('UPDATE_NEWS_LIST', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    
    // Удалить участника
    deleteStudent({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.delete(`${URL}workgroups/${data.id}/delete_workgroups_member/`, { data: data.data })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    leaveGroup({ commit }, id) {
        return new Promise((resolve, reject) => {
            axios.delete(`${URL}workgroups/${id}/leave_workgroups/`)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    toModerator({ commit }, data) {
        return new Promise((resolve, reject) => {
            axios.put(`${URL}workgroups/${data.id}/change_member_role/`, data.data)
                .then(({ data }) => {
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },

    // CREATE PAGE


}