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
        selectFirst: {
            type: Boolean,
            default: false
        },
        initLoading: {
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
            workList: []
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
        openSelect() {
            this.visibleChange(true)
        },
        open() {
            this.openSelect()
        },
        getPopupContainer(trigger) {
            if(this.usePopupContainer)
                return this.customPopupContainer()
            return trigger.parentNode
        },
        clear() {
            this.$emit('input', null)
            this.$emit('change', null)
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
                if (this.cancelSource)
                    this.cancelSource.cancel()
                setTimeout(() => {
                    this.getWorkList()
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
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
                this.inputFocus()
            }
        },
        checkSelected(work) {
            if(this.value && this.value.id === work.id) return 'active'
            else return ''
        },
        async selectWork(work) {
            if(work.id === (this.value && this.value.id)) {
                this.$emit('input', null)
                this.selectProject(null)
            } else {
                this.$emit('input', work)
                this.selectProject(work)
            }
            this.visible = false
            this.$emit('change', work)
        },
        async getWorkList($state = null) {
            if(!this.loading && this.scrollStatus && (this.visible || this.initLoading)) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1
                    const params = {
                        page_size: this.isMobile ? 20 : 15,
                        page: this.page,
                        model: 'event_calendar.CalendarModel'
                    }
                    if(this.search) {
                        params.text = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get('/app_info/filtered_select_list/', { params, cancelToken: axiosSource.token })
                    if(data?.filteredSelectList?.length) {
                        this.workList.push(...data.filteredSelectList)
                        if(this.selectFirst && !this.value && this.page === 1) {
                            this.$emit('input', data.filteredSelectList[0])
                            this.$emit('change', data.filteredSelectList[0])
                        }
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.cancelSource = null
                    if(this.search)
                        this.searchLoading = false
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    },
    mounted() {
        if(this.initLoading)
            this.getWorkList()
    }
}
