import Vue from 'vue'
import VueI18n from 'vue-i18n'
import axios from './axios'
import axiosPush from './axiosPush'
import moment from 'moment'
import store from "@/store"

Vue.use(VueI18n)

function getBrowserLanguage() {
    const language = navigator.language || navigator.userLanguage
    return language.split('-')[0]
}

export const i18n = new VueI18n({
    locale: 'ru',
    fallbackLocale: 'kk',
    messages: { ru: {}, kk: {} }
})

export const langList = ['ru', 'kk']

export const loadedLanguages = []

const getCurrentLang = () => {  
    if(store.state.user.user) {
        return store.state.user.user.language
    }
    // return 'ru' // localStorage.getItem('lang') || 'ru'
    return localStorage.getItem('lang') || 'ru'
}

function setI18nLanguage (lang) {
    i18n.locale = lang
    axios.defaults.headers.common['Accept-Language'] = lang
    axiosPush.defaults.headers.common['Accept-Language'] = lang
    document.querySelector('html').setAttribute('lang', lang)
    localStorage.setItem('lang', lang)
    setMomentLocale(lang)
    return lang
}

async function setMomentLocale(locale) {
    try {
        await import(`moment/locale/${locale}.js`)
        try {
            await import(`@/utils/moment-overrides/${locale}.js`)
        } catch(e) {}
        moment.locale(locale)
    } catch (e) {
        console.error(`Локаль "${locale}" не найдена`, e)
    }
}

export async function asyncInitLang() {
    try {
        const lang = getCurrentLang(),
            bLang = getBrowserLanguage(),
            lInit = localStorage.getItem('langInit') || false

        if(bLang !== lang && !lInit) {
            store.commit('SET_BROWSER_LANG', bLang)
            store.commit('SET_SHOW_LANG_MESSAGE', true)
        }
        // await loadLanguageAsync('ru') // lang || 'ru'
        await loadLanguageAsync(lang || 'ru') 
    } catch(e) {
        console.log(e)
    }
}

export function loadLanguageAsync(lang) {
    if (i18n.locale === lang && lang !== 'ru')
        return Promise.resolve(setI18nLanguage(lang))
    
    return import(/* webpackChunkName: "lang-[request]" */ `@/lang/${lang}.js`).then(
        messages => {
            i18n.setLocaleMessage(lang, messages.default)
            loadedLanguages.push(lang)
            return setI18nLanguage(lang)
        }
    )
}
