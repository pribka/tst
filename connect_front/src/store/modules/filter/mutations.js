import { isEmpty, isArray } from 'lodash'
import Vue from 'vue'
export default {

    clearAllData(state) {
        state.filter = {}
        state.filterStatus = {}
        state.filterData = {}
        state.filterSelected = {}
        state.filterActiv = {}
        state.filterTags = {}
        state.filtersSearch = {}
        state.filterOrdering = {}
        state.filterLoading = {}
    },

    SET_FILTER_LOADING(state, { name, value }) {
        Vue.set(state.filterLoading, name, value)
    },

    UPDATE_FILETR_DATA_DRAWER(state, { name, filterName, data }) {
        state.filterData[name][filterName] = state.filterData[name][filterName].concat(data.results)
        // Vue.set(state.filterData[name], filterName, data.results)
    },

    SET_FILTERS_SEARCH(state, { name, value }) {
        if(value?.length)
            Vue.set(state.filtersSearch, name, value)
        else {
            if(state.filtersSearch?.[name]?.length)
                Vue.delete(state.filtersSearch, name)
        }
    },

    SET_FILTERS_ORDERING(state, { name, value }) {
        if(value?.length)
            Vue.set(state.filterOrdering, name, value)
        else {
            if(state.filterOrdering?.[name]?.length)
                Vue.delete(state.filterOrdering, name)
        }
    },

    // Сбросить к исходному состоянию с бэка
    RESET_ACTIVE_FILTER(state, name) {
        let activeFilters = state.dataFilters.activeFilters
        if (!isEmpty(activeFilters)) {

            Object.keys(activeFilters).forEach(el => {
                let selected = null

                if (activeFilters[el].values.value !== undefined)
                    selected = activeFilters[el].values.value
                else
                    selected = activeFilters[el].values


                Vue.set(state.filterSelected[name], el, selected)
                Vue.set(state.filterActive[name], el, activeFilters[el].active)


            })

            state.filterTags[name] = state.dataFilters.filterTags.structure

        }

    },

    // Очитсить фильтры
    CLEAR_ACTIVE_FILTER(state, name) {
        for (let prop in state.filterSelected[name]) {
            if (state.filterSelected[name][prop] !== undefined) {

                let find = state.filter[name]['include'].find(f => f.name === prop)
                if (find === undefined) find = state.filter[name]['exclude'].find(f => f.name === prop)

                if (['Input', 'DateTime', 'Integer', 'Decimal'].includes(find.widget.type))
                    Vue.set(state.filterSelected[name], prop, null)
                else
                    Vue.set(state.filterSelected[name], prop, [])

                Vue.set(state.filterTags[name], prop, [])

            }
        }

        for (let prop in state.filterActive[name]) {
            Vue.set(state.filterActive[name], prop, false)
        }

    },


    // Установка выбранных значений для селектов
    TOGGLE_FILTER_VALUE(state, { name, value, filterName }) {
        const v = String(value)
        const list = state.filterSelected[name][filterName]
        const i = list.findIndex(x => String(x) === v)
        if (i !== -1) list.splice(i, 1)
        else list.push(v)
        const tags = state.filterTags[name][filterName]
        const j = tags.findIndex(f =>
            String(f.id) === v || String(f.value) === v || String(f.pk) === v || String(f.uuid) === v || String(f.code) === v || String(f.key) === v
        )
        if (j !== -1) tags.splice(j, 1)
        else {
            const found = state.filterData[name][filterName].find(f =>
                String(f.id) === v || String(f.value) === v || String(f.pk) === v || String(f.uuid) === v || String(f.code) === v || String(f.key) === v
            )
            if (found) tags.push(found)
        }
    },
    // Добавляем данные для селекта если они поулчаются через choices 
    SET_CHOICES_FROM_FILTERDATA(state, { name, filterName, choices }) {
        state.filterData[name][filterName] = choices
    },

    // Добваить тег в фильтры
    PUSH_FILTER_TAG(state, { name, value, filterName, toField }) {
        const key = toField || 'id'
        const v = String(value)
        const found = state.filterData[name][filterName].find(f =>
            String(f.id) === v || String(f.value) === v || String(f[key]) === v || String(f.pk) === v || String(f.uuid) === v || String(f.code) === v || String(f.key) === v
        )
        if (found) state.filterTags[name][filterName].push(found)
    },
    INCLUDE_FILTER_TAG(state, { name, value, filterName }) {
        const find = state.filterData[name][filterName].find(f => f.id === value.id)
        state.filterTags[name][filterName].push(value)
    },
    SET_FILTER_TAG(state, { name, value, filterName }) {
        Vue.set(state.filterTags[name], filterName, value)
    },


    // Удалить тег
    DELETE_FILTER_TAG(state, { name, filterName }) {
        Vue.delete(state.filterTags[name], filterName)
    },

    CLEAR_FILTER_TAG(state, { name, filterName }) {
        Vue.set(state.filterTags[name], filterName, [])
    },

    SPLICE_FILTER_TAG(state, { name, value, filterName, toField }) {
        const key = toField || 'id'
        const v = String(value)
        const i = state.filterTags[name][filterName].findIndex(f =>
            String(f.id) === v || String(f.value) === v || String(f[key]) === v || String(f.pk) === v || String(f.uuid) === v || String(f.code) === v || String(f.key) === v
        )
        if (i !== -1) state.filterTags[name][filterName].splice(i, 1)
    },



    // Установить выбранные значение
    SET_SELECTED_FILTER(state, { name, filterName, value }) {
        Vue.set(state.filterSelected[name], filterName, value)
    },


    // ГЕНЕРАЦИЯ 

    GENERATE_FILTER_DATA(state, { name }) {
        Vue.set(state.filterData, name, {})
    },

    GENERATE_FILTER_SELECTED(state, { name }) {
        Vue.set(state.filterSelected, name, {})
    },
    
    SET_FILTER_SEARCH_INPUT(state, { name, data }) {
        Vue.set(state.filterShowSearch, name, data?.searchInput ? true : false)
    },

    GENERATE_FILTER_TAGS(state, { name }) {
        Vue.set(state.filterTags, name, {})
    },

    GENERATE_FILTER_ACTIVE(state, { name }) {
        Vue.set(state.filterActive, name, {})
    },

    GENERATE_FILTER_EXCLUDE(state, { name }) {
        Vue.set(state.filterExclude, name, {})
    },

    // 

    FILTER_GENERATE(state, { name, data, excludeFields }) {

        let include = data.include
        let exclude = data.exclude

        if (excludeFields.length > 0) {
            excludeFields.forEach(item => {
                include = include.filter(el => item !== el.name)
                exclude = exclude.filter(el => item + '__exclude' !== el.name)
            })
        }


        let activeFilters = data.activeFilters

        let filterData = [...include, ...exclude]

        state.dataFilters = data
        state.filter[name] = { include: [], exclude: [] }
        state.filter[name]['include'] = include
        state.filter[name]['exclude'] = exclude


        filterData.forEach(item => {
            if ([
                'Input',
                'DateField',
                'DateTimeField',
                'PositiveIntegerField',
                'CharField',
                'DecimalField',
                'BooleanField'
            ].includes(item.type)) {
                Vue.set(state.filterSelected[name], item.name, null)
            }
            else {
                Vue.set(state.filterSelected[name], item.name, [])
            }

            Vue.set(state.filterTags[name], item.name, [])

            if (item.widget.model) {
                if (item.widget.mode === 'tags')
                    Vue.set(state.filterData[name], item.name, [])
                else {
                    Vue.set(state.filterData[name], item.name, '')
                }
            } else {
                if (item.type === 'BooleanField') {
                    Vue.set(state.filterData[name], item.name, null)
                }
                else if (['CharField', 'AutoField'].includes(item.type)) {
                    Vue.set(state.filterData[name], item.name, '')
                }

                else
                    Vue.set(state.filterData[name], item.name, item.widget.choices)
            }
        })



        // Устанвока активных фильтров

        if (!isEmpty(activeFilters)) {

            Object.keys(activeFilters).forEach(el => {
                let selected = null

                let find = filterData.find(item => item.name === el)
                if (find !== undefined) {
                    if (isArray(activeFilters[el].values.value))
                        selected = activeFilters[el].values.value.filter(el => el !== null)
                    else if (activeFilters[el].values.value !== undefined)
                        selected = activeFilters[el].values.value
                    else

                        selected = activeFilters[el].values


                    Vue.set(state.filterSelected[name], el, selected)
                    Vue.set(state.filterActive[name], el, activeFilters[el].active)
                }

            })

            state.filterTags[name] = data.filterTags.structure


        }


    },

    SET_ACTIVE_FILTERS(state, { name, filterName, value }) {
        Vue.set(state.filterActive[name], filterName, value)

    },


    // Добавить данные для селекта

    CONCAT_FILTER_DATA(state, { name, filterName, data }) {
        if (!state.filterData[name][filterName])
            Vue.set(state.filterData[name], filterName, [])

        state.filterData[name][filterName] = state.filterData[name][filterName].concat(data.results)
    },
    ADD_FILTER_DATA(state, { value, name, filterName }) {
        if (!state.filterData[name][filterName])
            Vue.set(state.filterData[name], filterName, [])

        state.filterData[name][filterName].push(value)
    },

    // Добавить данные для селекта
    CONCAT_FILTER_DATA_SELECT(state, { name, filterName, data }) {
        if (!state.filterData[name][filterName]) Vue.set(state.filterData[name], filterName, [])
        const list = data.filteredSelectList.map(el => {
            const id = String(
                el.id ?? el.value ?? el.pk ?? el.uuid ?? el.key ?? el.code ?? el[filterName] ?? JSON.stringify(el)
            )
            return {
                ...el,
                id,
                value: id,
                name: el.string_view || el.name || el.title || id,
                string_view: el.string_view || el.name || el.title || id
            }
        })
        state.filterData[name][filterName] = state.filterData[name][filterName].concat(list)
    },

    CLEAR_FILTER_DATA(state, { name, filterName }) {
        state.filterData[name][filterName] = []
    },


    REPLACE_FILTER_DATA(state, { name, filterName }) {

        let array = []
        state.filterSelected[name][filterName].forEach(item => {
            const find = state.filterData[name][filterName].find(find => find.id === item)
            if (find)
                array.push(find)
        })

        state.filterData[name][filterName] = array
    },

    // Записать обнвоить данные для селектов 

    UPDATE_FILETR_DATA(state, { name, filterName, data }) {
        Vue.set(state.filterData[name], filterName, data.results)
    },

    UPDATE_FILETR_DATA_SELECT(state, { name, filterName, data }) {
        const list = data.filteredSelectList.map(el => {
            const id = String(
                el.id ?? el.value ?? el.pk ?? el.uuid ?? el.key ?? el.code ?? el[filterName] ?? JSON.stringify(el)
            )
            return {
                ...el,
                id,
                value: id,
                name: el.string_view || el.name || el.title || id,
                string_view: el.string_view || el.name || el.title || id
            }
        })
        Vue.set(state.filterData[name], filterName, list)
    },

    UPDATE_TREE_FILTER_DATA_SELECT(state, { name, filterName, data }) {
        Vue.set(state.filterData[name], filterName, data.filteredSelectList.map(item => {
            return {
                ...item,
                value: item.id,
                title: item.string_view
            }
        }))
    },
}