import { mapState } from 'vuex'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: {
            type: Object,
            default: null
        },
        selectProject: {
            type: Function,
            default: () => {}
        },
        dbName: {
            type: String,
            default: 'old_select'
        },
        storeName: {
            type: String,
            default: 'organizations_select'
        },
        dbId: {
            type: String,
            default: 'support_wiki'
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
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    methods: {
        openSelect() {
            this.visibleChange(true)
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
            }, 500)
        },
        async visibleChange(vis) {
            this.visible = vis

            if(vis) {
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
                    const el = this.$refs.searchInput?.$refs?.input
                    if(el) el.focus()
                })
            })
        },
        checkSelected(work) {
            return this.value?.id === work.id ? 'active' : ''
        },
        async selectWork(work) {
            if(this.value?.id === work.id) {
                this.visible = false
                return
            }

            this.$emit('input', work)
            await this.selectProject(work)
            await this.pushToRecent(work)
            this.visible = false
        },
        async getWorkList($state = null) {
            if(!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page_size: this.$store.state.isMobile ? 20 : 15,
                        page: this.page,
                        display: 'tree',
                        page_name: 'select_organization_drawer_list'
                    }

                    if(this.search) {
                        params.search = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get('/users/my_organizations/', { params })

                    if(data?.results?.length)
                        this.workList.push(...data.results)

                    if(!data?.next) {
                        this.scrollStatus = false
                        if($state) $state.complete()
                    } else if($state) {
                        $state.loaded()
                    }
                } finally {
                    this.loading = false
                    this.searchLoading = false
                }
            } else if($state) {
                $state.complete()
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.logo || workgroup?.workgroup_logo?.path || ''
        },
        async loadRecent() {
            const arr = await this.idbGet(this.recordKey)
            this.recentList = Array.isArray(arr) ? arr : []
        },
        async pushToRecent(work) {
            const nextValue = this.recentList.filter(item => item && item.id !== work.id)
            nextValue.unshift(work)
            this.recentList = nextValue.slice(0, 8)
            await this.idbSet(this.recordKey, this.recentList)
        },
        async idbEnsureStore() {
            return await new Promise((resolve, reject) => {
                const req = window.indexedDB.open(this.dbName)
                req.onsuccess = e => {
                    const db = e.target.result
                    const has = Array.from(db.objectStoreNames).includes(this.storeName)

                    if(has) {
                        resolve(db)
                        return
                    }

                    const newVersion = db.version + 1
                    db.close()
                    const req2 = window.indexedDB.open(this.dbName, newVersion)
                    req2.onupgradeneeded = ev => {
                        const db2 = ev.target.result
                        if(!db2.objectStoreNames.contains(this.storeName))
                            db2.createObjectStore(this.storeName, { keyPath: 'id' })
                    }
                    req2.onsuccess = ev => resolve(ev.target.result)
                    req2.onerror = err => reject(err)
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
                    const req = store.get(id)
                    req.onsuccess = () => resolve(req.result ? req.result.value : null)
                    req.onerror = err => reject(err)
                })
            } catch(error) {
                return null
            }
        },
        async idbSet(id, value) {
            try {
                const db = await this.idbEnsureStore()
                await new Promise((resolve, reject) => {
                    const tx = db.transaction([this.storeName], 'readwrite')
                    const store = tx.objectStore(this.storeName)
                    const req = store.put({ id, value })
                    req.onsuccess = () => resolve()
                    req.onerror = err => reject(err)
                })
            } catch(error) {
                return false
            }

            return true
        }
    }
}
