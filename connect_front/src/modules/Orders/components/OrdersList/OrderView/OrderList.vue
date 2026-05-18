<template>
    <div class="order_list">
        <div 
            v-if="ordersEmpty" 
            class="pt-8">
            <a-empty>
                <template #description>
                    По данному запросу товары отсутствуют
                </template>
            </a-empty>
        </div>
        <OrderCard v-for="order in listOrders" :key="order.id" :order="order" />
        <infinite-loading
            ref="infiniteLoading"
            @infinite="getOrders"
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
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus.js'
export default {
    name: "OrderList",
    components:
    { 
        OrderCard: () => import('../OrderCard.vue'),
        InfiniteLoading
    },
    props: {
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "crm.GoodsOrderModel_list"
        },
        params: {
            type: Object,
            default: () => ({})
        },
        excludeCol: {
            type: Array,
            default: () => []
        }
    },
    data(){
        return {
            listOrders: [],
            listLoading: false,
            page: 0,
            pageSize: 15,
            model: "crm.GoodsOrderModel",
            currentOrdersCount: 0,
            ordering: null,
            infiniteId: new Date(),
            nextOrder: true
        }
    },
    computed: {
        tableScroll() {
            if(this.windowWidth > 1650)
                return false
            else
                return  1400
        },
        scroll() {
            return {
                x: this.tableScroll,
                y: 'calc(100vh - 272px)'
            }
        },
        ordersEmpty() {
            return !this.currentOrdersCount && !this.listLoading
        }
    },
    methods: {
        async getOrders($state){
            if(!this.listLoading && this.nextOrder) {
                try{
                    this.listLoading = true
                    this.page += 1
                    let {data} = await this.$http(`crm/orders/`,
                        { params: {
                            page_size: this.pageSize,
                            page: this.page,
                            page_name: this.pageName,
                            filters: this.filters,
                            ordering: this.ordering,
                            ...this.params
                        }})
                    if(data) {
                        this.currentOrdersCount = data.count
                        this.nextOrder = data.next
                    } 
                    if(data?.results?.length) {
                        data.results.forEach(row => this.hydrateCrmCustomer(row))
                        this.listOrders = this.listOrders.concat(data.results)
                    }
                    
                    if(this.nextOrder)
                        $state.loaded()
                    else 
                        $state.complete()

                } catch(e){
                    console.error(e)
                } finally{
                    this.listLoading = false
                }
            }
        },
        pageReload() {
            this.page = 0
            this.nextOrder = true
            this.listOrders = []
            if(this.$refs.infiniteLoading)
                this.$refs.infiniteLoading.stateChanger.reset();
        },
        async hydrateCrmCustomer(row) {
            const contract = row?.customer_contract
            const contractId = contract?.id || contract
            if(!contractId || row?.customer_card?.name) {
                return
            }
            try {
                const { data } = await this.$http.get(`/customer_contracts/${contractId}/`)
                if(data?.customer_cards?.length === 1) {
                    this.$set(row, 'customer_card', data.customer_cards[0])
                }
            } catch(e) {
                console.log(e)
            }
        }
    },

    mounted(){
        eventBus.$on('update_order_list', () => {
            this.pageReload()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.pageReload()
        })
        eventBus.$on('update_order_table', data => {
            if(this.listOrders?.length) {
                const index = this.listOrders.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    this.$set(this.listOrders, index, data)
                }
            }
        })
    },
    beforeDestroy(){
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off('update_order_list')
        eventBus.$off('update_order_table')
    }
}
</script>

<style scoped lang="scss">
.order_list{
    &::v-deep{
        .item {
            &:not(:last-child) {
                margin-bottom: 10px;
            }
        }
    }
}
</style>
