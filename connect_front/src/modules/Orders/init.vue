<template>
    <div>
        <component :is="orderShowDrawerAsync" v-if="$route.query.order" isProject />

        <OrderEditDrawer />
    </div>
</template>

<script>
import cart from "./store/cart/index.js"
import returnStore from "./store/return/index.js"
import './assets/scss/cart.scss'
export default {
    components: { 
        OrderEditDrawer: () => import("./components/OrdersList/OrderEditDrawer.vue")
    },
    data() {
        return {
            orderShowDrawerAsync: null,
        }
    },
    created() {
        if (!this.$store.hasModule("orders"))
            this.$store.registerModule("orders", cart)
        if (!this.$store.hasModule("return"))
            this.$store.registerModule("return", returnStore)
        this.getCartCount()
        this.getReturnCartCount()
    },
    watch: {
        '$route.query.order': {
            immediate: true,
            handler(v) {
                if (v && !this.orderShowDrawerAsync)
                    this.orderShowDrawerAsync = () => import(/* webpackChunkName: "order-show-drawer" */ "./components/OrdersList/OrderShowDrawer")
            }
        }
    },
    methods: {
        async getCartCount() {
            try {
                await this.$store.dispatch("orders/getCartCount")
            }
            catch (e) {
                console.log(e)
            }
        },
        async getReturnCartCount() {
            try {
                await this.$store.dispatch("return/getCartCount")
            }
            catch (e) {
                console.log(e)
            }
        }
    }
}
</script>
