<template>
    <Cart />
</template>

<script>
export default {
    components: {
        Cart: () => import('@apps/Orders/components/Cart/Cart.vue')
    }
}
</script>