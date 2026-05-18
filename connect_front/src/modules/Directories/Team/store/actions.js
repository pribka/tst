import axios from '@/config/axios'

export default {
    addOrganization({ commit, state }, { payload, parentId=null, relationType=null }) {
        return new Promise((resolve, reject) => {
            const url = `/users/my_organizations/create/`
            axios.post(url, payload)
                .then(({ data }) => {
                    if(parentId) {
                        commit('ADD_STRUCTURE', {
                            data: {
                                contractor: data,
                                contractor_parent: {
                                    id: parentId
                                },
                                relationType: { 
                                    code: relationType 
                                }
                            },
                            parentId: parentId,
                            relationType: relationType
                        })    
                    } else {
                        commit('ADD_ORGANIZATION', { data })
                    }
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    addStructure({ commit, state }, { payload, parentId }) {
        return new Promise((resolve, reject) => {
            const url = `/users/my_organizations/create/`
            axios.post(url, {
                ...payload,
                get_relation :true
            })
                .then(({ data }) => {
                    commit('ADD_STRUCTURE', {
                        data: data,
                        parentId: parentId,
                        relationType: payload.contractor_parent.relation_type
                    })
                    commit('UPDATE_STRUCTURE_COUNT', { 
                        parentId: parentId
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    addDepartment({ commit, state }, { payload, key, isDepartment=true }) {
        return new Promise((resolve, reject) => {
            const url = isDepartment ? `/users/my_organizations/${key}/departments/create/` :
                ``
            axios.post(url, payload)
                .then(({ data }) => {
                    commit('ADD_DEPARTMENT', { 
                        data: data, 
                        key: key 
                    })
                    commit('UPDATE_DEPARTMENT_COUNT', { 
                        parentId: key 
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },

    getOrganizationsList({ commit, state }, { params, isSearch=false }) {
        return new Promise((resolve, reject) => {
            if(isSearch) {
                delete params.display
            }
            axios.get('/users/my_organizations/', { params })
                .then(({ data }) => {
                    resolve(JSON.parse(JSON.stringify(data)))
                    commit('SET_ORGANIZATIONS', { 
                        data: data, 
                        page: params.page,
                    })
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },

    getActionInfo({ commit, state }, { payload }) {
        return new Promise((resolve, reject) => {
            axios.post('users/my_organizations/action_info/', payload)
                .then(({ data }) => {
                    resolve(data)
                    commit('SET_ACTION_INFO', {
                        data
                    })
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    getOrganizationActionInfo({ commit, state }, { organizationId }) {
        return new Promise(async (resolve, reject) => {
            await axios.get(`/users/my_organizations/${organizationId}/action_info/`)
                .then(({ data }) => {
                    resolve(data)
                    commit('SET_ORGANIZATOIN_ACTION_INFO', {
                        data,
                        organizationId
                    })
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    updateDepartment({ commit, state }, { payload, departmentId, parentId }) {
        const url = `/users/my_organizations/departments/${departmentId}/update/`
        return new Promise((resolve, reject) => {
            axios.patch(url, payload)
                .then(({ data }) => {
                    commit('UPDATE_DEPARTMENT', { 
                        data: data, 
                        departmentId: departmentId,
                        parentId: parentId
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    deleteOrganization({ commit, state }, { organizationId, parentId=null }) {
        const url = `/users/my_organizations/${organizationId}/delete/`
        return new Promise((resolve, reject) => {
            axios.post(url)
                .then(({ data }) => {
                    commit('DELETE_ORGANIZATION', { 
                        organizationId: organizationId,
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    getOrganizationChildrenList({ commit, state }, { params, key }) {
        return new Promise((resolve, reject) => {
            params.filters = { relation_type_id: 'structural_division' }
            axios.get(`/users/my_organizations/${key}/relations/`, { params })
                .then(({ data }) => {
                    resolve(JSON.parse(JSON.stringify(data)))
                    commit('SET_STRUCTURES_PAGE', { 
                        data: data, 
                        page: params.page,
                        key: key 
                    })
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    getDepartmentList({ commit, state }, { params, key }) {
        return new Promise((resolve, reject) => {
            params.filters = { relation_type_id: 'department' }
            
            axios.get(`users/my_organizations/${key}/departments/`, { params })
                .then(({ data }) => {
                    commit('SET_DEPARTMENTS_PAGE', { 
                        data: data, 
                        page: params.page,
                        key: key 
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    addEmployees({ commit, state }, { newEmployeeList, key, parentId, isDepartment=false, pageSize=15 }) {
        // TODO: На бэке нужен прием id-шников списком
        return new Promise((resolve, reject) => {
            const url = isDepartment ? `users/my_organizations/departments/${key}/users/create/` :
                `users/my_organizations/${key}/users/create/`
            newEmployeeList.forEach(employee => {
                const payload = {}
                if(isDepartment) {
                    payload.id = employee.id
                } else {
                    payload.user = employee.id
                }
                axios.post(url, payload)
                    .then(({ data }) => {
                        if(isDepartment) {
                            commit('ADD_DEPARTMENT_EMPLOYEE', { 
                                data: data, 
                                parentId: parentId,
                                key: key,
                                pageSize: pageSize

                            })
                        } else {
                            commit('ADD_EMPLOYEE', { 
                                data: data, 
                                parentId: parentId,
                                key: key,
                                pageSize: pageSize
                            })
                        }
                        resolve(data)
                    })
                    .catch((error) => { 
                        reject(error) 
                    })
            })
        })
    },
    getEmployeeList({ commit, state }, { params, key, isDepartment=false }) {
        return new Promise((resolve, reject) => {
            const url = isDepartment ? `users/my_organizations/departments/${key}/users/` : 
                `/users/my_organizations/${key}/users/`
            axios.get(url, { params })
                .then(({ data }) => {
                    commit('SET_EMPLOYEES_PAGE', { 
                        data: data, 
                        page: params.page,
                        key: key 
                    })
                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    deleteDepartment({ commit, state }, { departmentId, parentId }) {
        return new Promise((resolve, reject) => {
            axios.post(`users/my_organizations/departments/${departmentId}/delete/`)
                .then(({ data }) => {
                    commit('DELETE_DEPARTMENT', { 
                        departmentId: departmentId, 
                        parentId: parentId,
                    })
                    commit('UPDATE_DEPARTMENT_COUNT', { 
                        parentId: parentId,
                        decrement: true 
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    createRole({ commit, state }, { organizationId, payload }) {
        const url = `/contractor_permissions/roles/`
        
        return new Promise((resolve, reject) => {
            axios.post(url, payload)
                .then(({ data }) => {
                    commit('ADD_ROLE', { 
                        organizationId: organizationId,
                        role: data
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    editRole({ commit, state }, { organizationId, roleId, payload }) {
        const url = `contractor_permissions/roles/${roleId}/`

        return new Promise((resolve, reject) => {
            axios.put(url, payload)
                .then(({ data }) => {
                    commit('CHANGE_ROLE', { 
                        organizationId: organizationId,
                        role: data
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    getRoles({ commit, state }, { organizationId, params }) {
        const url = `/contractor_permissions/roles/`
        return new Promise((resolve, reject) => {
            axios.get(url, { params })
                .then(({ data }) => {
                    commit('SET_ROLES_PAGE', { 
                        data: data,
                        key: organizationId,
                        page: 1
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    getInfiniteRoles({ commit, state }, { organizationId, params }) {
        const url = `/contractor_permissions/roles/`
        return new Promise((resolve, reject) => {
            axios.get(url, { params })
                .then(({ data }) => {
                    console.log(params)
                    commit('SET_INFINITE_ROLES', { 
                        data: data,
                        key: organizationId,
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
    deleteRole({ commit, state }, { roleId, organizationId }) {
        const url = `/table_actions/update_is_active/`
        const payload = {
            id: roleId,
            is_active: false
        }
        return new Promise((resolve, reject) => {
            axios.post(url, payload)
                .then(({ data }) => {
                    commit('DELETE_ROLE', { 
                        roleId: roleId,
                        organizationId: organizationId,
                    })

                    resolve(data)
                })
                .catch((error) => { 
                    reject(error) 
                })
        })
    },
}
