<template>
    <div>
        <OrderProductMobile 
            v-for="product in products.results" 
            :key="product.id"
            :productList="products.results"
            :updateProductList="updateProductList"
            :actionLoading="actionLoading"
            :isLogistic="isLogistic"
            :order="order"
            :product="product" />
    </div>
</template>
 
<script>
export default {
    components: {
        OrderProductMobile: () => import('../../OrderProductMobile.vue')
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
    }
}
</script>

