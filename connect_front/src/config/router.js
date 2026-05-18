import Vue from 'vue'
import VueRouter from 'vue-router'
import { initRouteInfo, findFront, findName, queryCheck, dummyRoutes, processDrawersQueryParams, routeList, withLangParam, isOnlyQueryChange } from '@/utils/routerUtils.js'
import authorization from '@/views/Authorization/router'
import error from '@/views/Error/router'
import { i18n, loadLanguageAsync, langList } from '@/config/i18n-setup.js'
import axios from '@/config/axios'
import notification from '@apps/UIModules/antDesign/notification'
import Modal from '@apps/UIModules/antDesign/modal'
import { hideAll } from 'tippy.js'
import { restorePageTitle, clearLastTitle } from '@/utils/utils.js'
import { validate as uuidValidate } from 'uuid'

Vue.use(VueRouter)
let firstEntry = true

function joinExternalUrl(base, pathWithQuery) {
    if (!base) return pathWithQuery
    const b = base.endsWith('/') ? base.slice(0, -1) : base
    const p = pathWithQuery.startsWith('/') ? pathWithQuery : `/${pathWithQuery}`
    return `${b}${p}`
}

export default function setupRouter({ store, prototype }) {
    const appRoute = store.state.navigation?.routerApp?.length ? [...store.state.navigation.routerApp] : []
    const isMobile = store.state.isMobile
    const frontPage = findFront(appRoute)

    const mobileChildren = isMobile
        ? [
            ...require('@/views/Profile/router').default,
            ...require('@/views/Menu/router').default
        ]
        : []

    const layoutSwitch = isMobile 
        ? () => import('@/layouts/MobileDashboard')
        : () => import('@/layouts/Dashboard')

    const routes = [
        {
            path: '/access-denied',
            name: 'accessDenied',
            component: () => import(`@/views/Authorization/AccessDenied`)
        },
        {
            path: '/no-access',
            name: 'noaccess',
            component: () => import(`@/views/Authorization/NoAccess`)
        },
        {
            path: '/office-preview',
            name: 'office-preview',
            component: () => import('@/views/OfficePreview/Page')
        },
        {
            path: '/chat-window/:id',
            component: () => import('@/layouts/ChatWindow'),
            children: [
                {
                    path: '',
                    name: 'chat-window',
                    component: () => import('@/views/StandaloneChat/Page'),
                    meta: {
                        title: 'Чат'
                    },
                    beforeEnter: (to, from, next) => {
                        if (uuidValidate(to.params.id)) {
                            return next()
                        }

                        return next({ name: 'chat' })
                    }
                }
            ]
        },
        {
            path: '/call-popup',
            component: () => import('@/layouts/ChatWindow'),
            children: [
                {
                    path: '',
                    name: 'call-popup',
                    component: () => import('@/views/StandaloneCall/Page')
                }
            ]
        },
        {
            name: 'home',
            path: '/',
            component: layoutSwitch,
            redirect: frontPage ? { name: frontPage } : undefined,
            children: [...appRoute, ...mobileChildren, ...dummyRoutes]
        },
        {
            path: '/user',
            component: () => import('@/layouts/Authorization'),
            redirect: { name: 'login' },
            children: authorization
        },
        {
            path: '*',
            component: () => import('@/layouts/PageError'),
            redirect: { name: 'page_404' },
            children: error
        }
    ]

    const router = new VueRouter({
        mode: 'history',
        base: process.env.BASE_URL,
        routes
    })

    const checkTariffExpiration = async ({ to, next }) => {
        const routeMeta = store.state.navigation.routeInfo[to.name]
        if (!routeMeta) {
            await store.dispatch('navigation/routeInit')
            const routes = store.state.navigation.routerApp
            if (!routes.length) {
                if (to.name === 'accessDenied') { return next() }
                return next({ name: 'accessDenied' })
            }
            if (to.name === 'accessDenied') { return next({ name: 'home' }) }
        }
    }

    router.beforeEach(async (to, from, next) => {
        const runtimeAppRoute = store.state.navigation.routerApp || []
        const isDev = store.state.serverType === 'dev'
        const AUTH_URL = process.env.VUE_APP_AUTH_URL
        const user = store.state.user.user
        const locale = i18n.locale
        const resolveRedirectLocale = () => {
            const candidate = localStorage.getItem('redirectLang') || to.query?.lang || user?.language || i18n.locale || 'ru'
            if(localStorage.getItem('redirectLang'))
                localStorage.removeItem('redirectLang')
            return langList.includes(candidate) ? candidate : 'ru'
        }

        if (to.name === 'office-preview' || to.name === 'call-popup') {
            return next()
        }

        const query = queryCheck(to)
        const canAccessDesktopRoute = routeName => {
            if (!routeName) return false
            const topLevel = runtimeAppRoute.find(f => f.name === routeName)
            if (topLevel) return !!topLevel.isShow
            return runtimeAppRoute.some(parent => !!parent.isShow && findName(parent.children || [], routeName))
        }
        const canAccessMobileRoute = routeName => {
            if (!routeName) return false
            const topLevel = runtimeAppRoute.find(f => f.name === routeName)
            if (topLevel) return !!topLevel.isShowMobile
            return runtimeAppRoute.some(parent => !!parent.isShowMobile && findName(parent.children || [], routeName))
        }

        if (to.path.startsWith('/user')) {
            const allowLocalInDev = isDev && to.name === 'login'
            if (!allowLocalInDev) {
                const localizedFullPath = withLangParam(to.fullPath, resolveRedirectLocale())
                const target = joinExternalUrl(AUTH_URL, localizedFullPath)
                window.location.replace(target)
                return
            }
        }

        if (firstEntry && to.query?.lang && frontPage) {
            if(user?.id && user?.language !== to.query.lang) {
                await axios.put('/users/update_profile/', {
                    language: to.query.lang
                })
            }

            if(to.query.lang !== locale)
                await loadLanguageAsync(to.query.lang);
            const { lang, ...restQuery } = to.query;

            return next({
                name: to.name,
                params: to.params,
                query: restQuery,
                hash: to.hash,
                replace: true
            })
        }

        if (user?.id) {
            if(!user.has_access_group) {
                const localizedFullPath = withLangParam(to.fullPath, resolveRedirectLocale())
                const target = joinExternalUrl(AUTH_URL, localizedFullPath)
                window.location.replace(target)
            } else {
                if (to.name === 'noaccess')
                    return next({ name: frontPage, query })
            }

            if (!user.entry_complete) {
                const localizedFullPath = withLangParam(to.fullPath, resolveRedirectLocale())
                const target = joinExternalUrl(AUTH_URL, localizedFullPath)
                window.location.replace(target)
                return
            }

            await initRouteInfo({ to, from, init: firstEntry, prototype })
            await checkTariffExpiration({ to, next })

            const matched = router.match(to.fullPath)
            if (firstEntry && !matched.matched.length) {
                await store.dispatch('navigation/routeInit')
                return next(to.fullPath)
            }

            if (firstEntry) {
                try {
                    processDrawersQueryParams({ to, router, query })

                    if (!findName(authorization, to.name)) {
                        if (to.name) {
                            if (to.name === 'notifications_dummy') {
                                return next({ name: findFront(appRoute), query })
                            } else {
                                if (routeList.includes(to.name)) {
                                    return next({ query })
                                } else {
                                    if (to.name === 'profile' || to.name === 'menu') {
                                        if(isMobile) {
                                            return next({ query })
                                        } else {
                                            if (to.name === 'profile') return next({ name: 'home', query: { ...query, my_profile: 'open' } })
                                            if (to.name === 'menu') return next({ name: 'home', query })
                                        }
                                    } else {
                                        if (to.name === 'page_404') {
                                            return next({ query })
                                        } else {
                                            if(isMobile) {
                                                if(query.chat_id) {
                                                    const findChat = runtimeAppRoute.find(f => (f.name === 'chat' || to.name === 'chat-contact' || to.name === 'chat-body') && f.isShowMobile)
                                                    if(findChat) {
                                                        if(to.name === 'chat-contact' || to.name === 'chat-body') {
                                                            if(to.params?.id === query.chat_id) {
                                                                return next({ query })
                                                            } else {
                                                                return next({ name: 'chat-body', params: { id: query.chat_id } })
                                                            }
                                                        } else {
                                                            return next({ name: 'chat-body', params: { id: query.chat_id } })
                                                        }
                                                    } else {
                                                        if (canAccessMobileRoute(to.name)) {
                                                            return next({ query })
                                                        } else {
                                                            const front = findFront(runtimeAppRoute)
                                                            if (front && front !== to.name) {
                                                                return next({ name: front, query })
                                                            }
                                                            return next()
                                                        }
                                                    }
                                                } else {
                                                    if(to.name === 'chat-contact' || to.name === 'chat-body') {
                                                        return next({ query })
                                                    } else {
                                                        if (canAccessMobileRoute(to.name)) {
                                                            return next({ query })
                                                        } else {
                                                            const front = findFront(runtimeAppRoute)
                                                            if (front && front !== to.name) {
                                                                return next({ name: front, query })
                                                            }
                                                            return next()
                                                        }
                                                    }
                                                }
                                            } else {
                                                if (to.name === 'chat-body') {
                                                    return next({ name: 'chat', query: { chat_id: to.params.id } })
                                                } else {
                                                    if (query.chat_id) {
                                                        const findChat = runtimeAppRoute.find(f => f.name === 'chat' && f.isShow)
                                                        if (findChat) {
                                                            if (to.name === 'chat') {
                                                                return next({ query })
                                                            } else {
                                                                return next({ name: 'chat', query })
                                                            }
                                                        } else {
                                                            if (canAccessDesktopRoute(to.name)) {
                                                                return next({ query })
                                                            } else {
                                                                const front = findFront(runtimeAppRoute)
                                                                if (front && front !== to.name) {
                                                                    return next({ name: front, query })
                                                                }
                                                                return next()
                                                            }
                                                        }
                                                    } else {
                                                        if (canAccessDesktopRoute(to.name)) {
                                                            return next({ query })
                                                        } else {
                                                            const front = findFront(runtimeAppRoute)
                                                            if (front && front !== to.name) {
                                                                return next({ name: front, query })
                                                            }
                                                            return next()
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        } else {
                            return next({ name: 'home', query })
                        }
                    } else {
                        return next({ name: 'home', query })
                    }
                } catch (e) {
                    console.log(e)
                }
            } else {
                if (!findName(authorization, to.name)) {
                    return next()
                } else {
                    location.reload()
                }
            }
        } else {
            if (!findName(authorization, to.name)) {
                return next({ name: 'login', query })
            } else {
                return next({ query })
            }
        }
    })

    router.afterEach((to, from) => {
        if(to.name !== from.name)
            clearLastTitle()
        restorePageTitle()
        hideAll()
        notification.destroy()
        if (!isOnlyQueryChange(to, from))
            Modal.destroyAll()

        if (to.name !== 'Home' && to.name !== 'home' && !findName(authorization, to.name) && to.path !== from.path) {
            let route = Object.assign({}, to)
            if (route.fullPath.includes('?')) {
                route.fullPath = route.fullPath.split('?')[0]
                route.query = {}
            }
        }
        firstEntry = false
    })

    return router
}
