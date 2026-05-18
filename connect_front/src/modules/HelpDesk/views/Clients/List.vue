<template>
    <div>
        <div class="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <ClientCard 
                v-for="client in list.results" 
                :key="client.id" 
                :client="client" />
        </div>
        <a-empty v-if="empty" description="Нет данных" />
        <infinite-loading 
            @infinite="getList"
            v-bind:distance="50"
            ref="client_infinity">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner mt-3">
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
        InfiniteLoading: () => import('vue-infinite-loading'),
        ClientCard: () => import('../../components/ClientCard.vue')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page: this.page,
                        page_size: 12,
                        page_name: this.initPageName
                    }
                    const { data } = await this.$http.get('/help_desk/customer_cards/', { params })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }
                    
                    if(data.results?.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }

                    if (!data.next) {
                        $state.complete()
                    } else {
                        $state.loaded()
                    }
                } catch (error) {
                    this.$message.error(this.$t("Error") )
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        listReload() {
            this.page = 0
            this.empty = false
            this.list = {
                next: true,
                count: 0,
                results: []
            }
            this.$nextTick(() => {
                this.$refs['client_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.initPageModel}`, () => {
            this.listReload()
        })
        eventBus.$on(`update_filter_${this.initPageModel}_${this.initPageName}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.initPageModel}`)
        eventBus.$off(`update_filter_${this.initPageModel}_${this.initPageName}`)
    }
}
</script>