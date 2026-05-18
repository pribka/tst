<template>
    <div>
        <div
            v-if="empty"
            class="mt-5">
            <a-empty :description="$t('meeting.noData')" />
        </div>
        <RequestCard
            routerKey="ticketView"
            v-for="item in list.results"
            :key="item.id"
            :page_name="page_name"
            :pageModel="pageModel"
            :item="item" />
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
        InfiniteLoading: () => import('vue-infinite-loading' ),
        RequestCard: () => import('./components/RequestCard.vue')
    },
    props: {
        page_name: {
            type: String,
            required: true
        },
        pageModel: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            orgInit: false,
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.page_name,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    sockets: {
        workflow_request_update({data}){
            if(data)
                this.upsertItem(data)
        }
    },
    methods: {
        upsertItem(data) {
            if(!data?.id) return

            const index = this.list.results.findIndex(f => f.id === data.id)
            if(index === -1) {
                this.list.results.unshift(data)
                this.empty = false
                this.list.count += 1
                return
            }

            this.$set(this.list.results, index, data)
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
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/processes/workflow_requests/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.page_name,
                            model: this.pageModel
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
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}_${this.page_name}`, () => this.listReload())
        eventBus.$on(`update_filter_${this.page_name}`, () => this.listReload())
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}_${this.page_name}`)
        eventBus.$off(`update_filter_${this.page_name}`)
    }
}
</script>
