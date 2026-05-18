import Vue from 'vue'
import App from './App.vue'
import '@/config/registerServiceWorker'
import pkg from '../package'
import setupRouter from '@/config/router'
import store from './store'
import axios from '@/config/axios'
import socket from '@/config/socket'
import { i18n, asyncInitLang, loadLanguageAsync, langList } from '@/config/i18n-setup'
import moment from 'moment'
import { generateDeviceUUID } from '@/utils/utils.js'
import VueGtm from '@gtm-support/vue2-gtm'
import { initSounds } from '@/utils/sounds'
import SoundMaster from '@/utils/soundMaster'
import TitleBlinker from '@/utils/titleBlinker'
import VisibilityHub from '@/utils/visibilityHub'
import chatSync from '@/utils/chatSync'
import { initBrowserPush } from '@/utils/webPush'
import { initWebPushBridge } from '@/utils/webPushBridge'
import { initSocketLifecycle } from '@/utils/socketLifecycle'
//import * as Sentry from '@sentry/vue'
//import { BrowserTracing } from '@sentry/tracing'
import setupVersionWatch from '@/plugins/versionWatch'
import uploadFile from '@/utils/upload'
import '@/assets/css/uicons-regular-rounded.css'
import '@/assets/css/var.less'
import '@/assets/css/main.scss'
import 'tippy.js/dist/tippy.css'
//import 'moment/locale/ru'

/*
moment.locale('ru')
const originalFormat = moment.fn.format
moment.fn.format = function (...args) {
    const currentLocale = i18n?.locale || 'ru'
    if (this.locale() !== currentLocale) {
        this.locale(currentLocale)
    }
    return originalFormat.apply(this, args)
}
const originalFromNow = moment.fn.fromNow
moment.fn.fromNow = function (...args) {
    const currentLocale = i18n?.locale || 'ru'
    if (this.locale() !== currentLocale) {
        this.locale(currentLocale)
    }
    return originalFromNow.apply(this, args)
}*/
/*
const _setLocale = moment.locale.bind(moment)
moment.locale = function(l, ...rest) {
    if (typeof l === 'string' && l && l !== 'ru') {
        try { console.trace('[moment.locale] blocked', l) } catch(e) {}
        return _setLocale('ru')
    }
    return _setLocale(l, ...rest)
}*/

initSounds()
VisibilityHub.start(SoundMaster.tabId())
TitleBlinker.setOriginal(document.title)
initSocketLifecycle(store)

// Vue2TouchEvents
import Vue2TouchEvents from 'vue2-touch-events'
Vue.use(Vue2TouchEvents, {
    disableClick: false,
    touchClass: 'touch',
    tapTolerance: 10,
    touchHoldTolerance: 400,
    swipeTolerance: 30,
    longTapTimeInterval: 400,
    namespace: 'touch'
})

// VueSocketIOExt
import VueSocketIOExt from 'vue-socket.io-extended'
Vue.use(VueSocketIOExt, socket)

if (typeof window !== 'undefined' && !window.__socketPresenceListenersInited) {
    window.__socketPresenceListenersInited = true

    socket.on('online_list', data => {
        if(data?.data?.online_users)
            store.commit('user/SET_ONLINE_USERS', data.data.online_users)
    })
}

// VueCookies
import VueCookies from 'vue-cookies'
Vue.use(VueCookies)

// VueTippy
import VueTippy from "vue-tippy"
Vue.use(VueTippy, {
    directive: 'tippy',
    appendTo: () => document.body,
    trigger: store.state.isMobile ? 'manual' : 'mouseenter',
    duration: [300, 300],
    inertia: true
})

// VueMeta
import VueMeta from 'vue-meta'
Vue.use(VueMeta, { refreshOnceOnNavigation: true })

// lightgallery
import lightgallery from "lightgallery.js"
import "lightgallery.js/dist/css/lightgallery.min.css"
import "lg-zoom.js"
import "lg-thumbnail.js"
import "lg-fullscreen.js"
import "lg-rotate.js"
Vue.use(lightgallery)

// Profiler
import Profiler from '@apps/Profiler'
Vue.use(Profiler)

import VueProgressBar from 'vue-progressbar'
Vue.use(VueProgressBar, {
    color: "#1d65c0",
    failedColor: "#ff4d4e",
    thickness: "2px",
    autoRevert: true,
    location: "top",
    inverse: false
})

