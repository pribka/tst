export const VOICE_MIME_TYPES = [
    { mimeType: 'audio/mp4;codecs=mp4a.40.2', extension: 'm4a' },
    { mimeType: 'audio/mp4', extension: 'm4a' },
    { mimeType: 'audio/webm;codecs=opus', extension: 'webm' },
    { mimeType: 'audio/ogg;codecs=opus', extension: 'ogg' },
    { mimeType: 'audio/webm', extension: 'webm' },
    { mimeType: 'audio/ogg', extension: 'ogg' }
]

export function buildFallbackVoiceBars(count = 28) {
    return Array.from(
        { length: count },
        (_, index) => 10 + Math.round((Math.sin(index / 2.4) + 1) * 10)
    )
}

export function getVoiceMimeConfig() {
    if (typeof window === 'undefined' || typeof window.MediaRecorder === 'undefined') {
        return { mimeType: '', extension: 'm4a' }
    }

    const supported = VOICE_MIME_TYPES.find(item => {
        try {
            return window.MediaRecorder.isTypeSupported(item.mimeType)
        } catch (error) {
            return false
        }
    })

    return supported || { mimeType: '', extension: 'm4a' }
}

export function buildVoiceAudioConstraints() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getSupportedConstraints) {
        return true
    }

    const supportedConstraints = navigator.mediaDevices.getSupportedConstraints()
    const audioConstraints = {}

    if (supportedConstraints.echoCancellation) {
        audioConstraints.echoCancellation = true
    }

    if (supportedConstraints.noiseSuppression) {
        audioConstraints.noiseSuppression = true
    }

    if (supportedConstraints.autoGainControl) {
        audioConstraints.autoGainControl = true
    }

    return Object.keys(audioConstraints).length ? audioConstraints : true
}

export function formatVoiceDuration(seconds) {
    const total = Math.max(0, Math.round(Number(seconds) || 0))
    const minutes = Math.floor(total / 60)
    const remainder = total % 60

    return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

export function buildVoiceUploadFile(blob, extension = 'm4a', mimeType = 'audio/mp4') {
    const fileName = `voice-message-${Date.now()}.${extension}`

    if (typeof File === 'function') {
        return new File([blob], fileName, {
            type: mimeType,
            lastModified: Date.now()
        })
    }

    blob.name = fileName
    blob.lastModified = Date.now()

    return blob
}

export function getVoiceRecordingErrorMessage(error) {
    const errorName = String(error?.name || '')

    if (errorName === 'NotAllowedError' || errorName === 'SecurityError') {
        return 'Safari blocked microphone access. Check site permissions and OS microphone access.'
    }

    if (errorName === 'NotFoundError' || errorName === 'DevicesNotFoundError') {
        return 'No microphone was found on this device'
    }

    if (errorName === 'NotReadableError' || errorName === 'TrackStartError' || errorName === 'AbortError') {
        return 'Microphone is busy or unavailable'
    }

    if (errorName === 'OverconstrainedError' || errorName === 'ConstraintNotSatisfiedError') {
        return 'This browser rejected the requested microphone settings'
    }

    if (errorName === 'NotSupportedError' || errorName === 'TypeError') {
        return 'Voice recording format is not supported in this browser'
    }

    if (errorName === 'InvalidStateError') {
        return 'Voice recorder could not be started in this browser'
    }

    return 'Microphone access is unavailable'
}

export function isVoiceMessageFile(file = {}) {
    if (!file || typeof file !== 'object') {
        return false
    }

    if (file.is_voice === true || file.voice === true) {
        return true
    }

    const rawName = [
        file.name,
        file.original_name,
        file.file_name,
        file.title
    ].find(Boolean)

    const normalizedName = String(rawName || '')
        .trim()
        .toLowerCase()

    if (normalizedName.startsWith('voice-message-')) {
        return true
    }

    const meta = file.meta && typeof file.meta === 'object' ? file.meta : {}
    return meta.is_voice === true || meta.voice === true
}
