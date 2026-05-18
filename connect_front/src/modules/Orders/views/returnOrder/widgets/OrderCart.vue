<template>
    <div 
        class="form" 
        :key="reload">
        <div class="product_list">
            <template v-if="!isMobile">
                <div class="grid header_labels gap-3">
                    <div>№</div>
                    <div class="text-center">Артикул</div>
                    <div class="text-center">Наименование</div>
                    <div class="text-center">Цена</div>
                    <div class="text-center">Количество</div>
                    <div class="text-center">Сумма НДС</div>
                    <div class="text-right">
                        <span class="pr-4">
                            Сумма
                        </span>
                    </div>
                </div>
            </template>
            <component
                :is="cardWidget" 
                v-for="item in cartList.results" 
                :key="item.id" 
                :item="item" />
        </div>
        <InfiniteLoading 
            :distance="400"
            :identifier="currentContract"
            @infinite="getOrderList">
            <div 
                slot="spinner" 
                class="flex justify-center w-full">
                <a-spin class="mt-4" />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </InfiniteLoading>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import InfiniteLoading from "vue-infinite-loading"
export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        reload: {
            type: Boolean,
            default: false
        }
    },
    components: {
        InfiniteLoading
    },
    computed: {
        ...mapState({
            cartList: state => state.return.orderList,
            currentContract: state => state.return.currentContract
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        cardWidget() {
            if(this.isMobile)
                return () => import('../../../components/OrderProductItemMobile.vue')
            return () => import('../../../components/OrderProductItem.vue')
        },


    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        async getOrderList($state = null) {
            if(this.cartList.next && !this.loading) {
                try {
                    this.loading = true
                    const data = await this.$store.dispatch('return/getOrderList')
                    if(data?.next) {
                        if($state)
                            $state.loaded()
                    } else {
                        if($state)
                            $state.complete()
                    }
                } catch(e) {
                    console.log(e)
                    this.loading = false
                    if($state)
                        $state.complete()
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.header_labels{
    grid-template-columns: 40px 100px 1fr 120px 100px 100px 120px;
    padding: 10px 0;
    margin-bottom: 15px;
    background: #fff;
    border-bottom: 1px solid var(--border2);
    font-weight: 300;
    color: #000;
    position: sticky;
    top: 0px;
    z-index: 10;
}
</style>