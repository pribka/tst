<template>
    <Cart />
</template>

<script>
export default {
    name: 'HeaderCart',
    components: {
        Cart: () => import('@apps/Orders/components/Cart/Cart.vue')
    }
}
</script>