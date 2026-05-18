<template>
    <a-modal
        :title="$t('dashboard.selectEvent')"
        class="event_select_drawer"
        :width="isMobile ? '100%' : 620"
        destroyOnClose
        :dialog-style="{ top: '20px' }"
        :visible="visible"
        :afterVisibleChange="afterVisibleChange"
        @cancel="closeHandler()">
        <a-input-search
            class="mb-4 search_input"
            :loading="searchLoading"
            v-model="search"
            ref="searchInput"
            size="large"
            @input="onSearch"
            :placeholder="$t('dashboard.event')" />
        <div ref="event_scroll" class="max-w-full">
            <div
                v-if="searchLoading && !eventList.length"
                class="search_loading_state">
                <a-spin />
            </div>
            <EventSelectItem
                v-for="item in eventList"
                :key="item.id"
                :item="item"
                :selectFunction="selectEvent" />
            <infinite-loading
                ref="eventInfinite"
                @infinite="getEventList"
                :distance="10">
                <div slot="spinner">
                    <a-spin class="w-full" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <template #footer>
            <a-button
                block
                type="ui"
                ghost
                class="px-8"
                @click="closeHandler">
                {{ $t('dashboard.close') }}
            </a-button>
        </template>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
let timer
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        EventSelectItem: () => import('./EventSelectItem.vue')
    },
    props: {
        value: {
            type: Object,
            default: null
        },
        visible: {
            type: Boolean,
            default: false
        },
        closeHandler: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            searchLoading: false,
            eventList: [],
            search: '',
            scrollStatus: true,
            page: 0,
            loading: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    if(this.$refs.searchInput)
                        this.$refs.searchInput.focus()
                })
            }
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.searchLoading = true
                this.scrollStatus = true
                this.page = 0
                this.eventList = []
                this.getEventList().finally(() => {
                    this.searchLoading = false
                })
            }, 500)
        },
        selectEvent(item) {
            this.$emit('input', item)
            this.closeHandler()
        },
        async getEventList($state = null) {
            if(!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        paginate: 1,
                        page_size: 15,
                        page: this.page
                    }
                    if(this.search?.length)
                        params.search = this.search

                    const { data } = await this.$http.get('/calendars/events/top/', { params })

                    if(data?.results?.length)
                        this.eventList = this.eventList.concat(data.results)

                    if(!data?.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else if($state) {
                        $state.loaded()
                    }
                } catch(error) {
                    if($state)
                        $state.complete()
                    errorHandler({ error, show: false })
                } finally {
                    this.loading = false
                }
            } else if($state) {
                $state.complete()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
        }
    }
}

.search_loading_state{
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
