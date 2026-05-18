import Vue from 'vue'


export default {
    SET_ORGANIZATIONS(state, { data, page }) {
        data.page = page
        const isOrganizationsEmpty = !Object.keys(state.organizations).length
        if(isOrganizationsEmpty) {
            Vue.set(state, 'organizations', data)
        } else {
            const existOrganizationList = state.organizations.results
            state.organizations = data
            state.organizations.results.unshift(...existOrganizationList)
        }
    },
    ADD_ORGANIZATION(state, { data }) {
        const isOrganizationsEmpty = !state.organizations || !Object.keys(state.organizations).length
        if(isOrganizationsEmpty) {
            const organizations = {
                results: [data]
            }
            Vue.set(state, 'organizations', organizations)
        } else {
            state.organizations.results.unshift(data)
            if(state.organizations.next) {
                const lastIndex = state.organizations.results.length - 1 
                state.organizations.results.splice(lastIndex, 1)
            }
        }
    },
    DELETE_ORGANIZATION(state, { organizationId }) {
        const foundIndex = state.organizations.results
            .findIndex(organization => organization.id === organizationId)
        if(foundIndex !== -1) {
            state.organizations.results.splice(foundIndex, 1)
        }
        if(state.organizationChildren[organizationId]) {
            delete state.organizationChildren[organizationId]
        }
    },
    UPDATE_ORGANIZATION(state, { updatedOrganization, organizationParentId=null }) {
        if(organizationParentId) {
            const relations = state.organizationChildren?.[organizationParentId]?.results
            if(!Array.isArray(relations)) return

            const foundIndex = relations.findIndex(relation => relation.contractor.id === updatedOrganization.id)
            if(foundIndex !== -1)
                state.organizationChildren[organizationParentId].results[foundIndex].contractor = updatedOrganization
        } else {
            const organizations = state.organizations?.results
            if(!Array.isArray(organizations)) return

            const foundIndex = organizations.findIndex(organization => organization.id === updatedOrganization.id)
            if(foundIndex !== -1)
                Vue.set(state.organizations.results, foundIndex, updatedOrganization)
        }
    },
    ADD_STRUCTURE(state, { data, parentId, relationType }) {
        const isOrganizationsEmpty = !state.organizationChildren[parentId] || 
            !Object.keys(state.organizationChildren[parentId]).length
        if(isOrganizationsEmpty) {
            Vue.set(state.organizationChildren, parentId, { results: [data] })
        } else {
            state.organizationChildren[parentId].results.unshift(data)
        }
    },
    MOVE_ORGANIZATION(state, { data, parentId, organizationId, fosterParentId }) {
        console.log(parentId)
        if(parentId !== fosterParentId) {
            const foundIndex = state.organizations.results
                .findIndex(organization => organization.id === organizationId)
            if(foundIndex !== -1) {
                state.organizations.results.splice(foundIndex, 1)
            }

            if(state.organizationChildren?.[parentId]) {
                const foundIndex = state.organizationChildren[parentId].results
                    .findIndex(organization => organization.id === organizationId)
                if(foundIndex !== -1) {
                    state.organizationChildren[parentId].results.splice[foundIndex, 1]
                }
            }

            if(state.organizationChildren?.[fosterParentId]?.results?.length) {
                state.organizationChildren[fosterParentId].results.push(data)
            }
        }
    },
    CLEAR_ORGANIZATIONS(state) {
        state.organizations = {}
    },
    SET_ORGANIZATION_CHILDREN(state, { data, page, key }) {
        data.page = page

        const isOrganizationsEmpty = !state.organizationChildren[key] || !Object.keys(state.organizationChildren[key]).length
        if(isOrganizationsEmpty) {
            Vue.set(state.organizationChildren, key, data)
        } else {
            const existOrganizationList = state.organizationChildren[key].results
            state.organizationChildren[key] = data
            state.organizationChildren[key].results.unshift(...existOrganizationList)
        }
    },
    UNTIE_ORGANIZATION(state, { parentId, relationId }) {
        const foundRelation = state.organizationChildren[parentId].results
            .findIndex(relation => relation.id === relationId)
        if(foundRelation !== -1) {
            state.organizationChildren[parentId].results.splice(foundRelation, 1)
        }
    },
    // TODO: неудачное именование. Это для установки списка
    SET_DEPARTMENTS_PAGE(state, { data, page, key }) {
        data.page = page
        Vue.set(state.departments, key, data)
    },
    ADD_DEPARTMENT(state, { data, key }) {
        const isDepartmentsEmpty = !state.departments[key] || !Object.keys(state.departments[key]).length

        if(isDepartmentsEmpty) {
            Vue.set(state.departments, key, { results: [data] })
        } else {
            // TODO: Сделать проверку на pageSize
            if(state.departments[key].results.length >= 5) {
                const lastIndex = state.departments[key].results.length - 1
                state.departments[key].results.splice(lastIndex, 1)
            }
            state.departments[key].results.unshift(data)

            // const foundIndex = state.organizations.results.findIndex(organization => organization.id === key)
            // if(foundIndex !== -1) {
            //     state.organizations.results[foundIndex].department_count += 1
            // }
            // if(state.organizationChildren?.[key]) {
            //     state.organizationChildren[key].department_count += 1
            // } 
            // state.departments[key].count += 1

        }
    },
    // TODO: неудачное именование. Это для изменения страницы
    SET_DEPARTMENT_PAGE(state, { page, parentId }) {
        state.departments[parentId].page = page
    },
    // TODO: неудачное именование. Это для изменения страницы
    SET_STRUCTURE_PAGE(state, { page, parentId }) {
        state.organizationChildren[parentId].page = page
    },
    // TODO: неудачное именование. Это для установки списка
    SET_STRUCTURES_PAGE(state, { data, page, key }) {
        data.page = page
        Vue.set(state.organizationChildren, key, data)
    },
    SET_EMPLOYEES_PAGE(state, { data, page, key }) {
        data.page = page
        Vue.set(state.employees, key, data)
    },
    ADD_DEPARTMENT_EMPLOYEE(state, { data, key, parentId, pageSize=15 }) {
        if(data.created) {
            const foundIndex = state.departments?.[parentId].results
                .findIndex(department => department.id === key)
            if(foundIndex !== -1) {
                state.departments[parentId].results[foundIndex].members_count += 1
            }
        }

        const isEmployeesEmpty = !state.employees[key] || !Object.keys(state.employees[key]).length    
        if(isEmployeesEmpty) {
            Vue.set(state.employees, key, { results: [data] })
        } else {
            if(data.created) {
                const currentEmployeePage = state.employees[key].results
                currentEmployeePage.unshift(data)
                state.employees[key].count += 1 
                if(state.employees[key].results.length >= pageSize) {
                    const lastIndex = state.employees[key].results.length - 1 
                    state.employees[key].results.splice(lastIndex, 1)
                }
            }
        }
    },
    ADD_EMPLOYEE(state, { data, key, parentId, pageSize=15 }) {
        if(data.created) {
            if(parentId) {
                const childOrganizations = state.organizationChildren?.[parentId]?.results
                if(Array.isArray(childOrganizations)) {
                    const foundIndex = childOrganizations
                        .findIndex(organization => organization.contractor.id === key)
                    if(foundIndex !== -1) {
                        childOrganizations[foundIndex].contractor.members_count += 1
                    }
                } 
            } else {
                const organizations = state.organizations?.results
                if(Array.isArray(organizations)) {
                    const foundIndex = organizations
                        .findIndex(organization => organization.id === key)
                    if(foundIndex !== -1) {
                        organizations[foundIndex].members_count += 1
                    }
                }
            }
        }

        // TODO: требуется рефакторинг
        const isEmployeesEmpty = !state.employees[key] || !Object.keys(state.employees[key]).length

        if(isEmployeesEmpty) {
            Vue.set(state.employees, key, { results: [data] })
            state.employees[key].count += 1 
        } else {
            // const existEmployeeIndex = state.employees[key].results
            //     .findIndex(employee => employee.id === data.id)
            if(data.created) {
                const currentEmployeePage = state.employees[key].results
                currentEmployeePage.unshift(data)
                state.employees[key].count += 1 
                if(state.employees[key].results.length >= pageSize) {
                    const lastIndex = state.employees[key].results.length - 1 
                    state.employees[key].results.splice(lastIndex, 1)
                }
            }
        }

    },
    DELETE_EMPLOYEE(state, { organizationId, employeeId, parentId=null, isDepartment=false }) {
        const foundEmployeeIndex = state.employees[organizationId].results
            .findIndex(employee => employee.id === employeeId)
        if(foundEmployeeIndex !== -1) {
            state.employees[organizationId].results.splice(foundEmployeeIndex, 1)
        }
        
        if(parentId) {
            if(isDepartment) {
                const foundDepartmentIndex = state.departments[parentId].results
                    .findIndex(department => department.id === organizationId)
                if(foundDepartmentIndex !== -1) {
                    state.departments[parentId].results[foundDepartmentIndex].members_count -= 1
                }
            } else {
                const foundOrganizationIndex = state.organizationChildren[parentId].results
                    .findIndex(relation => relation.contractor.id === organizationId)
                if(foundOrganizationIndex !== -1) {
                    state.organizationChildren[parentId].results[foundOrganizationIndex].contractor.members_count -= 1
                }
            }    
        } else {
            const foundOrganizationIndex = state.organizations.results
                .findIndex(organization => organization.id === organizationId)
            if(foundOrganizationIndex !== -1) {
                state.organizations.results[foundOrganizationIndex].members_count -= 1
            }
        }
    },
    DELETE_DEPARTMENT(state, { departmentId, parentId }) {
        if(state.departments?.[parentId]?.results) {
            const foundIndex = state.departments[parentId].results.findIndex(department => department.id === departmentId)
            state.departments[parentId].results.splice(foundIndex, 1)
        }
    },
    UPDATE_DEPARTMENT_COUNT(state, { parentId, decrement=false }) {
        const delta = decrement ? -1 : 1
        const foundIndex = state.organizations.results
            .findIndex(organization => organization.id === parentId)
        if(foundIndex !== -1) {
            state.organizations.results[foundIndex].department_count += delta
        }
        if(state.organizationChildren?.[parentId]) {
            state.organizationChildren[parentId].department_count += delta
        } 
        state.departments[parentId].count += delta
    },
    UPDATE_STRUCTURE_COUNT(state, { parentId, decrement=false }) {
        const delta = decrement ? -1 : 1
        const foundIndex = state.organizations.results.findIndex(organization => organization.id === parentId)
        if(foundIndex !== -1) {
            state.organizations.results[foundIndex].structural_division_count += delta
        }
        if(state.organizationChildren?.[parentId]) {
            state.organizationChildren[parentId].structural_division_count += delta
        } 
        // state.departments[parentId].count += delta
    },
    UPDATE_DEPARTMENT(state, { data, departmentId, parentId }) {
        if(state.departments?.[parentId]?.results) {
            const foundIndex = state.departments[parentId].results.findIndex(department => department.id === departmentId)
            console.log(foundIndex)
            if(foundIndex !== -1) {
                Vue.set(state.departments[parentId].results, foundIndex, data)
            }
        }
    },
    SET_ACTION_INFO(state, { data }) {
        const isActionInfoEmpty = !Object.keys(state.actionInfo).length
        if(isActionInfoEmpty) {
            Vue.set(state, 'actionInfo', data)
        } else {
            Vue.set(state, 'actionInfo', {
                ...state.actionInfo,
                ...data
            })
        }
    },
    SET_ORGANIZATOIN_ACTION_INFO(state, { data, organizationId }) {
        Vue.set(state.actionInfo, organizationId, data.actions)
    },
    ADD_ROLE(state, { organizationId, role }) {
        if(state.roles?.[organizationId]?.results) {
            state.roles[organizationId].results.unshift(role)
        } else {
            Vue.set(state.roles, organizationId, { results: [role] })
        }
        // mobile
        if(state.infiniteRoles?.[organizationId]?.results) {
            state.infiniteRoles[organizationId].results.unshift(role)
        } else {
            Vue.set(state.infiniteRoles, organizationId, { results: [role] })
        }
    },
    SET_ROLES_PAGE(state, { data, page, key }) {
        data.page = page
        Vue.set(state.roles, key, data)
    },
    SET_INFINITE_ROLES(state, { data, key }) {
        if(state.infiniteRoles?.[key]?.results) {
            state.infiniteRoles[key].results.push(...data.results)
        } else {
            Vue.set(state.infiniteRoles, key, data)
        }
    },
    DELETE_ROLE(state, { roleId, organizationId }) { 
        const roleList = state.roles?.[organizationId]?.results
        if(roleList) {
            const foundIndex = roleList.findIndex(role => role.id === roleId)
            if(foundIndex !== -1) {
                roleList.splice(foundIndex, 1)
            }
        }
        // mobile
        const infiniteRoles = state.infiniteRoles?.[organizationId]?.results
        if(infiniteRoles) {
            const foundIndex = infiniteRoles.findIndex(role => role.id === roleId)
            if(foundIndex !== -1) {
                infiniteRoles.splice(foundIndex, 1)
            }
        }
    },
    CHANGE_ROLE(state, { organizationId, role }) {
        const roleList = state.roles?.[organizationId]?.results
        if(roleList) {
            const foundIndex = roleList.findIndex(roleItem => roleItem.id === role.id)
            if(foundIndex !== -1) {
                Vue.set(state.roles[organizationId].results, foundIndex, role)
            }
        }
        // mobile
        const infiniteRoles = state.infiniteRoles?.[organizationId]?.results
        if(infiniteRoles) {
            const foundIndex = infiniteRoles.findIndex(roleItem => roleItem.id === role.id)
            if(foundIndex !== -1) {
                Vue.set(state.infiniteRoles[organizationId].results, foundIndex, role)
            }
        }

    },
    ADD_ORGANIZATION_TASK(state, { task, organization }) {
    }

}
