<template>
    <Cart />
</template>

<script>
export default {
    name: 'HeaderReturnCart',
    components: {
        Cart: () => import('@apps/Orders/components/Cart/ReturnCart.vue')
    }
}
</script>