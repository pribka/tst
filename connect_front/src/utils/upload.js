import axios from 'axios'
import request from '@/config/axios'

export const DEFAULT_UPLOAD_CHUNK_SIZE = 2 * 1024 * 1024
const DEFAULT_CHUNK_RETRIES = 3
const CHUNK_CAPABLE_PATHS = [
    '/common/upload/',
    '/api/v1/common/upload/',
    '/common/upload_for_editor/',
    '/api/v1/common/upload_for_editor/',
]

function isAbsoluteUrl(url = '') {
    return /^https?:\/\//i.test(url)
}

function trimTrailingSlash(value = '') {
    return value.replace(/\/+$/, '')
}

function isLocalUploadUrl(url = '') {
    if (!url)
        return true

    if (!isAbsoluteUrl(url))
        return true

    const apiBaseUrl = trimTrailingSlash(process.env.VUE_APP_API_URL || '')
    if (!apiBaseUrl)
        return false

    return trimTrailingSlash(url).startsWith(apiBaseUrl)
}

function isChunkCapableUrl(url = '') {
    if (!isLocalUploadUrl(url))
        return false

    const normalizedUrl = String(url || '').split('?')[0]

    return CHUNK_CAPABLE_PATHS.some(path => normalizedUrl.endsWith(path) || normalizedUrl.includes(path))
}

function appendFormData(formData, extraData = {}) {
    Object.entries(extraData).forEach(([key, value]) => {
        if (value === undefined || value === null || value === false)
            return

        if (Array.isArray(value)) {
            value.forEach(item => appendFormData(formData, { [key]: item }))
            return
        }

        if (value === true) {
            formData.append(key, 'true')
            return
        }

        formData.append(key, value)
    })
}

function emitProgress(onProgress, loaded, total) {
    if (typeof onProgress !== 'function')
        return

    const safeLoaded = Math.max(0, Number(loaded) || 0)
    const safeTotal = Math.max(0, Number(total) || 0)
    const percent = safeTotal ? Math.min(100, Math.round((safeLoaded / safeTotal) * 100)) : 0

    onProgress({
        loaded: safeLoaded,
        total: safeTotal,
        percent
    })
}

function createUploadId() {
    return `upload-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function postWithRetry(factory, retries = DEFAULT_CHUNK_RETRIES) {
    let lastError = null

    for (let attempt = 1; attempt <= retries; attempt += 1) {
        try {
            return await factory(attempt)
        } catch (error) {
            if (axios.isCancel?.(error) || error?.code === 'ERR_CANCELED')
                throw error

            lastError = error
            if (attempt >= retries)
                throw error

            await new Promise(resolve => setTimeout(resolve, attempt * 250))
        }
    }

    throw lastError
}

async function uploadDirect({
    file,
    url,
    fieldName,
    fileName,
    extraData,
    headers,
    onProgress,
    cancelToken,
    requestInstance,
    withCredentials,
}) {
    const formData = new FormData()
    formData.append(fieldName, file, fileName)
    appendFormData(formData, extraData)

    const { data } = await requestInstance.post(url, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
            ...headers
        },
        withCredentials,
        cancelToken,
        onUploadProgress: ({ loaded, total }) => emitProgress(onProgress, loaded, total || file.size)
    })

    emitProgress(onProgress, file.size, file.size)
    return data
}

async function uploadChunked({
    file,
    url,
    fieldName,
    fileName,
    extraData,
    headers,
    onProgress,
    cancelToken,
    requestInstance,
    chunkSize,
    retries,
    withCredentials,
}) {
    const uploadId = createUploadId()
    const totalSize = file.size || 0
    const totalChunks = Math.max(1, Math.ceil(totalSize / chunkSize))
    let finalResponse = null

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex += 1) {
        const start = chunkIndex * chunkSize
        const end = Math.min(start + chunkSize, totalSize)
        const chunk = file.slice(start, end)

        const { data } = await postWithRetry(() => {
            const formData = new FormData()
            formData.append(fieldName, chunk, fileName)
            appendFormData(formData, extraData)
            formData.append('upload_id', uploadId)
            formData.append('chunk_index', String(chunkIndex))
            formData.append('total_chunks', String(totalChunks))
            formData.append('original_name', fileName)
            formData.append('chunked_upload', 'true')
            formData.append('file_size', String(totalSize))

            return requestInstance.post(url, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    ...headers
                },
                withCredentials,
                cancelToken,
                onUploadProgress: ({ loaded }) => emitProgress(onProgress, start + loaded, totalSize)
            })
        }, retries)

        emitProgress(onProgress, end, totalSize)
        finalResponse = data
    }

    return finalResponse
}

export async function uploadFile({
    file,
    url = '/common/upload/',
    fieldName = 'upload',
    fileName = file?.name || 'upload.bin',
    extraData = {},
    headers = {},
    onProgress,
    cancelToken,
    requestInstance = request,
    chunkSize = DEFAULT_UPLOAD_CHUNK_SIZE,
    mode = 'auto',
    retries = DEFAULT_CHUNK_RETRIES,
    withCredentials,
} = {}) {
    if (!file)
        throw new Error('File is required for upload.')

    const shouldUseChunks = (
        mode === 'chunked'
        || (mode === 'auto' && file.size > chunkSize && isChunkCapableUrl(url))
    )

    if (!shouldUseChunks) {
        return uploadDirect({
            file,
            url,
            fieldName,
            fileName,
            extraData,
            headers,
            onProgress,
            cancelToken,
            requestInstance,
            withCredentials,
        })
    }

    return uploadChunked({
        file,
        url,
        fieldName,
        fileName,
        extraData,
        headers,
        onProgress,
        cancelToken,
        requestInstance,
        chunkSize,
        retries,
        withCredentials,
    })
}

export default uploadFile
