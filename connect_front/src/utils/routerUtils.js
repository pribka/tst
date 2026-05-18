import store from '@/store/index.js'

const drawerQueryParams = [
    // 'token',
    'join',
    'deal',
    'meeting',
    'task',
    'contract',
    'event',
    'sprint',
    'viewGroup',
    'comment',
    'viewProject',
    'approvals',
    'newList',
    'newsItem',
    'notif_panel',
    'viewGoods',
    'notif_panel',
    'my_profile',
    'stab',
    'meettab',
    'sptab',
    'tab',
    'in_complete',
    'rtab',
    'chat_id',
    'sprint',
    'createProjectTemplate',
    'ticketView',
    'client',
    'ctab',
    'ttab',
    'create_project',
    'createGroup',
    'ai_chat',
    'my_plan',
    'wtab',
    'help',
    'chapters',
    'pages',
    'sections',
    'menu_page',
    'folder',
    'organization_drawer',
    'organization_id',
    'parent_id',
    'is_department',
    'requestView'
]

export const routeList = [
    'projects-list',
    'projects-gant',
    'projects-sprints',
    // TODO - стоит ли переделать на более
    // конкретные названия роутов, сейчас слишком общие??
    'articles',
    'official',
    'webinar',
    'question',
    'knowledgebase',
    'comment',
    'partition',
    'organ',
    'tag',
    'holidaycalendar',
    'calendar_finance',
    'news_finance',
    'news',
    //
    'reports-dashboards',
    'reports-templates',

    // HelpDesk
    'clients',
    'tickets',
    'spam',
    'unconfirmed_appeals',
    'request',
    'categories',
    'positions',

    // Moderation
    'moderation-list',
    'moderation-new-clients',

    'home',
    'create_order',
    'create_return_order',
    'full_invest_project',
    'full_invest_project_info',
    'full_invest_project_documents',
    'full_invest_project_timeline',
    'full_sports_facilities_pasport',
    'full_sports_facilities_repair',
    'full_sports_facilities_sections',
    'full_sports_facilities_technical',
    'full_sports_facilities_files',
    'full_sports_facilities_gallery',
    'full_sports_facilities_history',
    'full_sports_facilities_characteristics',
    'full_sports_facilities_section_information',
    'full_sports_facilities_object_information',
    'full_sports_facilities',
    'accessDenied',
    'okr-dashboard',
    'okr-strategic-plan',
    'okr-my-objectives                    ',
    'planner',
    'office-preview',
    'chat-window',
    'call-popup'

]

/*
export function checkPageWidget(item) {
    return () => import(`@/views/Dashboard/PageWidgets/${item.meta.pageWidget}.vue`)
        .then(module => {
            return module
        })
        .catch(e => {
            console.log(e, 'error')
            return import(`@/views/Dashboard/PageWidgets/NotPageWidget.vue`)
        })
}*/

export const dummyRoutes = [
    {
        name: 'profile',
        path: 'profile'
    },
    {
        name: 'menu',
        path: 'menu'
    },
    {
        name: 'ru_dummy',
        path: 'ru',
        children: [
            {
                name: 'notifications_dummy',
                path: 'notifications'
            }
        ]
    }
]

export const queryCheck = to => {
    const checkList = [
        'token',
        'mode',
        'join',
        'deal',
        'meeting',
        'task',
        'contract',
        'comment',
        'event',
        'sprint',
        'viewGroup',
        'approvals',
        'viewProject',
        'viewGoods',
        'my_profile',
        'menu_page',
        'stab',
        'notif_panel',
        'newList',
        'newsItem',
        'meettab',
        'sptab',
        'in_complete',
        'rtab',
        'notif_panel',
        'tab',
        'chat_id',
        'sprint',
        'createProjectTemplate',
        'client',
        'ctab',
        'create_project',
        'createGroup',
        'ticketView',
        'client',
        'ai_chat',
        'my_plan',
        'wtab',
        'ttab',
        'ctab',
        'help',
        'chapters',
        'pages',
        'sections',
        'folder',
        'organization_drawer',
        'organization_id',
        'parent_id',
        'is_department',
        'requestView',
        'scope',
        'file_id',
        'comment_id',
        'chat_uid',
        'message_uid']
    const query = {}
    checkList.forEach(item => {
        if(to.query?.[item]) {
            query[item] = to.query[item]
        }
    })
    return query
}

