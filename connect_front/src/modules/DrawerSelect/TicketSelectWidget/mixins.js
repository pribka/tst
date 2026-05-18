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
        inputType: { type: String, default: 'button' },
        placeholder: { type: String, default: '' },
        showClear: { type: Boolean, default: true },
        usePopupContainer: { type: Boolean, default: false },
        customPopupContainer: { type: [Function, Object], default: () => {} },
        showArrow: { type: Boolean, default: false }
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
            list: []
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        ticketTitle() {
            if (this.value) {
                const number = this.value.number ? `#${this.value.number}` : ''
                return `${number} ${this.value.name || ''}`.trim()
            }
            return this.placeholder || this.$t('dashboard.select')
        }
    },
    methods: {
        open() {
            this.openSelect()
        },
        openSelect() {
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
                this.list.splice(0)
                if (this.cancelSource)
                    this.cancelSource.cancel()
                setTimeout(() => {
                    this.getList()
                }, 100)
            }, 700)
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.list.splice(0)
                this.infiniteId += 1
                this.inputFocus()
            }
        },
        checkSelected(item) {
            if (this.value?.id && item?.id && this.value.id === item.id) return 'active'
            return ''
        },
        async selectItem(item) {
            if (item?.id && this.value?.id && item.id === this.value.id) {
                this.$emit('input', null)
                this.selectProject(null)
            } else {
                this.$emit('input', item)
                this.selectProject(item)
            }
            this.visible = false
            this.$emit('change', item)
        },
        async getList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1

                    const params = {
                        page_size: this.isMobile ? 20 : 15,
                        page: this.page
                    }

                    if (this.search?.length)
                        params.search = this.search

                    this.searchLoading = Boolean(this.search?.length)

                    const { data } = await this.$http.get('/help_desk/tickets/', { params, cancelToken: axiosSource.token })

                    if (data?.results?.length)
                        this.list.push(...data.results)

                    if (!data?.next) {
                        if ($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state) $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.cancelSource = null
                    this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state) $state.complete()
            }
        }
    }
}
