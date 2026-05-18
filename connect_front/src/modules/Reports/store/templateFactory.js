import { v1 as uuidv1 } from 'uuid'

export const getEmptyTemplate = () => ({
    id: null,
    name: '',
    editable: false,
    imported: false,
    description: '',
    availableFields: [],
    complexFilterMode: false,
    appSectionCode: '',
    is_base: false,
    base_report: null,
    template: null,
    metadata: {
        modelName: '',
        columns: [],
        filters: [],
        complexFilters: [],
        grouping: [],
        system_fields: [],
        aggregates: [],
        availableAggregateFields: [],
        ordering: [],
    }
})

export const getEmptyFilterGroup = () => ({
    filters: [],
    logic: 'and',
    id: uuidv1(),
})