// VueAnt
import {
    Slider,
    Empty,
    Popconfirm,
    Descriptions,
    Layout,
    Menu,
    Timeline,
    Result,
    Icon,
    Table,
    Rate,
    Spin,
    Divider,
    Radio,
    Badge,
    Form,
    FormModel,
    Statistic,
    Upload,
    TreeSelect,
    Card,
    Switch,
    Row,
    Col,
    Skeleton,
    ConfigProvider,
    InputNumber,
    Progress,
    Transfer,
    AutoComplete,
    List,
    Tree,
    Breadcrumb
} from 'ant-design-vue'
import Avatar from '@apps/UIModules/antDesign/avatar'
import Button from '@apps/UIModules/antDesign/button'
import Checkbox from '@apps/UIModules/antDesign/checkbox'
import Modal from '@apps/UIModules/antDesign/modal'
import Input from '@apps/UIModules/antDesign/input'
import Select from '@apps/UIModules/antDesign/select'
import Pagination from '@apps/UIModules/antDesign/pagination'
import DatePicker from '@apps/UIModules/antDesign/date-picker'
import Tabs from '@apps/UIModules/antDesign/tabs'
import Tag from '@apps/UIModules/antDesign/tag'
import Dropdown from '@apps/UIModules/antDesign/dropdown'
import Drawer from '@apps/UIModules/antDesign/drawer'
import Calendar from '@apps/UIModules/antDesign/calendar'
import TimePicker from '@apps/UIModules/antDesign/time-picker'
import Collapse from '@apps/UIModules/antDesign/collapse'
import Alert from '@apps/UIModules/antDesign/alert'
import notification from '@apps/UIModules/antDesign/notification'
import ListView from '@apps/UIModules/ListView'
import Tooltip from '@apps/UIModules/antDesign/tooltip'
import Popover from '@apps/UIModules/antDesign/popover'
import message from '@/utils/clickableMessage'

Vue.use(Tooltip)
Vue.use(ListView)
Vue.use(Slider)
Vue.use(Statistic)
Vue.use(Breadcrumb)
Vue.use(Tree)
Vue.use(Row)
Vue.use(Col)
Vue.use(Timeline)
Vue.use(Button)
Vue.use(Layout)
Vue.use(Menu)
Vue.use(Collapse)
Vue.use(Icon)
Vue.use(Table)
Vue.use(Tag)
Vue.use(Divider)
Vue.use(Dropdown)
Vue.use(Avatar)
Vue.use(Badge)
Vue.use(Select)
Vue.use(DatePicker)
Vue.use(Popover)
Vue.use(Input)
Vue.use(Modal)
Vue.use(Form)
Vue.use(FormModel)
Vue.use(Upload)
Vue.use(TreeSelect)
Vue.use(Alert)
Vue.use(Switch)
Vue.use(Card)
Vue.use(Tabs)
Vue.use(Radio)
Vue.use(Spin)
Vue.use(Tooltip)
Vue.use(Rate)
Vue.use(Pagination)
Vue.use(TimePicker)
Vue.use(Checkbox)
Vue.use(InputNumber)
Vue.use(Drawer)
Vue.use(Descriptions)
Vue.use(Popconfirm)
Vue.use(Empty)
Vue.use(Skeleton)
Vue.use(Calendar)
Vue.use(Transfer)
Vue.use(ConfigProvider)
Vue.use(Progress)
Vue.use(AutoComplete)
Vue.use(List)
Vue.use(Result)

Vue.prototype.$moment = moment
Vue.prototype.$message = message
Vue.prototype.$notification = notification
Vue.prototype.$error = Modal.error
Vue.prototype.$confirm = Modal.confirm
Vue.prototype.$success = Modal.success
Vue.config.productionTip = false
Vue.prototype.$http = axios
Vue.prototype.$uploadFile = uploadFile

Object.filter = function (obj, filtercheck) {
    let result = {}
    Object.keys(obj).forEach((key) => { if (filtercheck(obj[key])) result[key] = obj[key] })
    return result
}

const initChatSyncMenu = () => {
    if (typeof window === 'undefined') return
    if (window.__chatSyncMenuInited) return
    window.__chatSyncMenuInited = true

    chatSync.subscribe(payload => {
        try {
            if (!payload) return
            if (payload.from && payload.from === chatSync.tabId) return

            if (payload.type === 'menu_set') {
                store.commit('navigation/SET_MENU_COUNTER', { name: payload.name, value: payload.value, __fromSync: true })
                return
            }

            if (payload.type === 'menu_inc') {
                store.commit('navigation/INCREMENT_MENU_COUNTER', {
                    name: payload.name,
                    data: { __syncDelta: payload.delta, __syncMentionDelta: payload.mentionDelta },
                    __fromSync: true
                })
                return
            }

            if (payload.type === 'menu_clear') {
                store.commit('navigation/CLEAR_MENU_COUNTER', { name: payload.name, __fromSync: true })
            }
        } catch (e) {}
    })
}

