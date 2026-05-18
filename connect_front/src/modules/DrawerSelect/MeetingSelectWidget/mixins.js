import axios from 'axios'
import { errorHandler } from '@/utils/index.js'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: { type: Object, default: null },
        placeholder: { type: String, default: '' },
        showClear: { type: Boolean, default: true },
        inputType: { type: String, default: 'defaultInput' },
        getPopupContainerFn: { type: Function, default: null }
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
            meetingList: []
        }
    },
    computed: {
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
            if (this.getPopupContainerFn) return this.getPopupContainerFn()
            return trigger.parentNode
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.meetingList.splice(0)
                if (this.cancelSource) this.cancelSource.cancel()
                setTimeout(() => { this.infiniteId += 1 }, 100)
            }, 700)
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.meetingList.splice(0)
                this.infiniteId += 1
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
        checkSelected(item) {
            if (this.value?.id === item.id) return 'active'
            return ''
        },
        selectItem(item) {
            if (item.id === this.value?.id) {
                this.$emit('input', null)
                this.$emit('change', null)
            } else {
                this.$emit('input', item)
                this.$emit('change', item)
            }
            this.visible = false
        },
        async getMeetingList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page += 1
                    const params = {
                        model: 'meetings.PlannedMeetingModel',
                        page: this.page
                    }
                    if (this.search) {
                        params.search = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get('/app_info/filtered_select_list/', { params, cancelToken: axiosSource.token })
                    if (data?.filteredSelectList?.length) this.meetingList.push(...data.filteredSelectList)
                    if (!data.next) {
                        if ($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state) $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                    if ($state) $state.complete()
                } finally {
                    this.cancelSource = null
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state) $state.complete()
            }
        }
    }
}
