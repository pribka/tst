import { message as antMessage } from 'ant-design-vue'

const bindCloseOnClick = close => {
    if (typeof window === 'undefined' || typeof close !== 'function') return

    window.setTimeout(() => {
        const notices = document.querySelectorAll('.ant-message-notice:not([data-click-close-bound])')
        const notice = notices[0]

        if (!notice) return

        notice.setAttribute('data-click-close-bound', 'true')
        notice.addEventListener('click', () => close(), { once: true })
    }, 0)
}

const wrapMessageMethod = method => (...args) => {
    const close = method(...args)
    bindCloseOnClick(close)
    return close
}

const clickableMessage = Object.assign({}, antMessage, {
    open: wrapMessageMethod(antMessage.open),
    success: wrapMessageMethod(antMessage.success),
    info: wrapMessageMethod(antMessage.info),
    warning: wrapMessageMethod(antMessage.warning),
    warn: wrapMessageMethod(antMessage.warn),
    error: wrapMessageMethod(antMessage.error),
    loading: wrapMessageMethod(antMessage.loading)
})

export default clickableMessage