export function findName(array, name) {
    return array.some((object) => object.children ? findName(object.children, name) : object.name === name)
}

export const findFront = routes => {
    if (routes?.filter(f => f.isShow)?.length) {
        return routes.filter(f => f.isShow)[0].name
    } else
        return ''
}

export const initRouteInfo = async ({to, from, init, prototype}) => {
    if(from.name !== to.name
        && to.name !== 'profile'
        && to.name !== 'menu'
        && to.name !== 'chat-contact'
        && to.name !== 'chat-body'
        && to.name !== 'create_order'
        && to.name !== 'full_invest_project_info'
        && to.name !== 'workplan-employees'
        && to.name !== 'pulse'
        && to.name !== 'workplan-consolidation'
        && to.name !== 'planner'
        && to.name !== 'office-preview'
        && to.name !== 'chat-window'
        && to.name !== 'call-popup'
        && to.name !== 'company-wiki'
        && to.name !== 'full_sports_facilities_pasport'
        && to.name !== 'full_invest_project_timeline'
        && to.name !== 'full_invest_project_documents'
        && to.name !== 'full_sports_facilities_sections'
        && to.name !== 'full_sports_facilities_repair'
        && to.name !== 'full_sports_facilities_characteristics'
        && to.name !== 'full_sports_facilities_technical'
        && to.name !== 'full_sports_facilities_files'
        && to.name !== 'full_sports_facilities_history'
        && to.name !== 'full_sports_facilities_gallery'
        && to.name !== 'full_sports_facilities_section_information'
        && to.name !== 'full_sports_facilities_object_information'
        && to.name !== 'create_return_order') {
        try {
            prototype.$Progress.start()
            await store.dispatch('navigation/getRouterInfo', { name: to.name })
        } catch(e) {
            prototype.$Progress.fail()
            console.log(e, 'initRouteInfo')
        } finally {
            prototype.$Progress.finish()
        }
    }
}

export function checkNewPageWidget(route) {
    if(!route.type) {
        return () => import(/* webpackMode: "lazy" */`@/views/Dashboard/PageWidgets/${route.pageWidget}.vue`)
            .then(module => {
                return module
            })
            .catch(e => {
                console.log(e, 'error')
                return import(`@/views/Dashboard/PageWidgets/NotPageWidget.vue`)
            })
    }
    return null
}

export function childrenGenerate(c) {
    return () => import(`${c.children.config}`)
}

const getLastDrawerQueryParam = (route) => {
    let lastIndexOf = 0
    let lastParam = null
    let fallbackIndex = 0
    let fallbackParam = null

    drawerQueryParams.forEach(param => {
        const paramIndex = route.fullPath.indexOf(param)
        if (paramIndex === -1) return

        if (param.includes('tab')) {
            if (paramIndex >= fallbackIndex) {
                fallbackIndex = paramIndex
                fallbackParam = param
            }
        } else {
            if (paramIndex >= lastIndexOf) {
                lastIndexOf = paramIndex
                lastParam = param
            }
        }
    })

    return lastParam || fallbackParam
}

const isQueryChanged = (a, b) => {
    const aKeys = Object.keys(a)
    const bKeys = Object.keys(b)
    if (aKeys.length !== bKeys.length) return true
    return aKeys.some(key => a[key] !== b[key])
}

