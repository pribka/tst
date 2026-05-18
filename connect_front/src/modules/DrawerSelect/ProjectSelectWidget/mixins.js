import { mapState } from 'vuex'
import axios from 'axios'
import { errorHandler } from '@/utils/index.js'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: { type: [Object, Array, String] },
        selectProject: { type: Function, default: () => {} },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'projects_select' },
        dbId: { type: String, default: 'user' },
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
        candidates: {
            type: Array,
            default: () => {}
        },
        showClear: {
            type: Boolean,
            default: true
        },
        usePopupContainer: {
            type: Boolean,
            default: false
        },
        customPopupContainer: {
            type: [Function, Object],
            default: () => {}
        },
        useInputIcon: {
            type: Boolean,
            default: false
        },
        showArrow: {
            type: Boolean,
            default: false
        },
        initList: {
            type: Boolean,
            default: false
        },
        autoAdjustOverflow: {
            type: Boolean,
            default: true
        },
        multiple: {
            type: Boolean,
            default: false
        },
        disabled: {
            type: Boolean,
            default: false
        },
        apiUrl: {
            type: String,
            default: '/work_groups/workgroups/'
        },
        params: {
            type: Object,
            default: () => ({})
        },
        pageSize: {
            type: [Number, String],
            default: null
        },
        resultsKey: {
            type: String,
            default: 'results'
        },
        stringifyFilters: {
            type: Boolean,
            default: false
        },
        showRecent: {
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
            recentList: []
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
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMultiple() {
            return this.multiple
        },
        selectedList() {
            if (this.isMultiple) {
                return Array.isArray(this.value) ? this.value : []
            }
            return this.value ? [this.value] : []
        },
        hasValue() {
            return this.selectedList.length > 0
        },
        firstSelected() {
            return this.selectedList[0] || null
        },
        valueTitle() {
            if (!this.hasValue) {
                return this.placeholder || this.$t('project_label')
            }
            if (this.isMultiple) {
                return `${this.$t('project_label')}: ${this.selectedList.map(item => item.name).join(', ')}`
            }
            return `${this.$t('project_label')}: ${this.firstSelected?.name || ''}`
        }
    },
    methods: {
        open() {
            this.openSelect()
        },
        openSelect() {
            if (this.disabled) return
            this.visibleChange(true)
        },
        getPopupContainer(trigger) {
            if (this.usePopupContainer)
                return this.customPopupContainer()
            return trigger.parentNode
        },
        clear() {
            const emptyValue = this.isMultiple ? [] : null
            this.$emit('input', emptyValue)
            this.$emit('change', emptyValue)
        },
        clearAndClose() {
            this.clear()
            this.visible = false
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                if (this.cancelSource)
                    this.cancelSource.cancel()
                setTimeout(() => {
                    if (this.search.length && this.search.length > 2) this.getWorkList()
                    else this.getWorkList()
                }, 100)
            }, 700)
        },
        inputFocus() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    const el = this.$refs.searchInput && this.$refs.searchInput.$refs && this.$refs.searchInput.$refs.input
                    if (el) el.focus()
                })
            })
        },
        async visibleChange(vis) {
            if (this.disabled && vis) return
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
                if (this.showRecent) await this.loadRecent()
                else this.recentList = []
                this.inputFocus()
            }
        },
        checkSelected(work) {
            if (this.selectedList.some(item => item?.id === work.id)) return 'active'
            else return ''
        },
        async selectWork(work) {
            if (this.isMultiple) {
                const selectedList = [...this.selectedList]
                const index = selectedList.findIndex(item => item?.id === work.id)
                if (index !== -1) {
                    selectedList.splice(index, 1)
                } else {
                    selectedList.push(work)
                    await this.pushToRecent(work)
                }
                this.$emit('input', selectedList)
                this.selectProject(selectedList)
                this.$emit('change', selectedList)
            } else {
                if (work.id === (this.value && this.value.id)) {
                    this.$emit('input', null)
                    this.selectProject(null)
                } else {
                    this.$emit('input', work)
                    this.selectProject(work)
                    await this.pushToRecent(work)
                }
                this.visible = false
                this.$emit('change', work)
            }
        },
        async getWorkList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1
                    const params = this.normalizeRequestParams({
                        page_size: this.pageSize || (this.isMobile ? 20 : 15),
                        page: this.page,
                        is_project: 1,
                        page_name: 'project_drawer',
                        filters: { is_finished: false }
                    })
                    if (this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get(this.apiUrl, { params, cancelToken: axiosSource.token })
                    const results = Array.isArray(data?.[this.resultsKey]) ? data[this.resultsKey] : []
                    if (results.length) this.workList.push(...results)
                    if (!data.next) {
                        if ($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state)
                            $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.cancelSource = null
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state)
                    $state.complete()
            }
        },
        normalizeRequestParams(baseParams) {
            const params = {
                ...baseParams,
                ...this.params,
                filters: {
                    ...(baseParams.filters || {}),
                    ...(this.params?.filters || {})
                }
            }

            if (this.stringifyFilters && params.filters && typeof params.filters === 'object') {
                params.filters = JSON.stringify(params.filters)
            }

            return params
        },
        workgroupLogoPath(workgroup) {
            return workgroup && workgroup.workgroup_logo && workgroup.workgroup_logo.path ? workgroup.workgroup_logo.path : ''
        },
        async loadRecent() {
            const arr = await this.idbGet(this.recordKey)
            this.recentList = Array.isArray(arr) ? arr : []
            this.$emit('recent-change', this.recentList)
        },
        async pushToRecent(work) {
            const base = this.recentList.filter(i => i && i.id !== work.id)
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
