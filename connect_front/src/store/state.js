const documentReverseStorage = JSON.parse(localStorage.getItem('documentReverse'))
const eyeVersionStorage = JSON.parse(localStorage.getItem('eyeVersionStorage'))
const asideTypeStorage = JSON.parse(localStorage.getItem('asideType'))
const userAgent = typeof navigator !== 'undefined' ? (navigator.userAgent || '') : ''
const isSafari = /Safari/i.test(userAgent) && !/Chrome|CriOS|Chromium|Android/i.test(userAgent)

export default () => ({
    windowWidth: null,
    windowHeight: null,
    platform: null,
    wrapperPadding: true,
    showFooter: true,
    showHeader: true,
    showHeaderComp: () => import('@/layouts/components/Mobile/Header'),
    showFooterComp: () => import('@/layouts/components/Mobile/Footer'),
    documentReverse: documentReverseStorage ? documentReverseStorage : false,
    online: true,
    loginProgress: 0,
    cacheUID: localStorage.getItem('cacheUID') ? localStorage.getItem('cacheUID') : null,
    dbList: ['config', 'sort', 'task', 'order', 'groups', 'table', 'bannerNews'],
    storageList: ['user', 'task_create_form_draft'],
    serverType: process.env.NODE_ENV,
    eyeVersion: eyeVersionStorage ? eyeVersionStorage : false,
    swUpdate: false,
    swRegistration: null,
    pushAuth: null,
    visibilityState: true,
    pwaCounter: {},
    deferredPrompt: null,
    isMobile: window.matchMedia('(max-width: 768px)').matches,
    isSafari,
    asideType: asideTypeStorage ? asideTypeStorage : 'mini',
    connectedModules: [],
    connectedRooms: [],
    showLangMessage: false,
    browserLang: null,
    openDrawers: [],
    showSnow: localStorage.getItem('show_snow') ? JSON.parse(localStorage.getItem('show_snow')) : false,
    miniMenu: localStorage.getItem('miniMenu') ? JSON.parse(localStorage.getItem('miniMenu')) : false,
    menuOpen: localStorage.getItem('local_menu') ? JSON.parse(localStorage.getItem('local_menu')) : {},
    sidebarTemplate: null,
    isApp: false,
    onlyofficePreview: {
        visible: false,
        query: null
    }
})
