
import Vue from 'vue';
import { i18n } from '@/config/i18n-setup';
import { getEmptyTemplate, getEmptyFilterGroup } from './templateFactory';

const getFilterIndexByName = (state, name) => {
    return state.activeTemplate.metadata.filters.findIndex(filter => filter.name === name)
}
const getListByKey = (state, key) => {
    return state.activeTemplate.metadata[key]
}
const getItemIndexByKey = (state, listKey, itemKey) => {
    const list = getListByKey(state, listKey)
    return list.findIndex(item => item.name === itemKey)
}
const getOrderedList = (list) => {
    return list.map((item, index) => ({ ...item, order: index+1 }))
}
const normalizeOrderingList = (orderingList = []) => {
    orderingList
        .filter(i => i && i.orderBy)
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
        .forEach((item, idx) => {
            item.order = idx
        })

    for (let i = orderingList.length - 1; i >= 0; i--) {
        if (!orderingList[i]?.orderBy) orderingList.splice(i, 1)
    }
}

const systemFields = [
    {
        verbose_name: i18n.t('reports_mobule.system_fields'),
        unselectable: true,
        children: [
            { 
                name: "index",
                active: true,
                verbose_name: "№",
                title: '№',
                defaultTitle: '№',
                type: 'DecimalField',
                sortable: false,
                system: true,
            },
            { 
                name: "group_index",
                active: true,
                verbose_name: i18n.t('reports_mobule.number_in_group'),
                title: i18n.t('reports_mobule.number_in_group'),
                defaultTitle: i18n.t('reports_mobule.number_in_group'),
                type: 'DecimalField',
                sortable: false,
                system: true,
            }
        ]
    }
]

