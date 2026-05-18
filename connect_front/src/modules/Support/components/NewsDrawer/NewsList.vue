<template>
    <div class="news_list h-full">
        <div class="news_list__header">
            <h1>{{ $t('support.newsFeed') }}</h1>
            <div class="close_header" @click="drawerClose()">
                <i class="fi fi-rr-cross"></i>
            </div>
        </div>
        <div class="news_list__body">
            <div v-if="user && user.is_staff" class="mb-4">
                <a-button @click="openCreate()">
                    {{ $t('support.addNews') }}
                </a-button>
            </div>
            <div v-if="empty" class="pt-4">
                <a-empty :description="$t('support.noNewNews')" />
            </div>
            <NewsCard 
                v-for="item in list.results" 
                :key="item.id"
                :data-news-id="item.id"
                :item="item" 
                :externalVote="item._vote"
                :setNewsRead="setNewsRead"
                :updateNewsVote="updateNewsVote" />
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
        updateNewsVote(id, vote) {
            if(!id || !vote || !this.list.results?.length)
                return
            const index = this.list.results.findIndex(f => f.id === id)
            if(index !== -1) {
                this.$set(this.list.results[index], '_vote', {...vote})
            }
        },
        onVoteChange(payload = {}) {
            this.updateNewsVote(payload.id, payload.vote)
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
                            page_size: 15
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
                    const { news: newsId, ...query } = this.$route.query
                    if (newsId) {
                        const foundNews = data.results.find(news => news.id === newsId)
                        if (foundNews) {
                            this.$nextTick(() => {
                                const newsElement = document.querySelector(`[data-news-id="${newsId}"]`)
                                if (newsElement) {
                                    newsElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                                    this.$router.replace({ query })
                                }
                            })
                        }
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
        eventBus.$on('support_news_vote_changed', this.onVoteChange)
        eventBus.$on('support_news_list_reload', this.onListReload)
    },
    beforeDestroy() {
        eventBus.$off('support_news_vote_changed', this.onVoteChange)
        eventBus.$off('support_news_list_reload', this.onListReload)
    }
}
</script>

<style lang="scss" scoped>
.news_list{
    display: flex;
    flex-direction: column;
    &__header{
        background: var(--blue);
        padding: 10px 15px 10px 15px;
        position: relative;
        background-image: url('../../assets/img/wiki_bg.png');
        background-position: center;
        background-repeat: no-repeat;
        background-size: cover;
        @media (min-width: 768px) {
            padding: 50px 15px 10px 15px;
        }
        .close_header{
            position: absolute;
            top: 10px;
            right: 15px;
            color: #ffffff;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &:hover{
                opacity: 0.6;
            }
            @media (min-width: 768px) {
                top: 15px;
            }
        }
        h1{
            font-size: 20px;
            margin: 0px;
            color: #ffffff;
            font-weight: bold;
            @media (min-width: 768px) {
                font-size: 28px;
            }
        }
    }
    &__body{
        flex-grow: 1;
        overflow-y: auto;
        padding: 20px 15px;
    }
}
</style>
