const state = () => ({
    visible: false,
    shareModel: null,
    messageText: '',
    shareId: null,
    shareObject: null,
    bodySelector: 'body',
    useForwarded: false,
    shareUrl: null,
    shareTitle: null
})

function blurActiveElement() {
    if (typeof document === 'undefined') return

    const activeElement = document.activeElement
    if (activeElement && typeof activeElement.blur === 'function') {
        activeElement.blur()
    }
}

const mutations = {
    SET_VISIBLE(state, value) {
        if (value) {
            blurActiveElement()
        }

        state.visible = value
    },
    SET_SHARE_PARAMS(state, { model = null, shareId = null, object = null, bodySelector, shareUrl = null, shareTitle = null, messageText='', useForwarded = false }) {
        blurActiveElement()
        state.visible = true
        if(model)
            state.shareModel = model
        if(shareId)
            state.shareId = shareId
        if(object)
            state.shareObject = object
        if(shareUrl)
            state.shareUrl = shareUrl
        if(shareTitle)
            state.shareTitle = shareTitle
        state.messageText = messageText
        state.useForwarded = useForwarded

        if(bodySelector)
            state.bodySelector = bodySelector
    },
    CLEAR_PARAMS(state) {
        state.shareModel = null
        state.messageText = ''
        state.shareId = null
        state.shareObject = null
        state.shareUrl = null
        state.shareTitle = null
        state.useForwarded = false
    }
}

export default {
    namespaced: true,
    state,
    mutations
}
