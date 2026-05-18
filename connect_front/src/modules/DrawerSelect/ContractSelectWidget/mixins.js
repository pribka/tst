import { mapState } from 'vuex'
import axios from 'axios'
import { errorHandler } from '@/utils/index.js'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: { type: [Object, String, Number], default: null },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'api_select' },
        dbId: { type: String, default: 'api_select' },
        inputType: {
            type: String,
            default: 'button'
        },
        placeholder: {
            type: String,
            default: ''
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        apiUrl: {
            type: String,
            required: true
        },
        params: {
            type: Object,
            default: () => ({})
        },
        listObject: {
            type: String,
            default: 'results'
        },
        valueKey: {
            type: String,
            default: 'id'
        },
        labelKey: {
            type: String,
            default: 'name'
        },
        searchKey: {
            type: String,
            default: 'text'
        },
        pageName: {
            type: String,
            default: ''
        },
        pageSize: {
            type: Number,
            default: 15
        },
        pagination: {
            type: Boolean,
            default: false
        },
        showIcon: {
            type: Boolean,
            default: false
        },
        iconClass: {
            type: String,
            default: 'fi-rr-folder'
        },
        disabled: {
            type: Boolean,
            default: false
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        showRecent: {
            type: Boolean,
            default: true
        },
        showClear: {
            type: Boolean,
            default: true
        },
        showArrow: {
            type: Boolean,
            default: true
        },
        size: {
            type: String,
            default: 'default'
        },
        title: {
            type: String,
            default: ''
        },
        searchPlaceholder: {
            type: String,
            default: ''
        },
        initList: {
            type: Boolean,
            default: true
        },
        useSearchApi: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            cancelSource: null,
            search: '',
            searchLoading: false,
            scrollStatus: true,
            page: 0,
            infiniteId: 0,
            visible: false,
            loading: false,
            workList: [],
            recentList: [],
            selectedOption: null
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        userId() {
            return this.user?.id || 'guest'
        },
        recordKey() {
            return `${this.dbId}_${this.userId}`
        },
        sizeTypes() {
            if (this.size === 'large')
                return 'lg'
            if (this.size === 'small')
                return 'sm'
            return ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        resolvedTitle() {
            return this.title || this.placeholder
        },
        resolvedSearchPlaceholder() {
            return this.searchPlaceholder || this.placeholder
        },
        selectedId() {
            if (!this.value) return null
            if (typeof this.value === 'object')
                return this.getItemId(this.value)
            return this.value
        },
        currentValue() {
            if (this.value && typeof this.value === 'object')
                return this.value
            if (this.selectedOption && this.getItemId(this.selectedOption) === this.selectedId)
                return this.selectedOption
            return null
        },
        hasValue() {
            return Boolean(this.currentValue || this.selectedId)
        },
        displayedWorkList() {
            if (!this.search || this.useSearchApi)
                return this.workList

            const search = this.search.toLowerCase().trim()
            return this.workList.filter(item => {
                const label = String(this.getItemLabel(item) || '').toLowerCase()
                return label.includes(search)
            })
        },
        valueTitle() {
            if (!this.currentValue)
                return this.resolvedTitle || this.placeholder

            return this.resolvedTitle
                ? `${this.resolvedTitle}: ${this.getItemLabel(this.currentValue)}`
                : this.getItemLabel(this.currentValue)
        }
    },
    watch: {
        value: {
            immediate: true,
            handler(value) {
                if (value && typeof value === 'object') {
                    this.selectedOption = value
                } else if (!value) {
                    this.selectedOption = null
                }
            }
        },
        apiUrl() {
            this.resetState()
        },
        params: {
            deep: true,
            handler() {
                this.resetState()
            }
        }
    },
    methods: {
        open() {
            this.openSelect()
        },
        openSelect() {
            if (this.disabled)
                return
            this.visibleChange(true)
        },
        inputFocus() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    const el = this.$refs.searchInput && this.$refs.searchInput.$refs && this.$refs.searchInput.$refs.input
                    if (el) el.focus()
                })
            })
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        getValueByPath(item, path) {
            if (!item || !path) return ''
            return path.split('.').reduce((acc, key) => {
                if (acc === null || typeof acc === 'undefined') return ''
                return acc[key]
            }, item)
        },
        getItemId(item) {
            return this.getValueByPath(item, this.valueKey)
        },
        getItemLabel(item) {
            return this.getValueByPath(item, this.labelKey)
        },
        normalizeSearchValue(value) {
            if (typeof value === 'string')
                return value
            if (value && typeof value === 'object' && value.target)
                return value.target.value || ''
            return ''
        },
        onSearch(value) {
            const nextValue = this.normalizeSearchValue(value)
            if (nextValue !== this.search)
                this.search = nextValue

            if (!this.useSearchApi)
                return

            clearTimeout(timer)
            timer = setTimeout(() => {
                this.resetState(false)
                if (this.visible)
                    this.getWorkList()
            }, 700)
        },
        resetState(resetSearch = true) {
            this.scrollStatus = true
            this.loading = false
            this.page = 0
            this.workList.splice(0)
            this.infiniteId += 1
            if (resetSearch)
                this.search = ''
            if (this.cancelSource)
                this.cancelSource.cancel()
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.resetState(false)
                if (this.showRecent)
                    await this.loadRecent()
                if (this.showSearch)
                    this.inputFocus()
            }
        },
        checkSelected(work) {
            if (this.selectedId === this.getItemId(work)) return 'active'
            return ''
        },
        clear() {
            this.selectedOption = null
            this.$emit('input', null)
            this.$emit('change', null)
        },
        async selectWork(work) {
            if (this.selectedId === this.getItemId(work)) {
                this.clear()
            } else {
                this.selectedOption = work
                this.$emit('input', work)
                this.$emit('change', work)
                if (this.showRecent)
                    await this.pushToRecent(work)
            }
            this.visible = false
        },
        normalizeResponse(data) {
            if (Array.isArray(data)) {
                return {
                    items: data,
                    hasMore: false
                }
            }

            const items = Array.isArray(data?.[this.listObject])
                ? data[this.listObject]
                : Array.isArray(data?.results)
                    ? data.results
                    : []

            return {
                items,
                hasMore: this.pagination ? Boolean(data?.next) : false
            }
        },
        mergeUniqueItems(items) {
            items.forEach(item => {
                if (!this.workList.some(listItem => this.getItemId(listItem) === this.getItemId(item)))
                    this.workList.push(item)
            })

            if (this.selectedId && !this.selectedOption) {
                const selected = this.workList.find(item => this.getItemId(item) === this.selectedId)
                if (selected)
                    this.selectedOption = selected
            }
        },
        async getWorkList($state = null) {
            if (!this.initList && !this.search.length) {
                this.scrollStatus = false
                if ($state)
                    $state.complete()
                return
            }

            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1

                    const params = { ...this.params }
                    if (this.pagination) {
                        params.page_size = this.isMobile ? 20 : this.pageSize
                        params.page = this.page
                        if (this.pageName)
                            params.page_name = this.pageName
                    }

                    if (this.useSearchApi && this.search) {
                        params[this.searchKey] = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get(this.apiUrl, { params, cancelToken: axiosSource.token })
                    const { items, hasMore } = this.normalizeResponse(data)

                    if (items.length)
                        this.mergeUniqueItems(items)

                    if (!hasMore) {
                        if ($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else if ($state) {
                        $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.cancelSource = null
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else if ($state) {
                $state.complete()
            }
        },
        async loadRecent() {
            const arr = await this.idbGet(this.recordKey)
            this.recentList = Array.isArray(arr) ? arr : []
            this.$emit('recent-change', this.recentList)
        },
        async pushToRecent(work) {
            const base = this.recentList.filter(i => i && this.getItemId(i) !== this.getItemId(work))
            base.unshift(work)
            const sliced = base.slice(0, 8)
            this.recentList = sliced
            await this.idbSet(this.recordKey, sliced)
            this.$emit('recent-change', this.recentList)
        },
        async idbEnsureStore() {
            return await new Promise((resolve, reject) => {
                const req = window.indexedDB.open(this.dbName)
                req.onsuccess = e => {
                    const db = e.target.result
                    const has = Array.from(db.objectStoreNames).includes(this.storeName)
                    if (has) resolve(db)
                    else {
                        const newVersion = db.version + 1
                        db.close()
                        const req2 = window.indexedDB.open(this.dbName, newVersion)
                        req2.onupgradeneeded = ev => {
                            const db2 = ev.target.result
                            if (!db2.objectStoreNames.contains(this.storeName)) db2.createObjectStore(this.storeName, { keyPath: 'id' })
                        }
                        req2.onsuccess = ev => resolve(ev.target.result)
                        req2.onerror = err => reject(err)
                    }
                }
                req.onerror = err => reject(err)
            })
        },
        async idbGet(id) {
            try {
                const db = await this.idbEnsureStore()
                return await new Promise((resolve, reject) => {
                    const tx = db.transaction([this.storeName], 'readonly')
                    const store = tx.objectStore(this.storeName)
                    const r = store.get(id)
                    r.onsuccess = () => resolve(r.result ? r.result.value : null)
                    r.onerror = e => reject(e)
                })
            } catch (e) {
                return null
            }
        },
        async idbSet(id, value) {
            try {
                const db = await this.idbEnsureStore()
                await new Promise((resolve, reject) => {
                    const tx = db.transaction([this.storeName], 'readwrite')
                    const store = tx.objectStore(this.storeName)
                    const r = store.put({ id, value })
                    r.onsuccess = () => resolve()
                    r.onerror = e => reject(e)
                })
                return true
            } catch (e) {
                return false
            }
        }
    }
}
