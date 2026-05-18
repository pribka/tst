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
        organizationId: {
            type: String,
            required: true
        },
        excludedUserIds: {
            type: Array,
            default: () => []
        },
        inputType: {
            type: String,
            default: 'bordered_input'
        },
        placeholder: {
            type: String,
            default: ''
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        pageName: {
            type: String,
            default: 'organization_user_mini_select'
        },
        pageSize: {
            type: Number,
            default: 15
        },
        disabled: {
            type: Boolean,
            default: false
        },
        showIcon: {
            type: Boolean,
            default: true
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        showRecent: {
            type: Boolean,
            default: false
        },
        size: {
            type: String,
            default: 'default'
        },
        getPopupContainer: {
            type: Function,
            default: null
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
        sizeTypes() {
            if (this.size === 'large') return 'lg'
            if (this.size === 'small') return 'sm'
            return ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        resolvedPageSize() {
            return this.isMobile ? 20 : this.pageSize
        },
        endpoint() {
            return `/users/my_organizations/${this.organizationId}/users/`
        },
        filteredExcludedIds() {
            return new Set(this.excludedUserIds || [])
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
        inputFocus() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    const el = this.$refs.searchInput && this.$refs.searchInput.$refs && this.$refs.searchInput.$refs.input
                    if (el) el.focus()
                })
            })
        },
        popupContainer(trigger) {
            if (this.getPopupContainer) {
                return this.getPopupContainer(trigger)
            }

            return trigger.parentNode
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                if (this.cancelSource) this.cancelSource.cancel()
                this.getWorkList()
            }, 500)
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                this.infiniteId += 1
                if (this.showSearch) this.inputFocus()
            }
        },
        checkSelected(work) {
            if (this.value && this.value.id === work.id) return 'active'
            return ''
        },
        async selectWork(work) {
            if (work.id === (this.value && this.value.id)) {
                this.$emit('input', null)
                this.$emit('change', null)
            } else {
                this.$emit('input', work)
                this.$emit('change', work)
            }

            this.visible = false
        },
        async getWorkList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page += 1

                    const params = {
                        page_size: this.resolvedPageSize,
                        page: this.page,
                        page_name: this.pageName
                    }

                    if (this.search) {
                        params.text = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get(this.endpoint, {
                        params,
                        cancelToken: axiosSource.token
                    })

                    const results = (data?.results || []).filter(item => !this.filteredExcludedIds.has(item.id))
                    if (results.length) {
                        this.workList.push(...results)
                    }

                    if (!data?.next) {
                        this.scrollStatus = false
                        if ($state) $state.complete()
                    } else if ($state) {
                        $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.cancelSource = null
                    this.searchLoading = false
                    this.loading = false
                }
            } else if ($state) {
                $state.complete()
            }
        }
    }
}
