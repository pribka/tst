import Vue from 'vue'
import ordersRoutes from '@apps/Orders/config/router.js'
import investProjectRoutes from '@apps/InvestProject/config/router.js'
import sportsFacilitiesRoutes from '@apps/SportsFacilities/config/router.js'
import moderationRoutes from '@apps/Moderation/config/router.js'
import helpdeskRoutes from '@apps/HelpDesk/config/router.js'
import directoriesRoutes from '@apps/Directories/config/router.js'
import workPlanRoutes from '@apps/WorkPlan/config/router.js'
import gos24Routes from '@apps/GOS24/config/router.js'
import supportRoutes from '@apps/Support/config/router.js'
import chatRoutes from '@apps/vue2ChatComponent/config/router.js'
// import { Trans } from '@/config/Translation'
//import { v4 as uuidv4, validate as uuidValidate } from 'uuid'
import { checkNewPageWidget } from '@/utils/routerUtils'
import store from '@/store'
import chatSync from '@/utils/chatSync'

const appsRoutes = [
    {
        name: 'moderation',
        redirect: { name: 'moderation-list' },
        children: moderationRoutes
    },
    {
        name: 'helpdesk',
        redirect: { name: 'tickets' },
        children: helpdeskRoutes
    },
    {
        name: 'tickets-and-clients',
        redirect: { name: 'request' },
        children: helpdeskRoutes
    },
    {
        name: 'gos24',
        redirect: { name: 'articles' },
        children: gos24Routes
    },
    {
        name: 'directories',
        redirect: { name: 'directories-team' },
        children: directoriesRoutes
    },
    {
        name: 'pulse',
        redirect: { name: 'workplan-consolidation' },
        children: workPlanRoutes
    }
]

const SALES_SOURCE_ROUTE_NAMES = [
    'interest',
    'interest-kanban',
    'interest_kanban',
    'contractors',
    'goods',
    'orders',
    'deals'
]

const buildSalesRoute = routerList => {
    const routeMap = new Map(routerList.map(route => [route.name, route]))
    const sourceRoutes = SALES_SOURCE_ROUTE_NAMES
        .map(name => routeMap.get(name))
        .filter(Boolean)

    const hasHelpdeskAccess = [
        'helpdesk',
        'tickets-and-clients',
        'tickets',
        'request',
        'unconfirmed_appeals',
        'clients'
    ].some(name => routeMap.has(name))

    if (!sourceRoutes.length && !hasHelpdeskAccess) {
        return routerList
    }

    const salesChildren = [
        {
            name: 'sales-dashboard',
            path: '',
            title: 'Рабочий стол',
            icon: 'fi-rr-chart-histogram',
            isShow: true,
            component: () => import('@/views/Dashboard/PageWidgets/SalesDashboard.vue'),
            meta: {
                title: 'Рабочий стол',
                pageWidget: 'SalesDashboard'
            }
        }
    ]

    if (hasHelpdeskAccess) {
        salesChildren.push({
            name: 'sales-leads',
            path: 'leads',
            title: 'Лиды',
            icon: 'fi-rr-comment-exclamation',
            isShow: true,
            component: () => import('@/views/Dashboard/PageWidgets/SalesLeads.vue'),
            meta: {
                title: 'Лиды',
                pageWidget: 'SalesLeads'
            }
        })
    }

    const addChild = (sourceName, childName, path, title, icon, isShow = true, extraMeta = {}) => {
        const sourceRoute = routeMap.get(sourceName)
        if (!sourceRoute) return
        const child = {
            ...sourceRoute,
            name: childName,
            path,
            title: title || sourceRoute.title,
            icon: icon || sourceRoute.icon,
            ...extraMeta,
            isShow,
            isHidden: !isShow,
            meta: {
                ...(sourceRoute.meta || {}),
                title: title || sourceRoute.meta?.title || sourceRoute.title,
                salesSourceRoute: sourceName,
                ...extraMeta
            }
        }
        delete child.children
        delete child.redirect
        salesChildren.push(child)
    }

    addChild('interest', 'sales-interest', 'interests', 'Интересы', 'fi-rr-memo-circle-check', true, { task_type: 'interest' })

    if (routeMap.has('interest-kanban') || routeMap.has('interest_kanban')) {
        salesChildren.push({
            name: 'sales-funnel',
            path: 'funnel',
            title: 'Воронка',
            icon: 'fi-rr-diagram-project',
            task_type: 'interest',
            isShow: true,
            component: () => import('@/views/Dashboard/PageWidgets/SalesFunnel.vue'),
            meta: {
                title: 'Воронка',
                pageWidget: 'SalesFunnel',
                salesSourceRoute: routeMap.has('interest-kanban') ? 'interest-kanban' : 'interest_kanban',
                task_type: 'interest'
            }
        })
    }

    if (hasHelpdeskAccess) {
        salesChildren.push({
            name: 'sales-clients',
            path: 'clients',
            title: 'Клиенты',
            icon: 'fi-rr-id-card-clip-alt',
            isShow: true,
            component: () => import('@/views/Dashboard/PageWidgets/SalesClients.vue'),
            meta: {
                title: 'Клиенты',
                pageWidget: 'SalesClients'
            }
        })
    }

    addChild('orders', 'sales-orders', 'orders', 'Заказы', 'fi-rr-shopping-bag')
    addChild('goods', 'sales-goods', 'goods', 'Товары и услуги', 'fi-rr-shop', false)

    salesChildren.push({
        name: 'sales-reports',
        path: 'reports',
        title: 'Отчеты',
        icon: 'fi-rr-chart-pie-alt',
        isShow: true,
        component: () => import('@/views/Dashboard/PageWidgets/SalesReports.vue'),
        meta: {
            title: 'Отчеты',
            pageWidget: 'SalesReports'
        }
    })

    const uniqueChildren = []
    const childNames = new Set()
    salesChildren.forEach(child => {
        if (!childNames.has(child.name)) {
            childNames.add(child.name)
            uniqueChildren.push(child)
        }
    })

    const sourceOrder = sourceRoutes
        .map(route => typeof route.descOrder === 'number' ? route.descOrder : null)
        .filter(order => order !== null)
    const salesOrder = sourceOrder.length ? Math.min(...sourceOrder) : 12

    const salesRoute = {
        name: 'sales',
        path: 'sales',
        pageWidget: 'Sales',
        title: 'Продажи',
        icon: 'fi-rr-handshake',
        isFooter: false,
        isShow: true,
        isShowMobile: true,
        mobileOrder: salesOrder,
        descOrder: salesOrder,
        component: checkNewPageWidget({ pageWidget: 'Sales' }),
        redirect: { name: 'sales-dashboard' },
        children: uniqueChildren,
        meta: {
            title: 'Продажи',
            pageWidget: 'Sales'
        }
    }

    return [
        salesRoute,
        ...routerList.filter(route => route.name !== 'sales')
    ]
}

