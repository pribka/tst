const getProcessedItem = ({ item, additionalFields=[] }) => {
    const processedItem = {
        name: item.name
    }
    additionalFields.forEach(field => {
        if (item[field] !== undefined) {
            processedItem[field] = item[field]
        }
    })
    return processedItem
}

const getSQLCompatibleString = (string) => {
    return string.replace(/[\s"';:,.]/g, (match) => {
        switch (match) {
        case ':': return '__COLON'
        case ';': return '__SEMICOLON'
        case ' ': return '__SPACE'
        case ',': return '__COMMA'
        case '.': return '__DOT'
        }
    })
}

const getAggregateFieldTitleByName = (fieldName, getters) => {
    const field = getters.activeTemplateMetadata.columns
        .filter(column => column.aggregate)
        .find(column => column.name === fieldName)
    return getSQLCompatibleString(field.title)
}

const getComplexFiltersTree = (filters) => {
    return filters
        .filter(item => item.filters 
                || (item.active && ![null, undefined].includes(item.value))
                || item.comparison_type === 'isnull'
                || item.comparison_type === 'not isnull')
        .map(item => {
            if (item.filters) {
                return { logic: item.logic, filters: getComplexFiltersTree(item.filters) }
            }
            return { 
                field: item.aggregate ?  getAggregateFieldTitleByName(item.name, getters) : item.name,
                comparison_type: item.comparison_type,
                value: item.value,
            }
        })
}

export default {
    reportParams: (state, getters) => (htmlType=true) => {
        const fields = {
            groups: getters.columns,
            leveling: getters.grouping,
            aggregates: getters.aggregates,
            system_fields: getters.systemFields
        }
        const filters = state.activeTemplate.complexFilterMode ? getters.complexFilters : getters.filters
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const params = {
            report_name: state.activeTemplate.name || null,
            fields: fields,
            filters: filters,
            ordering: getters.ordering,
            results: 'xls',
            html: htmlType,
            id: state.activeTemplate.id,
            timezone: timezone
        }
        
        if (getters.activeTemplateMetadata.queryset_params) {
            params.queryset_params = getters.activeTemplateMetadata.queryset_params
        }
        return params
    },
    activeTemplateMetadata(state) {
        return state.activeTemplate.metadata
    },
    hasChanges(state) {
        if (!state.originalTemplate) return false
        
        // Сравниваем текущий шаблон с исходным
        const current = JSON.stringify(state.activeTemplate)
        const original = JSON.stringify(state.originalTemplate)
        
        return current !== original
    },
    columns(state, getters) {
        const excludeColumns = ['aggregate', 'system']
        return getters.activeTemplateMetadata.columns
            .filter(column => !excludeColumns.some(excludeColumn => column[excludeColumn]))
            .map(item => getProcessedItem({ item, additionalFields: ['title', 'order', 'is_visible'] }))
    },
    filters(state, getters) {
        const activeFilters = getters.activeTemplateMetadata.filters
            .filter(item => item.active && ![null, undefined].includes(item.value))
        const preprocessedFilters = []
        // TODO
        for (let i = 0; i < activeFilters.length; i++) {
            const item = activeFilters[i]
            if (item.type.includes('DateTimeField') || item.type.includes('DateField')) {
                preprocessedFilters.push({
                    // Особенно здесь. НЕ name a field
                    name: item.name,
                    comparison_type: '>=',
                    value: item.value?.[0] || null,
                })
                preprocessedFilters.push({
                    // Особенно здесь. НЕ name a field
                    name: item.name,
                    comparison_type: '<=',
                    value: item.value?.[1] || null,
                })
            } else {
                preprocessedFilters.push(item)
            }
        }
        return preprocessedFilters
            .map(item => ({
                field: item.aggregate ?  getAggregateFieldTitleByName(item.name, getters) : item.name,
                comparison_type: item.comparison_type,
                value: item.value,
            }))
    },
    complexFilters(state, getters) {
        const complexFilters = {
            filters: getComplexFiltersTree(getters.activeTemplateMetadata.complexFilters),
            logic: 'and',
        }
        return complexFilters
        // const activeFilters = 
        //     .filter(item => (item.filters) || item.active && item.value)
        // return activeFilters
    },
    aggregates(state, getters) {
        return getters.activeTemplateMetadata.columns
            .filter(column => column.aggregate)
            .map(item => ({ ...item, name: getSQLCompatibleString(item.title) }))
            // TODO временно убрал, пока не известны все доступные поля
            // .map(item => getProcessedItem({ item, additionalFields: ['title', 'order'] }))
    },
    grouping(state, getters) {
        return getters.activeTemplateMetadata.grouping
            // TODO А можно ли передавать title для группировки вообще?
            .map(item => getProcessedItem({ item }))
            
    },
    systemFields(state, getters) {
        return getters.activeTemplateMetadata.columns
            .filter(item => item.system)
            .map(item => getProcessedItem({ item, additionalFields: ['title', 'order', 'is_visible'] }))
    },
    ordering(state, getters) {
        return getters.activeTemplateMetadata.ordering
            .filter(item => item.orderBy)
            .slice()
            .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
            .map(item => {
                const fieldName = item.aggregate ? getSQLCompatibleString(item.name) : item.name
                return (item.orderBy === 'DESC' ? '-' : '') + fieldName
            })
    }
}