import Vue from 'vue'

export default {
    SET_REACTIONS(state, value) {
        state.reactions = value
    },
    REGISTER_COMMENT_VISIBILITY(state, payload) {
        const objectKey = String(payload?.relatedObject || '')
        const instanceKey = String(payload?.instanceKey || '')

        if (!objectKey || !instanceKey) return

        const currentEntry = state.visibilityByObject[objectKey] || {
            relatedObject: objectKey,
            instances: {}
        }

        if (!state.visibilityByObject[objectKey]) {
            Vue.set(state.visibilityByObject, objectKey, currentEntry)
        }

        Vue.set(currentEntry.instances, instanceKey, false)
    },
    SET_COMMENT_VISIBILITY(state, payload) {
        const objectKey = String(payload?.relatedObject || '')
        const instanceKey = String(payload?.instanceKey || '')

        if (!objectKey || !instanceKey) return

        const currentEntry = state.visibilityByObject[objectKey] || {
            relatedObject: objectKey,
            instances: {}
        }

        if (!state.visibilityByObject[objectKey]) {
            Vue.set(state.visibilityByObject, objectKey, currentEntry)
        }

        Vue.set(currentEntry.instances, instanceKey, !!payload.visible)
    },
    UNREGISTER_COMMENT_VISIBILITY(state, payload) {
        const objectKey = String(payload?.relatedObject || '')
        const instanceKey = String(payload?.instanceKey || '')

        if (!objectKey || !instanceKey) return

        const currentEntry = state.visibilityByObject[objectKey]
        if (!currentEntry?.instances?.[instanceKey] && currentEntry?.instances?.[instanceKey] !== false) return

        Vue.delete(currentEntry.instances, instanceKey)

        if (!Object.keys(currentEntry.instances).length) {
            Vue.delete(state.visibilityByObject, objectKey)
        }
    }
}