export default {
    SET_ROUTE_ACTIONS(state, { data, name }) {
        Vue.set(state.routeActions, name, data)
    },
    SET_ROUTE_INFO(state, data) {
        Vue.set(state.routeInfo, data.name, data)
    },
    SET_ROUTER_INIT(state, {data, rootState}) {
        const value = data
        state.apiRoute = value
        const allowed = new Set(Object.keys(value || {}))
        const hasTickets = allowed.has('tickets')
        const hasRequest = allowed.has('request')

        const filterByNames = list => {
            if (!Array.isArray(list)) return []
            return list.reduce((acc, r) => {
                const children = r.children ? filterByNames(r.children) : []
                const includeSelf = r.name && allowed.has(r.name)
                if (includeSelf || children.length) {
                    const copy = { ...r }
                    if (children.length) copy.children = children
                    else if (copy.children) delete copy.children
                    acc.push(copy)
                }
                return acc
            }, [])
        }

        const filteredHelpdeskRoutes = filterByNames(helpdeskRoutes)
        const firstHelpdeskChild = filteredHelpdeskRoutes.length ? filteredHelpdeskRoutes[0].name : null

        let routerList = []
        for (const name in value) {
            const route = {
                ...value[name],
                component: checkNewPageWidget(value[name]),
                name,
                path: name,
                meta: {
                    ...value[name]
                }
            }

            if(rootState.isMobile) {
                if(route.name === 'chat') {
                    Vue.set(route, 'badge', true)
                    route.children = chatRoutes
                    route.redirect = { name: 'chat-contact' }
                }
            } else {
                if(route.name === 'chat') {
                    Vue.set(route, 'badge', true)
                    route.children = [
                        {
                            name: 'chat-body',
                            path: '/chat/:id',
                            component: checkNewPageWidget(value[name])
                        }
                    ]
                }
            }

            const supportRoute = supportRoutes.find(item => item.name === route.name)
            if(supportRoute) {
                if(supportRoute.path) {
                    route.path = supportRoute.path
                }
                if(supportRoute.meta) {
                    route.meta = {
                        ...route.meta,
                        ...supportRoute.meta
                    }
                }
            }

            const appRoute = appsRoutes.find(a => a.name === route.name)
            if (appRoute) {
                let children = appRoute.children
                if (route.name === 'helpdesk' || route.name === 'tickets-and-clients') {
                    children = filteredHelpdeskRoutes
                    const redirectName = hasTickets ? 'tickets' : hasRequest ? 'request' : firstHelpdeskChild
                    if (redirectName) route.redirect = { name: redirectName }
                } else {
                    route.redirect = appRoute.redirect
                }
                route.children = children
            }

            routerList.push(route)
        }

        routerList = buildSalesRoute(routerList)

        if (routerList && routerList.length) {
            routerList = routerList
                .concat(ordersRoutes)
                .concat(investProjectRoutes)
                .concat(sportsFacilitiesRoutes)
            routerList = routerList.sort(function (a, b) {
                return a.descOrder - b.descOrder
            })
            const routerListMobile = JSON.parse(JSON.stringify(routerList)).sort(function (a, b) {
                return a.mobileOrder - b.mobileOrder
            })

            const filterChildrenMobile = list => {
                return list
                    .filter(f => !f.hideMobile)
                    .map(item => {
                        const copy = { ...item }
                        if (Array.isArray(copy.children)) {
                            copy.children = filterChildrenMobile(copy.children)
                                .filter(child => !(child.meta && child.meta.hideMobile))
                        }
                        return copy
                    })
            }
            const filteredRouterListMobile = filterChildrenMobile([...routerListMobile].filter(f => !f.isHidden && !f.hideMobile))
            const routerListMixed = rootState.isMobile ? filterChildrenMobile(routerList) : routerList

            state.routerApp = [...routerListMixed].filter(f => !f.type)
            state.routerMobile = filteredRouterListMobile
            state.routerList = [...routerListMixed].filter(f => !f.isHidden)
        }
    },
    CHANGE_ROUTE_MOBILE_FOOTER(state, value) {
        if (value.removed) {
            const route = value.removed.element
            const index = state.routerMobile.findIndex(f => f.name === route.name)
            if (index !== -1)
                Vue.set(state.routerMobile[index], 'isFooter', false)
        }
        if (value.added) {
            const route = value.added.element
            const footerRoutes = state.routerMobile.filter(f => f.isFooter && f.isShowMobile)
            if (footerRoutes.length >= 4) {
                message.warning({ content: 'Максимум 4 модуля' })
            } else {
                const index = state.routerMobile.findIndex(f => f.name === route.name)
                if (index !== -1) {
                    Vue.set(state.routerMobile[index], 'isFooter', true)
                }
            }
        }
    },
    CHANGE_ROUTE_MOBILE_DEACTIVATE(state, value) {
        if (value.removed) {
            const route = value.removed.element
            const index = state.routerMobile.findIndex(f => f.name === route.name)
            if (index !== -1)
                Vue.set(state.routerMobile[index], 'isShowMobile', true)
        }
        if (value.added) {
            const route = value.added.element
            const index = state.routerMobile.findIndex(f => f.name === route.name)
            if (index !== -1) {
                Vue.set(state.routerMobile[index], 'isShowMobile', false)
            }
        }
    },
    CHANGE_ROUTE_SHOW(state, { value, route }) {
        return new Promise((resolve, reject) => {
            const index = state.routerList.findIndex(f => f.name === route.name)
            if (index !== -1)
                Vue.set(state.routerList[index], 'isShow', value)
            resolve(true)
        })
    },
    DELETE_ROUTE_MOBILE(state, route) {
        const index = state.routerMobile.findIndex(f => f.name === route.name)
        if (index !== -1)
            Vue.set(state.routerMobile[index], 'isFooter', false)
    },
    CHANGE_ROUTER_LIST(state, value) {
        state.routerList = value
    },
    CHANGE_MOBILE_ROUTER_LIST(state, value) {
        state.routerMobile = value
    },
    ADD_ROUTE(state, value) {
        state.addRoute.push(value)
    },
    SET_MENU_COUNTER(state, { value, name, __fromSync }) {
        Vue.set(state.counterLink, name, value)

        if (__fromSync) return
        if (name === 'chat') chatSync.menuSet(name, value)
    },
    CHANGE_MENU_COUNT(state, { count, mentions, name }) {
        if (typeof state.counterLink?.[name] !== 'undefined') {
            state.counterLink[name].count = state.counterLink[name].count - count
            state.counterLink[name].mention_count = state.counterLink[name].mention_count - mentions
        }
    },
    INCREMENT_MENU_COUNTER(state, { name, data }) {
        if (typeof state.counterLink?.[name] !== 'undefined') {
            state.counterLink[name].count++
            if(data?.mentions?.length) {
                const find = data.mentions.find(f => f === store.state.user?.user?.id)
                if(find)
                    state.counterLink[name].mention_count++
            }
        } else {
            state.counterLink[name] = {
                count: 1
            }

            if(data?.mentions?.length) {
                const find = data.mentions.find(f => f === store.state.user?.user?.id)
                if(find)
                    state.counterLink[name].mention_count = 1
            }
        }
    },
    CLEAR_MENU_COUNTER(state, payload) {
        const name = typeof payload === 'string' ? payload : payload?.name
        const __fromSync = typeof payload === 'object' ? payload.__fromSync === true : false

        if (typeof state.counterLink?.[name] !== 'undefined') {
            Vue.delete(state.counterLink, name)
        }

        if (__fromSync) return
        if (name === 'chat') chatSync.menuClear(name)
    },
    SET_MENU(state, value) {
        
    },
    PAGE_ROUTE_GENERATE(state, list) {
        
    },
    FORM_ROUTE_GENERATE(state, list) {
        
    },
    TOGGLE_ACTIVE_MENU(state, value) {
        state.activeMenu = value
    },
    PUSH_HEADER_BTN_ROUTER(state, value) {
        state.pushRoutes.push(value)
    }
}
