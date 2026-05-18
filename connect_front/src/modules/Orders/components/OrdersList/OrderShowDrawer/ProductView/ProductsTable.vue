<template>
    <div>
        <div class="grid header_labels gap-3"
             :class="order.show_nds ? 'grid-cols-[15px,1fr,100px,120px,120px,120px,130px,100px,130px]' : 'grid-cols-[15px,1fr,100px,120px,120px,120px,130px]'">
            <div>
                №
            </div>
            <div>
                <span class="pl-4">
                    Наименование
                </span>
            </div>
            <div class="text-center">Количество</div>
            <template v-if="!logisticManagerOnly">
                <div class="text-center">Цена</div>
                <template v-if="!hideDetailPrice">
                    <div class="text-center">Сумма без скидки</div>
                    <div class="text-center">Скидка</div>

                    <div v-if="order.show_nds" class="text-center">Ставка НДС</div>
                    <div v-if="order.show_nds" class="text-center">Сумма НДС</div>
                </template>
                <div class="text-right">
                    <span class="pr-4">Сумма</span>
                </div>
                <template v-if="isLogistic">
                    <div class="text-center">Отгружено</div>
                </template>
            </template>
        </div>
        <OrderProduct
            v-for="product in products.results"
            :key="product.id"
            :updateProductList="updateProductList"
            :logisticManagerOnly="logisticManagerOnly"
            :productList="products.results"
            :order="order"
            :showNDS="order.show_nds"
            :actionLoading="actionLoading"
            :isLogistic="isLogistic"
            :product="product" />
    </div>
</template>

<script>
export default {
    components: {
        OrderProduct: () => import('../../OrderProduct.vue')
    },
    props: {
        products: {
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
        hideDetailPrice() {
            return this.isLogistic
        },
        logisticManagerOnly() {
            return this.$store.state?.user?.user?.me_logistic_manager_only
        },
    }
}
</script>

<style lang="scss" scoped>
.header_labels{
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
</style>