<template>
    <div class="products order_block">
        <h2 v-if="showTitle">Содержимое заказа</h2>
        <div class="product_list">
            <template v-if="productsEmpty">
                <a-empty>
                    <span slot="description">
                        В заказе отсутствуют товары
                    </span>
                </a-empty>
            </template>
            <template v-else>
                <component 
                    :is="viewWidget"
                    :products="products"
                    :actionLoading="actionLoading"
                    :updateProductList="updateProductList"
                    :isLogistic="isLogistic"
                    :order="order" />
                <InfiniteLoading 
                    :distance="500"
                    @infinite="getProduct">
                    <div slot="spinner" >
                        <a-spin class="mt-4" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </InfiniteLoading>
            </template>
        </div>
    </div>
</template>

<script>
import InfiniteLoading from "vue-infinite-loading"
export default {
    components: {
        InfiniteLoading,
        OrderProduct: () => import('../OrderProduct.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        order: {
            type: Object,
            required: true
        },
        showTitle: {
            type: Boolean,
            default: true
        },
        isLogistic: {
            type: Boolean,
            default: false
        },
        actionLoading: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            productLoader: false,
            page: 0,
            productsEmpty: false,
            products: {
                next: true,
                results: []
            }
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewWidget() {
            if(this.isMobile)
                return () => import('./ProductView/ProductsList.vue')
            return () => import('./ProductView/ProductsTable.vue')
        }
    },
    methods: {
        clear() {
            this.page = 0
            this.productsEmpty = false
            this.products = {
                next: true,
                results: []
            }
        },
        async getProduct($state) {
            if(!this.productLoader && this.products.next) {
                try{ 
                    this.productLoader = true
                    this.page += 1
        
                    const {data} = await this.$http(`/crm/orders/${this.id}/goods/`, {
                        params: {
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data?.results?.length) {
                        this.products.next = data.next
                        this.products.results = this.products.results.concat(data.results)
                    } else
                        this.productsEmpty = true

                    if(data?.next)
                        $state.loaded()
                    else
                        $state.complete()
                }
                catch(e){
                    console.error(e)
                }
                finally{
                    this.productLoader = false
                }
            } else {
                $state.complete()
            }
        },
        updateProductList(index, data) {
            // this.products.results[1].quantity_success = 1
            this.$set(this.products.results, index, data)
        }
    }
}
</script>

<style lang="scss" scoped>
.product_list{
    .header_labels{
        grid-template-columns: 15px 1fr 100px 120px 120px 120px 130px 100px 130px;
        padding: 10px 0;
        margin-bottom: 15px;
        background: #fff;
        border-bottom: 1px solid var(--border2);
        font-weight: 300;
        color: #000;
        position: sticky;
        top: -20px;
        z-index: 10;
    }
}
</style>