export const processDrawersQueryParams = ({ to, router, query }) => {
    const queryCopy = { ...query }
    if ('in_complete' in queryCopy) delete queryCopy.in_complete

    const keys = Object.keys(queryCopy)
    if (!keys.length) return

    const groupedQueryParams = [
        ['task', 'comment'],
        ['help', 'sections', 'chapters', 'pages', 'my_profile', 'menu_page'],
        ['organization_drawer', 'organization_id', 'parent_id', 'is_department']
    ]
    const matchedGroup = groupedQueryParams.find(group => keys.filter(k => group.includes(k)).length > 1)
    const presentGroupKeys = matchedGroup ? keys.filter(k => matchedGroup.includes(k)) : []
    const keepGroupTogether = presentGroupKeys.length > 1

    const getLastNonTabParamName = (fullPath) => {
        if (!fullPath || !fullPath.includes('?')) return null
        const qs = fullPath.split('?')[1].split('#')[0]
        if (!qs) return null
        const parts = qs.split('&').filter(Boolean)

        for (let i = parts.length - 1; i >= 0; i--) {
            const pair = parts[i]
            const idx = pair.indexOf('=')
            const rawKey = idx === -1 ? pair : pair.slice(0, idx)
            const key = decodeURIComponent(rawKey)

            if (!key.includes('tab') && key !== 'in_complete') {
                return key
            }
        }

        return null
    }

    const lastNonTabName = getLastNonTabParamName(to.fullPath)

    if (!lastNonTabName) {
        const hasTabOnly = keys.some(k => k.includes('tab'))
        if (!hasTabOnly) return

        const newQuery = {}

        if (keepGroupTogether) {
            presentGroupKeys.forEach(k => {
                newQuery[k] = queryCopy[k]
            })
        }

        if (isQueryChanged(to.query, newQuery)) {
            router.replace({ ...to, query: newQuery })
        }

        return
    }

    const newQuery = {}

    if (keepGroupTogether) {
        presentGroupKeys.forEach(k => {
            newQuery[k] = queryCopy[k]
        })
    } else if (lastNonTabName in queryCopy) {
        newQuery[lastNonTabName] = queryCopy[lastNonTabName]
    }

    keys.forEach(k => {
        if (k.includes('tab')) {
            newQuery[k] = queryCopy[k]
        }
    })

    if (Object.keys(newQuery).length && isQueryChanged(to.query, newQuery)) {
        router.replace({ ...to, query: newQuery })
    }
}

export const clearTabQuery = (query, options = {}) => {
    const removeKeys = Array.isArray(options.removeKeys) ? options.removeKeys : []
    const removeMap = removeKeys.reduce((acc, key) => {
        if (typeof key === 'string' && key) acc[key] = true
        return acc
    }, {})
    const result = {}
    Object.keys(query).forEach(key => {
        const value = query[key]
        const shouldRemoveByValue = value === undefined || value === null || value === ''
        const shouldRemoveByKey = Boolean(removeMap[key])
        if (!shouldRemoveByValue && !shouldRemoveByKey) {
            result[key] = query[key]
        }
    })
    return result
}

export function withLangParam(pathWithQuery, locale) {
    const [pathAndQuery, hash = ''] = pathWithQuery.split('#')
    const base = pathAndQuery.startsWith('/') ? 'http://x' : 'http://x/'
    const u = new URL(pathAndQuery, base)
    u.searchParams.set('lang', locale)
    const rebuilt = u.pathname + (u.search || '') + (hash ? `#${hash}` : '')
    return rebuilt
}

export const isOnlyQueryChange = (to, from) => {
    const sameName = to.name === from.name
    const samePath = to.path === from.path
    const sameHash = to.hash === from.hash
    const sameParams = JSON.stringify(to.params || {}) === JSON.stringify(from.params || {})
    const diffQuery = JSON.stringify(to.query || {}) !== JSON.stringify(from.query || {})
    return sameName && samePath && sameHash && sameParams && diffQuery
}
