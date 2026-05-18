import { mapState } from 'vuex'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: { type: [Object, Array, String] },
        selectProject: { type: Function, default: () => {} },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'organizations_select' },
        dbId: { type: String, default: 'user' },
        placeholder: {
            type: String,
            default: ''
        },
        opnUserSetting: {
            type: Function,
            default: () => {}
        },
        inputType: {
            type: String,
            default: 'button'
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        autoAdjustOverflow: {
            type: Boolean,
            default: true
        },
        showDefaultOrganizationSwitcher: {
            type: Boolean,
            default: true
        },
        apiUrl: {
            type: String,
            default: '/users/my_organizations/'
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
        showRecent: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
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
        openUserSetting() {
            this.visible = false
            this.opnUserSetting()
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                if (this.search.length && this.search.length > 2) this.getWorkList()
                else this.getWorkList()
            }, 800)
        },
        async visibleChange(vis) {
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
            this.$emit('input', work)
            this.selectProject(work)
            if (this.showRecent) await this.pushToRecent(work)
            this.visible = false
            this.$emit('change', work)
        },
        async getWorkList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    const params = {
                        page_size: this.pageSize || (this.isMobile ? 20 : 15),
                        page: this.page,
                        display: 'tree',
                        page_name: 'select_organization_drawer_list',
                        ...this.params
                    }
                    if (this.search) {
                        params.search = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get(this.apiUrl, { params })
                    const list = Array.isArray(data) ? data : (Array.isArray(data?.[this.resultsKey]) ? data[this.resultsKey] : [])
                    if (list.length) this.workList.push(...list)
                    const hasNext = !Array.isArray(data) && Boolean(data?.next)
                    if (!hasNext) {
                        if ($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state) $state.loaded()
                    }
                } finally {
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state) $state.complete()
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.logo || ''
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
