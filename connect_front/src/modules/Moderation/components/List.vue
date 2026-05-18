<template>
    <div class="moderate_list">
        <div 
            v-if="empty" 
            class="mt-5">
            <a-empty description="Нет данных" />
        </div>
        <Card v-for="item in list.results" :key="item.id" :item="item" />
        <infinite-loading 
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Card: () => import('./Card.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    data() {
        return {
            pageName: 'catalogs.ContractorProfileRequestModel',
            pageModel: 'catalogs.ContractorProfileRequestModel',
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.pageName,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/catalogs/profile_requests/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.pageName
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }  
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['list_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.listReload()
        })
        eventBus.$on('update_moderation_list', () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`)
        eventBus.$off('update_moderation_list')
    }
}
</script>

<style lang="scss" scoped>
.moderate_list{
    &::v-deep{
        .card{
            margin-bottom: 15px;
        }
    }
}
</style>