const mainAppInit = async () => {
    try {
        const user = await store.dispatch('user/getUserInfo')
        const queryLang = (() => {
            if (typeof window === 'undefined') return null
            const lang = new URLSearchParams(window.location.search).get('lang')
            return langList.includes(lang) ? lang : null
        })()

        if (queryLang) {
            await loadLanguageAsync(queryLang)
            if (user?.status === 200 && store.state.user.user?.id && store.state.user.user?.language !== queryLang) {
                try {
                    await axios.put('/users/update_profile/', { language: queryLang })
                    store.commit('user/SET_USER', { language: queryLang })
                } catch (e) {
                    console.log(e, 'update_profile language sync')
                }
            }
        } else {
            await asyncInitLang()
        }
        generateDeviceUUID()
        if (user?.status === 200) {
            await store.dispatch('getCacheUID')
            const config = await store.dispatch('configInit')
            await store.dispatch('config/fetchBannerNews')
            // await store.dispatch('appInit')
            await store.dispatch('navigation/routeInit')
            await initBrowserPush()
            initChatSyncMenu()

            const primaryColor = config?.theme?.main_color || process.env.VUE_APP_MAIN_COLOR
            store.commit("config/SET_PRIMARY_COLOR", primaryColor)
            /*if(config?.site_setting?.pwa) {
                setupSW()
            }*/

            // await initModules(store)
        } else {
            store.commit("config/SET_PRIMARY_COLOR", process.env.VUE_APP_MAIN_COLOR)
        }

        /*if(store.state.config.config?.site_setting?.ui_key)
            registerLicense(store.state.config.config.site_setting.ui_key)
        else
            console.log('UI key not found')*/

        // Vue.prototype.$i18nRoute = Trans.i18nRoute.bind(Trans)
        const router = setupRouter({ store, axios, VueCookies, prototype: Vue.prototype })
        initWebPushBridge(router)
        if(process.env.NODE_ENV !== 'dev')
            setupVersionWatch(router)

        /*if(process.env.NODE_ENV !== 'dev') {
            Sentry.init({
                Vue,
                dsn: process.env.VUE_APP_SENTRY_DSN || '',
                environment: process.env.VUE_APP_SENTRY_ENV || process.env.NODE_ENV || 'development',
                release: `${process.env.VUE_APP_SENTRY_PROJECT}@${pkg.version}`,
                tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1,
                integrations: [
                    new BrowserTracing({
                        routingInstrumentation: Sentry.vueRouterInstrumentation(router)
                    })
                ]
            })
        }*/

        Vue.use(VueGtm, {
            id: 'GTM-WR54QKMN', // Your GTM single container ID, array of container ids ['GTM-xxxxxx', 'GTM-yyyyyy'] or array of objects [{id: 'GTM-xxxxxx', queryParams: { gtm_auth: 'abc123', gtm_preview: 'env-4', gtm_cookies_win: 'x'}}, {id: 'GTM-yyyyyy', queryParams: {gtm_auth: 'abc234', gtm_preview: 'env-5', gtm_cookies_win: 'x'}}], // Your GTM single container ID or array of container ids ['GTM-xxxxxx', 'GTM-yyyyyy']
            defer: false, // Script can be set to `defer` to speed up page load at the cost of less accurate results (in case visitor leaves before script is loaded, which is unlikely but possible). Defaults to false, so the script is loaded `async` by default
            compatibility: false, // Will add `async` and `defer` to the script tag to not block requests for old browsers that do not support `async`
            enabled: process.env.NODE_ENV === 'production' && process.env.VUE_APP_BUILD_TYPE  === 'production' ? true : false, // defaults to true. Plugin can be disabled by setting this to false for Ex: enabled: !!GDPR_Cookie (optional)
            debug: false, // Whether or not display console logs debugs (optional)
            loadScript: true, // Whether or not to load the GTM Script (Helpful if you are including GTM manually, but need the dataLayer functionality in your components) (optional)
            vueRouter: router, // Pass the router instance to automatically sync with router (optional)
            trackOnNextTick: false, // Whether or not call trackView in Vue.nextTick
        })

        console.log(`%c ${pkg.name} version ${pkg.version} ${process.env.NODE_ENV} init 👍`, 'color: #bada55')

        new Vue({
            i18n,
            router,
            store,
            render: h => h(App)
        }).$mount('#app')
    } catch (e) {
        console.log(e, 'mainAppInit')
    }
}

mainAppInit()

document.addEventListener('visibilitychange', () => {
    TitleBlinker.setVisible(document.visibilityState === 'visible')
})

window.addEventListener('beforeunload', (event) => {
    if (window.__meetingCallUnloadProtected__) {
        event.preventDefault()
        event.returnValue = ''
    }

    const r = window.__swRegistration__
    if (r && r.waiting) r.waiting.postMessage({ type: 'SKIP_WAITING' })
})

VisibilityHub.onChange(anyVis => {
    TitleBlinker.setVisible(anyVis)
})
