import axios from '@/config/axios'
import { errorHandler } from '@/utils/index.js'

const FIELD_PATH_SEPARATOR = ' > '
const toModelName = (relatedModel) => (relatedModel || '').toLowerCase()

const createMetaFetcher = (dispatch) => {
    const cache = {}

    return async (modelName) => {
        if (!modelName) {
            return null
        }
        if (!cache[modelName]) {
            cache[modelName] = dispatch('getModelMeta', modelName).then(meta => meta || null)
        }
        return cache[modelName]
    }
}

const resolveLocalizedFieldTitle = async ({ rootModelName, fieldPath, getModelMeta }) => {
    if (!rootModelName || !fieldPath) {
        return null
    }

    const path = fieldPath.split('__')
    const titleParts = []
    let currentModel = rootModelName

    for (let i = 0; i < path.length; i++) {
        const part = path[i]
        const modelMeta = await getModelMeta(currentModel)
        const field = modelMeta?.fields?.find(item => item.name === part)

        if (!field) {
            return null
        }

        titleParts.push(field.verbose_name)

        if (!field.related_model) {
            break
        }

        currentModel = toModelName(field.related_model)
    }

    return titleParts.join(FIELD_PATH_SEPARATOR)
}

const shouldReplaceTitle = (item) => {
    if (!item) {
        return false
    }

    if (!item.title) {
        return true
    }

    const currentDefault = item.defaultTitle || item.verbose_name
    return !currentDefault || item.title === currentDefault
}

const AGGREGATE_KEYS = ['sum', 'avg', 'min', 'max', 'count', 'distinct_count', 'concatenate']

const getAggregateFieldIdentity = (item) => {
    if (!item?.aggregate) {
        return null
    }

    const aggregateKey = AGGREGATE_KEYS.find(key => item[key] !== undefined)

    return {
        aggregateKey,
        aggregateValue: aggregateKey ? item[aggregateKey] : undefined,
        name: item.name,
    }
}

const findAvailableAggregateField = (item, availableAggregateFields = []) => {
    const identity = getAggregateFieldIdentity(item)
    if (!identity) {
        return null
    }

    const exactMatch = availableAggregateFields.find((field) => {
        const fieldIdentity = getAggregateFieldIdentity(field)

        if (!fieldIdentity) {
            return false
        }

        if (identity.aggregateKey && fieldIdentity.aggregateKey) {
            return identity.aggregateKey === fieldIdentity.aggregateKey
                && identity.aggregateValue === fieldIdentity.aggregateValue
                && identity.name === fieldIdentity.name
        }

        return fieldIdentity.name === identity.name
    })

    if (exactMatch) {
        return exactMatch
    }

    return availableAggregateFields.find(field => field?.name === item.name) || null
}

const localizeMetadataLists = async ({ metadata, rootModelName, getModelMeta }) => {
    if (!metadata || !rootModelName) {
        return metadata
    }

    const listKeys = ['columns', 'filters', 'grouping']
    const fieldsToResolve = []
    const availableAggregateFields = metadata.availableAggregateFields || []

    listKeys.forEach((listKey) => {
        const list = metadata[listKey]
        if (!Array.isArray(list)) {
            return
        }

        list.forEach((item) => {
            if (!item || item.aggregate || item.system || !item.name) {
                return
            }
            fieldsToResolve.push(item.name)
        })
    })

    const uniqueFields = [...new Set(fieldsToResolve)]
    const resolvedTitles = {}

    await Promise.all(uniqueFields.map(async (fieldName) => {
        resolvedTitles[fieldName] = await resolveLocalizedFieldTitle({
            rootModelName,
            fieldPath: fieldName,
            getModelMeta,
        })
    }))

    listKeys.forEach((listKey) => {
        const list = metadata[listKey]
        if (!Array.isArray(list)) {
            return
        }

        list.forEach((item) => {
            if (item?.aggregate) {
                const aggregateField = findAvailableAggregateField(item, availableAggregateFields)

                if (!aggregateField) {
                    return
                }

                const localizedTitle = aggregateField.title || aggregateField.defaultTitle || aggregateField.verbose_name
                if (!localizedTitle) {
                    return
                }

                const replaceTitle = shouldReplaceTitle(item)
                item.defaultTitle = localizedTitle
                item.verbose_name = localizedTitle
                if (replaceTitle) {
                    item.title = localizedTitle
                }
                return
            }

            const localizedTitle = resolvedTitles[item?.name]
            if (!localizedTitle) {
                return
            }

            const replaceTitle = shouldReplaceTitle(item)
            item.defaultTitle = localizedTitle
            item.verbose_name = localizedTitle
            if (replaceTitle) {
                item.title = localizedTitle
            }
        })
    })

    return metadata
}

export default {
    getReportCategories({ state, commit }, { force = false } = {}) {
        if (!force && state.reportCategories.length) {
            return Promise.resolve(state.reportCategories)
        }

        const params = {
            model: 'reports.ReportCategoryModel'
        }

        return axios.get('/app_info/select_list/', { params })
            .then(({ data }) => {
                const categories = data?.selectList || []
                commit('SET_REPORT_CATEGORIES', categories)
                return categories
            })
            .catch(error => {
                console.error(error)
                return null
            })
    },
    getModelMeta({}, modelName) {
        const params = { meta: true }
        const url = `reports/${modelName}/`
        return axios.get(url, { params })
            .then(({ data }) => data?.meta)
            .catch(error => {
                console.error(error)
            })
    },
    async openReportModal({ commit, dispatch }, templateData) {
        const modelName = templateData.metadata.modelName
        try {
            const modelMeta = await dispatch('getModelMeta', modelName)

            if (templateData?.metadata) {
                const getModelMeta = createMetaFetcher(dispatch)
                await localizeMetadataLists({
                    metadata: templateData.metadata,
                    rootModelName: modelName,
                    getModelMeta,
                })
            }

            commit('INIT_AVAILABLE_FIELDS', { modelMeta, templateData })
            commit('OPEN_REPORT_MODAL', { templateData })
        } catch (error) {
            console.error(error)
            // this.$message.error('Не удалось инициализировать доступные поля')
        }
    },
    updateTemplate({ commit, state }) {
        const templateId = state.activeTemplate.id
        const listKey = state.activeTemplate.editable ? 'my_templates' : 'templates'
        const url = `/reports/user_report_settings/${templateId}/`
        const payload = {
            name: state.activeTemplate.name,
            description: state.activeTemplate.description,
            app_section_code: state.activeTemplate.appSectionCode || 'tasks',
            template: state.activeTemplate.template || null,
            metadata: {
                ...state.activeTemplate.metadata,
                complexFilter: state.activeTemplate.complexFilterMode || false
            }
        }
        return axios.put(url, payload)
            .then(({ data }) => {
                commit('RESET_TEMPLATES', { listKey })
                commit('UPDATE_TEMPLATE_NAME', data.name)
                commit('UPDATE_TEMPLATE_DESCRIPTION', data.description)
                commit('RESET_CHANGES')
            })
            .catch(error => {
                errorHandler({error})
            })
    }
}
