const PREVIEWABLE_EXTENSIONS = new Set([
    'csv',
    'doc',
    'docm',
    'docx',
    'dot',
    'dotm',
    'dotx',
    'fodp',
    'fods',
    'fodt',
    'odp',
    'ods',
    'odt',
    'pot',
    'potm',
    'potx',
    'pps',
    'ppsm',
    'ppsx',
    'pdf',
    'ppt',
    'pptm',
    'pptx',
    'rtf',
    'txt',
    'xls',
    'xlsb',
    'xlsm',
    'xlsx'
])

export function normalizeFileExtension(fileOrExtension) {
    const raw = typeof fileOrExtension === 'string'
        ? fileOrExtension
        : fileOrExtension?.extension

    return String(raw || '').toLowerCase().replace(/^\./, '')
}

export function isOnlyofficePreviewable(fileOrExtension) {
    return PREVIEWABLE_EXTENSIONS.has(normalizeFileExtension(fileOrExtension))
}

export function buildOnlyofficePreviewLocation(router, query = {}) {
    return router.resolve({
        name: 'office-preview',
        query
    })
}

export function buildOnlyofficePreviewHref(router, query = {}) {
    return buildOnlyofficePreviewLocation(router, query).href
}

export function openOnlyofficePreview(store, query = {}) {
    store.commit('OPEN_ONLYOFFICE_PREVIEW', query)
}
