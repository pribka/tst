<template>
    <div class="news_list">
        <div class="news_list__body">
            <div v-if="user && user.is_staff" class="mb-4">
                <a-button @click="openCreate()">
                    {{ $t('support.addNews') }}
                </a-button>
            </div>
            <div v-if="empty" class="pt-4">
                <a-empty :description="$t('support.noNewNews')" />
            </div>
            <NewsCard v-for="item in list.results" :key="item.id" :item="item" :setNewsRead="setNewsRead" />
            <infinite-loading 
                ref="news_d_infinity"
                @infinite="getNews"
                v-bind:distance="10">
                <div 
                    slot="spinner"
                    class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <CreateDrawer ref="createDrawer" :resetList="resetList" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        NewsCard: () => import('./NewsCard.vue'),
        CreateDrawer: () => import('./CreateDrawer.vue')
    },
    props: {
        drawerClose: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        }
    },
    data() {
        return {
            page: 0,
            loading: false,
            empty: false,
            list: {
                results: [],
                next: true
            }
        }
    },
    methods: {
        openCreate() {
            this.$nextTick(() => {
                this.$refs.createDrawer.openDrawer()
            })
        },
        setNewsRead(id) {
            if(this.list.results?.length) {
                const index = this.list.results.findIndex(f => f.id === id)
                if(index !== -1) {
                    this.list.results[index].has_read = true
                }
            }
        },
        onListReload() {
            this.resetList()
        },
        resetList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true
                }
                this.$refs['news_d_infinity'].stateChanger.reset()
            })
        },
        async getNews($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/news/news/list/', {
                        params: {
                            page: this.page,
                            page_size: 6
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({ error, show: false })
                    $state.complete()
                } finally {
                    this.loading = false
                }
            }
        }
    },
    mounted() {
        eventBus.$on('support_news_list_reload', this.onListReload)
    },
    beforeDestroy() {
        eventBus.$off('support_news_list_reload', this.onListReload)
    }
}
</script>
