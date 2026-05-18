export default {
    list: s => s.list,
    hasAny: s => Array.isArray(s.list) && s.list.length > 0,
    isLoaded: s => s.loaded,
    isLoading: s => s.loading
}
