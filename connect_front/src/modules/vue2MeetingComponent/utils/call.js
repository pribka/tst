import { message } from 'ant-design-vue'
import { i18n } from '@/config/i18n-setup'
import eventBus from '@/utils/eventBus'

export const CALL_START_EVENT = 'meeting_call:start'
export const CALL_RESTORE_EVENT = 'meeting_call:restore'

export async function ensureMicrophoneAccess() {
    if (typeof window === 'undefined')
        return true

    if (!navigator?.mediaDevices?.getUserMedia) {
        message.error(i18n.t('meeting.microphone_not_supported'))
        return false
    }

    try {
        if (navigator?.permissions?.query) {
            const permissionStatus = await navigator.permissions.query({ name: 'microphone' })

            if (permissionStatus?.state === 'denied') {
                message.error(i18n.t('meeting.microphone_access_required'))
                return false
            }
        }
    } catch (e) {}

    let stream = null

    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        return true
    } catch (error) {
        message.error(i18n.t('meeting.microphone_access_required'))
        return false
    } finally {
        if (stream) {
            stream.getTracks().forEach(track => {
                try {
                    track.stop()
                } catch (e) {}
            })
        }
    }
}

export async function startMeetingCall(options = {}) {
    const hasMicrophoneAccess = await ensureMicrophoneAccess()

    if (!hasMicrophoneAccess) {
        if (typeof options.onMicrophoneDenied === 'function')
            options.onMicrophoneDenied()

        return false
    }

    eventBus.$emit(CALL_START_EVENT, options)
    return true
}

export function restoreMeetingCalls(calls = []) {
    if (typeof window !== 'undefined')
        window.__meetingActiveCallsBootstrap__ = calls

    eventBus.$emit(CALL_RESTORE_EVENT, calls)
}
