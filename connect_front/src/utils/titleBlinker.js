import { i18n } from '@/config/i18n-setup'

let original = typeof document !== 'undefined' ? document.title : ''
let timer = null
let count = 0
let visible = typeof document === 'undefined' ? true : document.visibilityState === 'visible'
let forms = [i18n.t('tab_notify1'), i18n.t('tab_notify2'), i18n.t('tab_notify3')]

const plural = n => {
    const n10 = n % 10
    const n100 = n % 100
    if (n10 === 1 && n100 !== 11) return forms[0]
    if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return forms[1]
    return forms[2]
}

const titleMsg = () => `(${count}) ${plural(count)}`

const tick = () => {
    if (!timer) return
    document.title = document.title === original ? titleMsg() : original
}

const ensure = () => {
    if (timer) return
    timer = setInterval(tick, 1000)
}

const stop = () => {
    if (!timer) return
    clearInterval(timer)
    timer = null
    document.title = original
}

const setVisible = v => {
    visible = v
    if (visible) {
        stop()
        resetCount()
    } else {
        if (count > 0) ensure()
    }
}

const bump = (n = 1, customForms) => {
    if (Array.isArray(customForms) && customForms.length === 3) forms = customForms
    count += n
    if (!visible && count > 0) ensure()
}

const resetCount = () => {
    count = 0
}

const setOriginal = t => {
    original = t || original
}

export default { bump, setVisible, setOriginal, resetCount }