export default {
    INIT_AVAILABLE_FIELDS(state, { modelMeta, templateData }) {
        state.activeTemplate.availableFields = modelMeta.fields.map(field => ({ 
            ...field, 
            title: field.verbose_name,
            defaultTitle: field.verbose_name,
            active: true
        }))
        const aggregateFields = templateData.metadata.availableAggregateFields || []
        state.activeTemplate.availableFields.unshift(...[
            ...systemFields,
            {
                verbose_name: i18n.t('reports_mobule.aggregate_fields'),
                name: 'aggregate_fields',
                unselectable: true,
                children: [
                    ...aggregateFields,
                    { 
                        name: "add_aggregate_field",
                        verbose_name: i18n.t('reports_mobule.add_own_field'), 
                    }
                ]
            }
        ])
    },
    CLOSE_REPORT_MODAL(state) {
        state.reportModalVisible = false
        state.activeTemplate = getEmptyTemplate()
        state.originalTemplate = null
    },
    CLOSE_REPORT_MODAL_CHECK(state) {
        state.reportModalVisibleCheck = false
    },
    OPEN_REPORT_MODAL(state, { templateData=null }={}) {
        state.reportModalVisibleCheck = true
        state.reportModalVisible = true
        if (!templateData) { 
            // Для нового шаблона сохраняем пустое состояние
            state.originalTemplate = JSON.parse(JSON.stringify(getEmptyTemplate()))
            return 
        }
        const complexFilterMode = (
            templateData.complexFilterMode ??
            templateData.complexFilter ??
            templateData.metadata?.complexFilter ??
            false
        )
        state.activeTemplate.editable = templateData.editable
        state.activeTemplate.imported = templateData.imported || false
        state.activeTemplate.complexFilterMode = complexFilterMode
        state.activeTemplate.appSectionCode = templateData.appSectionCode || ''
        state.activeTemplate.metadata = templateData.metadata
        state.activeTemplate.id = templateData.id || null
        state.activeTemplate.name = templateData.name || ''
        state.activeTemplate.description = templateData.description || ''
        state.activeTemplate.is_base = templateData.is_base || false
        state.activeTemplate.base_report = templateData.base_report || null
        state.activeTemplate.template = templateData.template || null

        const ordering = state.activeTemplate.metadata?.ordering
        if (Array.isArray(ordering) && ordering.length) {
            ordering
                .filter(i => i && i.orderBy)
                .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                .forEach((item, idx) => {
                    if (item.order === undefined || item.order === null) item.order = idx
                })
        }
        // Сохраняем исходное состояние для сравнения
        state.originalTemplate = JSON.parse(JSON.stringify(state.activeTemplate))
    },
    SET_COLUMN_CUSTOM_TITLE(state, { itemName, itemIndex, customTitle }) {
        const index = Number.isInteger(itemIndex) ? itemIndex : getItemIndexByKey(state, 'columns', itemName)
        if (index !== -1) {
            state.activeTemplate.metadata.columns[index].title = customTitle
        } else {
            // TODO Написать ошибку 
            // console.error('Удаляемого фильтра нет в списке')
        }
    },
    SET_COLUMN_FIELD(state, { itemName, itemIndex, fieldName, value }) {
        const index = Number.isInteger(itemIndex) ? itemIndex : getItemIndexByKey(state, 'columns', itemName)
        if (index !== -1) {
            Vue.set(state.activeTemplate.metadata.columns[index], fieldName, value)
            // state.activeTemplate.metadata.columns[index][fieldName] = value
        } else {
            console.error(i18n.t('reports_mobule.column_not_found'))
        }
    },

    SET_FILTER_FIELD(state, { filter, fieldName, value }) {
        const index = getFilterIndexByName(state, filter.name)
        if (index !== -1) {
            state.activeTemplate.metadata.filters[index][fieldName] = value
        } else {
            console.error(i18n.t('reports_mobule.filter_not_found'))
        }
    },
    SET_LIST(state, { key, list }) {
        state.activeTemplate.metadata[key].splice(0)
        state.activeTemplate.metadata[key].push(...list)
    },
    REORDER_COLUMN_LIST(state) {
        const newList = getOrderedList(state.activeTemplate.metadata.columns)
        state.activeTemplate.metadata.columns.splice(0)
        state.activeTemplate.metadata.columns.push(...newList)
    },
    ADD_ITEM(state, { listKey, item }) {
        state.activeTemplate.metadata[listKey].push(item)
    },

    REMOVE_LIST_ITEM(state, { listKey, item, itemIndex }) {
        const itemKey = item.name
        const index = listKey === 'columns' && Number.isInteger(itemIndex)
            ? itemIndex
            : getItemIndexByKey(state, listKey, itemKey)
        if (index !== -1) {
            const list = getListByKey(state, listKey)
            list.splice(index, 1)

            if (listKey === 'columns') {
                const orderingList = state.activeTemplate.metadata.ordering || []
                const removeNames = [item.name]

                if (item.aggregate) {
                    removeNames.push(item.title, item.defaultTitle)
                }

                for (let i = orderingList.length - 1; i >= 0; i--) {
                    if (removeNames.includes(orderingList[i]?.name)) {
                        orderingList.splice(i, 1)
                    }
                }
                normalizeOrderingList(orderingList)
            }
        } else {
            console.error(i18n.t('reports_mobule.filter_not_found'))
        }
    },
    SET_REPORT_CATEGORIES(state, categories) {
        state.reportCategories = categories
    },
    LOAD_TEMPLATES(state, { loadedData, listKey }) {
        const results = state.templates[listKey].results.concat(...loadedData.results)
        state.templates[listKey] = {
            ...loadedData,
            results
        }
    },
    RESET_TEMPLATES(state, { listKey }) {
        state.infiniteId[listKey] = new Date()
        state.templates[listKey] = {
            results: []
        }
    },
    RESET_ALL_TEMPLATES(state) {
        state.infiniteId = {
            'templates': new Date(),
            'my_templates': new Date()
        }
        state.templates = {
            'templates': {
                results: []
            },
            'my_templates': {
                results: []
            },
        }
    },
    SET_ORDERING(state, { fieldName, orderBy, aggregate = false }) {
        const orderingList = state.activeTemplate.metadata.ordering || (state.activeTemplate.metadata.ordering = [])
        const index = orderingList.findIndex(field => field.name === fieldName)

        if (!orderBy) {
            if (index !== -1) orderingList.splice(index, 1)
            normalizeOrderingList(orderingList)
            return
        }

        if (index !== -1) {
            orderingList[index].orderBy = orderBy
            orderingList[index].aggregate = aggregate

            if (orderingList[index].order === undefined || orderingList[index].order === null) {
                const maxOrder = orderingList.reduce((m, x) => Math.max(m, x?.order ?? -1), -1)
                orderingList[index].order = maxOrder + 1
            }

            normalizeOrderingList(orderingList)
            return
        }

        const maxOrder = orderingList.reduce((m, x) => Math.max(m, x?.order ?? -1), -1)
        orderingList.push({ name: fieldName, orderBy, aggregate, order: maxOrder + 1 })
        normalizeOrderingList(orderingList)
    },
    ADD_FILTER_GROUP(state) {
        const newGroup = getEmptyFilterGroup()
        state.activeTemplate.metadata.complexFilters.push(newGroup)
    },
    UPDATE_COMPLEX_FILTER_LIST(state, newList) {
        state.activeTemplate.metadata.complexFilters = newList
    },
    CHANGE_COMPLEX_FILTER_FIELD(state, { path, fieldName, value }) {
        const filters = state.activeTemplate.metadata.complexFilters
        const lastKey = path.pop()
        const items = path.reduce((filterItems, key) => {
            const index = filterItems.findIndex(filterItem => filterItem.id === key)
            return filterItems[index].filters
        }, filters)
        const item = (items.length ? items : filters).find(filterItem => filterItem.id === lastKey)
        item[fieldName] = value
    },
    REMOVE_COMPLEX_FILTER_FIELD(state, { path }) {
        const filters = state.activeTemplate.metadata.complexFilters
        const lastKey = path.pop()
        const items = path.reduce((filterItems, key) => {
            const index = filterItems.findIndex(filterItem => filterItem.id === key)
            return filterItems[index].filters
        }, filters)
        const parentList = (items.length ? items : filters)
        const index = parentList.findIndex(filterItem => filterItem.id === lastKey)
        parentList.splice(index, 1)
    },
    RESET_CHANGES(state) {
        // Сбрасываем отслеживание изменений после сохранения
        if (state.activeTemplate) {
            state.originalTemplate = JSON.parse(JSON.stringify(state.activeTemplate))
        }
    },
    DISCARD_CHANGES(state) {
        // Отменяем изменения, возвращаясь к исходному состоянию
        if (state.originalTemplate) {
            state.activeTemplate = JSON.parse(JSON.stringify(state.originalTemplate))
        }
    },
    CLOSE_CREATE_AGGREGATE_FIELD_MODAL(state) {
        state.createAggregateFieldVisible = false
    },
    OPEN_CREATE_AGGREGATE_FIELD_MODAL(state) {
        state.createAggregateFieldVisible = true
    },
    UPDATE_TEMPLATE_NAME(state, name) {
        state.activeTemplate.name = name
    },
    UPDATE_TEMPLATE_DESCRIPTION(state, description) {
        state.activeTemplate.description = description
    }
}
