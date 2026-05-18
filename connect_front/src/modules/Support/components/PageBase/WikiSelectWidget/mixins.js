import { errorHandler } from '@/utils/index.js'

let timer = null

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: {
            type: [Object, String],
            default: null
        },
        contractorId: {
            type: [String, Number],
            default: null
        },
        disabled: {
            type: Boolean,
            default: false
        },
        selectItem: {
            type: Function,
            default: () => {}
        },
        endpoint: {
            type: String,
            required: true
        },
        title: {
            type: String,
            default: ''
        },
        placeholder: {
            type: String,
            default: ''
        },
        placement: {
            type: String,
            default: 'bottomLeft'
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
            itemList: []
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
        openSelect() {
            if (this.disabled) return
            this.visibleChange(true)
        },
        open() {
            this.openSelect()
        },
        getPopupContainer(trigger) {
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
                this.itemList = []
                this.infiniteId += 1
            }, 400)
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.itemList = []
                this.infiniteId += 1
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        const input = this.$refs.searchInput?.$refs?.input
                        if (input) input.focus()
                    })
                })
            }
        },
        checkSelected(item) {
            return this.value && this.value.id === item.id ? 'active' : ''
        },
        selectEntity(item) {
            this.$emit('input', item)
            this.$emit('change', item)
            this.selectItem(item)
            this.visible = false
        },
        async getItemList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    const params = {
                        page_size: this.isMobile ? 20 : 15,
                        page: this.page
                    }

                    if (this.contractorId) {
                        params.contractor = this.contractorId
                    }

                    if (this.search) {
                        params.text = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get(this.endpoint, { params })
                    if(data?.results?.length)
                        this.itemList.push(...data.results)

                    if(!data?.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else if($state) {
                        $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    if (this.search) this.searchLoading = false
                    this.loading = false
                }
            } else if($state) {
                $state.complete()
            }
        }
    }
}
