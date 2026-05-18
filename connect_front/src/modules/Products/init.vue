<template>
    <component :is="productShowDrawerAsync" v-if="$route.query.viewGoods" />
</template>

<script>
import store from "./store/index"
export default {
    data() {
        return {
            productShowDrawerAsync: null,
        }
    },
    watch: {
        '$route.query.viewGoods': {
            immediate: true,
            handler(v) {
                if (v && !this.productShowDrawerAsync)
                    this.productShowDrawerAsync = () => import(/* webpackChunkName: "product-show-drawer" */ "./Detail.vue")
            }
        }
    },
    created() {
        if(!this.$store.hasModule('products'))
            this.$store.registerModule("products", store)
    }
}
</script>