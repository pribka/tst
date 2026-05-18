import { setAppBadge, clearAppBadge } from '../mixins/appBadge'
import Vue from 'vue'

export default {
    SNOW_TOGGLE(state) {
        const value = !state.showSnow
        localStorage.setItem('show_snow', JSON.stringify(value))
        state.showSnow = value
    },
    ADD_CONNECTED_MODULES(state, value) {
        state.connectedModules.push(value)
    },
    SET_SHOW_LANG_MESSAGE(state, value) {
        state.showLangMessage = value
    },
    SET_BROWSER_LANG(state, value) {
        state.browserLang = value
    },
    SET_IS_APP(state, value) {
        state.isApp = value
    },
    SET_IS_MOBILE(state, value) {
        state.isMobile = value
    },
    ADD_CONNECTED_ROOMS(state, value) {
        state.connectedRooms.push(value)
    },
    SHOW_FOOTER(state, value) {
        state.showFooter = value
        if(value) {
            state.showFooterComp = () => import('@/layouts/components/Mobile/Footer')
        } else {
            state.showFooterComp = null
        }
    },
    SHOW_HEADER(state, value) {
        state.showHeader = value
        if(value) {
            state.showHeaderComp = () => import('@/layouts/components/Mobile/Header')
        } else {
            state.showHeaderComp = null
        }
    },
    DELETE_CONNECTED_ROOMS(state, value) {
        const index = state.connectedRooms.findIndex(f => f === value)
        if(index !== -1) {
            Vue.delete(state.connectedRooms, index)
        }
    },
    TOGGLE_MENU_OPEN(state, {name, show}) {
        const store = localStorage.getItem('local_menu') ? JSON.parse(localStorage.getItem('local_menu')) : {}
        store[name] = show
        if(Object.keys(store)?.length) {
            localStorage.setItem('local_menu', JSON.stringify(store))
            state.menuOpen = store
        }
    },
    TOGGLE_MINI_MENU(state) {
        state.miniMenu = !state.miniMenu 
        localStorage.setItem('miniMenu', state.miniMenu)
        state.sidebarTemplate = state.miniMenu
            ? () => import(`@/layouts/components/Sidebar/MiniAside/index.vue`)
            : () => import(`@/layouts/components/Sidebar/BigAside/index.vue`)
    },
    INIT_SIDEBAR_TEMPLATE(state) {
        state.sidebarTemplate = state.miniMenu
            ? () => import(`@/layouts/components/Sidebar/MiniAside/index.vue`)
            : () => import(`@/layouts/components/Sidebar/BigAside/index.vue`)
    },
    TOGGLE_ASIDE_TYPE(state, value) {
        state.asideType = value
        localStorage.setItem('asideType', JSON.stringify(value))
    },
    SET_CACHE_UID(state, value) {
        state.cacheUID = value
    },
    TOGGLE_ONLINE(state, value) {
        state.online = value
    },
    TOGGLE_DOCUMENT_REVERSE(state, value) {
        localStorage.setItem('documentReverse', JSON.stringify(value))
        state.documentReverse = value
    },
    TOGGLE_EYE_VERSION(state, value) {
        localStorage.setItem('eyeVersionStorage', JSON.stringify(value))
        state.eyeVersion = value
    },
    TOGGLE_WRAPPER_PADDING(state, value) {
        state.wrapperPadding = value
    },
    UPDATE_WINDOW_WIDTH(state, value) {
        state.windowWidth = value
    },
    UPDATE_WINDOW_HEIGHT(state, value) {
        state.windowHeight = value
    },
    ADD_LOGIN_PROGRESS(state, value) {
        state.loginProgress = state.loginProgress + value
    },
    SET_SW_UPDATE(state, value) {
        state.swUpdate = value
    },
    SET_SW_REG(state, value) {
        state.swRegistration = value
    },
    SET_PUSH_AUTH(state, value) {
        state.pushAuth = value
    },
    TOGGLE_VISIBILITY_STATE(state, value) {
        state.visibilityState = value
    },
    INCRIMENT_PWA_COUNTER(state, name) {
        state.pwaCounter[name]++
        setAppBadge(state.pwaCounter)
    },
    DICRIMENT_PWA_COUNTER(state, name) {
        state.pwaCounter[name]--
        setAppBadge(state.pwaCounter)
    },
    SET_PWA_COUNTER(state, { name, value }) {
        state.pwaCounter[name] = +value
        setAppBadge(state.pwaCounter)
    },
    ADD_PWA_COUNTER(state, { name, value }) {
        state.pwaCounter[name] = state.pwaCounter[name] + +value
        setAppBadge(state.pwaCounter)
    },
    REMOVE_PWA_COUNTER(state, { name, value }) {
        state.pwaCounter[name] = state.pwaCounter[name] - +value
        if (state.pwaCounter === 0)
            clearAppBadge()
        else
            setAppBadge(state.pwaCounter)

    },
    CLEAR_PWA_COUNTER(state) {
        state.pwaCounter = 0
        clearAppBadge()
    },
    SET_PWA_POPUP(state, value) {
        state.deferredPrompt = value
    },
    PUSH_OPEN_DRAWERS(state, uid) {
        const index = state.openDrawers.findIndex(f => f.uid === uid)
        if(index !== -1) {
            state.openDrawers.splice(index, 1)
        }
        const zIndex = state.openDrawers?.[state.openDrawers.length - 1]?.zIndex + 200 || 1000
        state.openDrawers.push({ uid, zIndex: zIndex })
    },
    REMOVE_OPEN_DRAWERS(state, uid) {
        const index = state.openDrawers.findIndex(f => f.uid === uid)
        if(index !== -1) {
            state.openDrawers.splice(index, 1)
        }
    },
    OPEN_ONLYOFFICE_PREVIEW(state, query) {
        state.onlyofficePreview = {
            visible: true,
            query: { ...(query || {}) }
        }
    },
    CLOSE_ONLYOFFICE_PREVIEW(state) {
        state.onlyofficePreview = {
            visible: false,
            query: null
        }
    },

}
