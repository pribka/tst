<template>
    <a-card
        class="item"
        :key="product.id"
        style="border-radius: var(--borderRadius);"
        size="small"
        :bordered="false">
        <div class="flex items-start justify-between item_row cursor-pointer"
             @click="openDetailt()">
            <div class="flex open_order truncate">
                <span>
                    {{ '№' + product.number}}
                </span>
                <div class="cart_info w-full ml-2 truncate">
                    <div class="w-full">
                        <h3 class="truncate">
                            {{ goods.name }}
                        </h3>
                        <div 
                            v-if="checkStock && warehouse" 
                            class="cart_warehouse truncate">
                            Склад: {{ warehouse.name }}
                        </div>
                        <div class="article truncate">
                            Арт: {{ goods.article_number }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="flex items-start justify-between item_row">
            <div class="font-medium">
                Количество
            </div>
            <div>
                {{ product.quantity }}
            </div>
        </div>
        <div class="flex items-start justify-between item_row">
            <div class="font-medium">
                Цена
            </div>
            <div>
                {{ price(product.price) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
            </div>
        </div>
        <template v-if="!hideDetailPrice">
            <div class="flex items-start justify-between item_row">
                <div class="font-medium">
                    Сумма без скидки
                </div>
                <div>
                    {{ amount_no_discount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>
            </div>
            <div class="flex items-start justify-between item_row">
                <div class="font-medium">
                    Скидка
                </div>
                <div>
                    {{ discount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>
            </div>
            <div class="flex items-start justify-between item_row">
                <div class="font-medium">
                    Ставка НДС 
                </div>
                <div>
                    {{ nds }} 
                </div>
            </div>
            <div class="flex items-start justify-between item_row">
                <div class="font-medium">
                    Сумма НДС  
                </div>
                <div>
                    {{ nds_amount }}  
                </div>
            </div>
        </template>
        <div class="flex items-start justify-between item_row">
            <div class="font-medium">
                Сумма 
            </div>
            <div>
                {{ amount }} <template v-if="order.currency">{{ order.currency.icon }}</template>
            </div>
        </div>
        <template v-if="isLogistic">
            <div class="flex items-center justify-between">
                <div class="font-medium">
                    Отгружено
                </div>
                <div>
                    {{ product.quantity_success }}
                </div>
            </div>
            <div class="mt-2">
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
                        <div>
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
                                v-if="orderActions"
                                block
                                v-tippy="{ inertia : true}"
                                content="Неполная отгрузка"
                                type="danger"
                                ghost
                                @click="incompleteModal(product)">
                                Неполная отгрузка
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
    </a-card>
</template>

<script>
import 'lazysizes'
import { priceFormatter } from '@/utils'
import ProductModal from './ProductModal.vue'
import mixins from './mixins'
import { mapState } from 'vuex'
export default {
    mixins: [mixins],
    components: {
        ProductModal
    },
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
        actionLoading: {
            type: Boolean,
            default: false
        }
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
        }
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


.item {
    &:not(:last-child) {
        margin-bottom: 10px;
    }
    .article{
        margin-top: 2px;
        font-size: 12px;
        font-weight: 300;
        color: #999;
    }
    .cart_warehouse{
        margin-top: 2px;
        font-weight: 300;
        font-size: 14px;
    }
    h3{
        &:hover{
            color: var(--blue);
        }
    }
}
.item_row {
    &:not(:last-child) {
        margin-bottom: 5px;
    }
}
</style>