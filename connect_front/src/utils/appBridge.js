const stringifyPayload = payload => JSON.stringify(payload)

export const notifyAppLogoutRequest = () => {
    if (typeof window === 'undefined') {
        return false
    }

    const payload = {
        type: 'logout',
        action: 'logout'
    }
    const message = stringifyPayload(payload)
    let delivered = false

    if (window.ReactNativeWebView?.postMessage) {
        window.ReactNativeWebView.postMessage(message)
        delivered = true
    }

    if (window.Flutter?.postMessage) {
        window.Flutter.postMessage(message)
        delivered = true
    }

    if (window.webkit?.messageHandlers?.app?.postMessage) {
        window.webkit.messageHandlers.app.postMessage(payload)
        delivered = true
    }

    if (window.webkit?.messageHandlers?.logout?.postMessage) {
        window.webkit.messageHandlers.logout.postMessage(payload)
        delivered = true
    }

    if (window.flutter_inappwebview?.callHandler) {
        window.flutter_inappwebview.callHandler('app', payload)
        window.flutter_inappwebview.callHandler('logout', payload)
        delivered = true
    }

    return delivered
}
