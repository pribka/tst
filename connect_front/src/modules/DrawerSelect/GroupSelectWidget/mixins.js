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
        storeName: { type: String, default: 'groups_select' },
        dbId: { type: String, default: 'user' },
        inputType: {
            type: String,
            default: 'button'
        },
        placeholder: {
            type: String,
            default: ''
        },
        useInputIcon: {
            type: Boolean,
            default: false
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
        showArrow: {
            type: Boolean,
            default: false
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
        }
    },
    methods: {
        open() {
            this.openSelect()
        },
        openSelect() {
            this.visibleChange(true)
        },
        clear() {
            this.$emit('input', null)
            this.$emit('change', null)
        },
        clearAndClose() {
            this.clear()
            this.visible = false
        },
        getPopupContainer(trigger) {
            if (this.usePopupContainer)
                return this.customPopupContainer()
            return trigger.parentNode
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
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
                await this.loadRecent()
                this.inputFocus()
            }
        },
        inputFocus() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    const el = this.$refs.searchInput && this.$refs.searchInput.$refs && this.$refs.searchInput.$refs.input
                    if (el) el.focus()
                })
            })
        },
        checkSelected(work) {
            if (this.value?.id === work.id) return 'active'
            return ''
        },
        async selectWork(work) {
            if (work.id === this.value?.id) {
                this.$emit('input', null)
                this.selectProject(null)
            } else {
                this.$emit('input', work)
                this.selectProject(work)
                await this.pushToRecent(work)
            }
            this.visible = false
            this.$emit('change', work)
        },
        async getWorkList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1
                    const params = {
                        page_size: this.isMobile ? 20 : 15,
                        page: this.page,
                        is_project: 0,
                        page_name: 'group_drawer',
                        filters: { is_finished: false }
                    }
                    if (this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get('/work_groups/workgroups/', { params, cancelToken: axiosSource.token })
                    if (data?.results?.length) this.workList.push(...data.results)
                    if (!data.next) {
                        if ($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state) $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.cancelSource = null
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state) $state.complete()
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
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
