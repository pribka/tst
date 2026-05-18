const EMPTY_ARRAY_WIDGETS = ['Input', 'DateTime', 'Integer', 'Decimal']

export const buildMeetingRequestParams = ({ filterState, pageName, projectId, page, pageSize, ordering }) => {
    const params = {
        filters: JSON.stringify(buildFilters({ filterState, pageName, projectId }))
    }

    if (page !== undefined)
        params.page = page

    if (pageSize !== undefined)
        params.page_size = pageSize

    const search = filterState?.filtersSearch?.[pageName]
    if (search?.length)
        params.search = search

    const activeOrdering = filterState?.filterOrdering?.[pageName] || ordering
    if (activeOrdering?.length)
        params.ordering = activeOrdering

    return params
}

const buildFilters = ({ filterState, pageName, projectId }) => {
    const filters = {
        project: String(projectId)
    }

    const selected = filterState?.filterSelected?.[pageName] || {}
    const active = filterState?.filterActive?.[pageName] || {}
    const config = filterState?.filter?.[pageName] || { include: [], exclude: [] }
    const filterMap = [...(config.include || []), ...(config.exclude || [])].reduce((acc, item) => {
        acc[item.name] = item
        return acc
    }, {})

    Object.keys(selected).forEach((key) => {
        if (!active[key])
            return

        const value = selected[key]
        const filterConfig = filterMap[key]

        if (value === null || value === undefined)
            return

        if (Array.isArray(value)) {
            if (!value.length) {
                if (filterConfig && EMPTY_ARRAY_WIDGETS.includes(filterConfig.widget?.type))
                    filters[key] = [null]
                return
            }
            filters[key] = value
            return
        }

        if (typeof value === 'object') {
            const hasRangeValue = Object.values(value).some(item => item !== null && item !== undefined && item !== '')
            if (hasRangeValue)
                filters[key] = value
            return
        }

        if (value === '')
            return

        filters[key] = value
    })

    return filters
}
