<template>
    <div class="product_item grid gap-3"
         :class="showNDS ? 'grid-cols-[15px,1fr,100px,120px,120px,120px,130px,100px,130px]' : 'grid-cols-[15px,1fr,100px,120px,120px,120px,130px]'">
        <div class="flex items-center">
            {{product.number}}
        </div>
        <div class="flex items-start">
            <div
                v-if="goods.image"
                class="img" @click="openDetailt()">
                <div class="img_wrap">
                    <img
                        v-if="goods.image"
                        :data-src="goods.image"
                        class="lazyload"
                        :alt="goods.name" />
                    <img
                        v-else
                        :data-src="require('../../assets/noimage_product.svg')"
                        class="lazyload"
                        :alt="goods.name" />
                </div>
            </div>
            <div class="cart_info w-full">
                <div class="w-full cursor-pointer">
                    <h3 @click="openDetailt()">
                        {{ goods.name }}
                    </h3>
                    <div
                        v-if="checkStock && warehouse"
                        class="cart_warehouse">
                        Склад: {{ warehouse.name }}
                    </div>
                    <div class="article">
                        Арт: {{ goods.article_number }}
                    </div>
                </div>
            </div>
        </div>
        <div class="count flex items-center justify-center">
            {{ product.quantity }}
        </div>
        <template v-if="!logisticManagerOnly">
            <div class="price flex items-center justify-center">
                {{ price(product.price) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
            </div>
            <template v-if="!hideDetailPrice">
                <div class="price flex items-center justify-center">
                    {{ amount_no_discount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>
                <div class="price flex items-center justify-center">
                    {{ discount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>

                <div v-if="showNDS" class="flex items-center justify-center font-semibold">
                    {{ nds }}
                </div>
                <div v-if="showNDS" class="flex items-center justify-center font-semibold">
                    {{ nds_amount }}
                </div>
            </template>
            <div class="price_end flex items-center justify-end font-semibold">
                {{ amount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
            </div>

            <template v-if="isLogistic">

                <div class="flex items-center justify-center">
                    {{ product.quantity_success }}
                </div>

                <div class="flex">
                    <template v-if="product.quantity_success && Number(product.quantity_success) > 0">
                        <!-- <template v-if="product.attachments.length || product.comment.length">
                            <a-button
                                class="mb-1 ant-btn-icon-only"
                                v-tippy="{ inertia : true}"
                                content="Информация"
                                @click="openInfo(product)">
                                <i class="fi fi-rr-info"></i>
                            </a-button>
                        </template> -->
                    </template>
                    <template v-else>
                        <template v-if="order.delivery_status.code !== 'delivered'">
                            <div class="flex items-center px-4">
                                <a-spin
                                    v-if="actionLoading"
                                    size="small" />
                                <!-- <a-button
                                    class="ant-btn-icon-only"
                                    v-tippy="{ inertia : true}"
                                    content="Полная отгрузка"
                                    type="primary"
                                    ghost
                                    :loading="fullLoading && fullLoading[product.id]"
                                    @click="fullShipment(product)">
                                    <i class="fi fi-rr-boxes"></i>
                                </a-button> -->
                                <a-button
                                    v-if="orderActions && orderActions.shipment"
                                    class="ant-btn-icon-only ml-1"
                                    v-tippy="{ inertia : true}"
                                    content="Неполная отгрузка"
                                    type="danger"
                                    ghost
                                    @click="incompleteModal(product)">
                                    <i class="fi fi-rr-truck-loading"></i>
                                </a-button>
                            </div>
                        </template>
                    </template>
                </div>
            </template>

            <ProductModal
                :visibleInfo="visibleInfo"
                :afterCloseInfo="afterCloseInfo"
                :infoData="infoData"
                :closeInfoModal="closeInfoModal"
                :visible="visible"
                :incomplete="incomplete"
                :afterClose="afterClose"
                :closeFormModal="closeFormModal"
                :updateProduct="updateProduct"
                :updateProductList="updateProductList" />
        </template>

    </div>
</template>

<script>
import 'lazysizes'
import mixins from './mixins'
import { priceFormatter } from '@/utils'
import ProductModal from './ProductModal.vue'
import { mapState } from 'vuex'
export default {
    mixins: [mixins],
    props: {
        productList: {
            type: Array,
            required: true
        },
        product: {
            type: Object,
            required: true
        },
        order: {
            type: Object,
            required: true
        },
        isLogistic: {
            type: Boolean,
            default: false
        },
        updateProductList: {
            type: Function,
            default: () => {}
        },
        logisticManagerOnly: {
            type: Boolean,
            default: false
        },
        actionLoading: {
            type: Boolean,
            default: false
        },
        showNDS: {
            type: Boolean,
            default: false
        },
    },
    components: {
        ProductModal
    },
    computed: {
        ...mapState({
            orderActions: state => state.orders.orderActions
        }),
        config() {
            return this.$store.state.config.config
        },
        checkStock() {
            if(this.config?.order_setting?.check_stock)
                return true
            else
                return false
        },
        goods() {
            return this.product.goods
        },
        // price() {
        //     return priceFormatter(this.product.price)
        // },
        amount() {
            return priceFormatter(this.product.amount)
        },
        amount_no_discount() {
            return priceFormatter(this.product.amount_no_discount)
        },
        discount () {
            return priceFormatter(this.product.discount )
        },
        nds(){
            return this.product.nds || "-"
        },
        nds_amount(){
            return priceFormatter(this.product.nds_amount)
        },
        warehouse() {
            if(this.product.warehouse)
                return this.product.warehouse
            else
                return null
        },
        hideDetailPrice() {
            return this.isLogistic
        },
    },
    methods: {
        openDetailt() {
            let query = Object.assign({}, this.$route.query)

            if(!query?.viewGoods || query.viewGoods !== this.goods.id) {
                query.viewGoods = this.goods.id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>

.product_item{
    .article{
        font-size: 12px;
        margin-top: 4px;
        font-weight: 300;
        color: #999;
    }
    .cart_warehouse{
        margin-top: 5px;
        font-weight: 300;
        font-size: 14px;
    }
    h3{
        -webkit-hyphens: auto;
        -ms-hyphens: auto;
        hyphens: auto;
        font-weight: 400;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
        font-size: 14px;
        &:hover{
            color: var(--blue);
        }
    }
    .img{
        width: 60px;
        height: 60px;
        overflow: hidden;
        border-radius: 5px;
        margin-right: 15px;
        cursor: pointer;
        position: relative;
        .img_wrap{
            margin: 0;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        img{
            object-fit: contain;
            vertical-align: middle;
            -o-object-fit: contain;
            opacity: 0;
            transition: opacity 0.15s ease-in-out;
            max-height: 100%;
            &.lazyloaded{
                opacity: 1;
            }
        }
    }
}
</style>