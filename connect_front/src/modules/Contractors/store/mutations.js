import Vue from 'vue'
import store from '@/store'

export default {
    SET_CONSTRACTORS(state, { data, key, page }) {
        data.page = page
        if(state.contractors[key]) {
            const existContractors = state.contractors[key].results
            state.contractors[key] = data
            state.contractors[key].results.unshift(...existContractors)
        } else {
            Vue.set(state.contractors, key, data)
        }
    },
    ADD_CONTRACTOR(state, { newContractor }) {
        if(newContractor) {
            if(state.contractorsTable[state.contractorsType]?.results)
                state.contractorsTable[state.contractorsType].results.unshift(newContractor)
            
            if(state.contractors[state.contractorsType]?.results)
                state.contractors[state.contractorsType].results.unshift(newContractor)
        }
    },
    ADD_ONLY_CONTRACTOR(state, { newContractor }) {
        if(newContractor) {
            if(state.contractorsTable.contractors?.results)
                state.contractorsTable.contractors.results.unshift(newContractor)
            
            if(state.contractors.contractors?.results)
                state.contractors.contractors.results.unshift(newContractor)
        }
    },
    UPDATE_CONTRACTOR(state, { contractor }) {
        if(state.contractorsTable[state.contractorsType]?.results) {
            const indexToReplaceInTable = state.contractorsTable[state.contractorsType].results.findIndex(
                obj => obj.id === contractor.id
            )
            if (indexToReplaceInTable !== -1)
                Vue.set(state.contractorsTable[state.contractorsType].results, indexToReplaceInTable, contractor)
        }
        if(state.contractors[state.contractorsType]?.results) {
            const indexToReplaceCard = state.contractors[state.contractorsType].results.findIndex(
                obj => obj.id === contractor.id
            )
            if (indexToReplaceCard !== -1)
                Vue.set(state.contractors[state.contractorsType].results, indexToReplaceCard, contractor)
        }
    },
    SET_CONSTRACTORS_TABLE(state, { data, key, page }) {
        data.page = page
        Vue.set(state.contractorsTable, key, data)
    },
    CHANGE_ACTIVE_TYPE(state, value) {
        localStorage.setItem('contractorslistType', value)
        state.activeGridType = value
    },
    SET_DEFAULT_GRID_TYPE(state) {
        const storedListType = localStorage.getItem('contractorslistType')
        const isActualType = storedListType && state.gridType.reduce((hasInTypeList, gridTypeItem) => {
            return hasInTypeList || (gridTypeItem.type === storedListType)
        }, false)
        
        if(isActualType)
            state.activeGridType = storedListType
        else if(store.state.config.config?.contractors_setting?.contractors_default_list)
            state.activeGridType = store.state.config.config.contractors_setting.contractors_default_list
        else
            state.activeGridType = 'ContractorsViewTable'
    },
    SET_GRID_TYPE(state, value) {
        state.gridType = value
    },
}