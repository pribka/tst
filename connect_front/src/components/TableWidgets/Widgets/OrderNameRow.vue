<template>
    <OrderName :record="record" />
</template>

<script>
export default {
    components: {
        OrderName: () => import('@apps/Orders/components/OrdersList/OrderName.vue')
    },
    props: {
        record: {
            type: Object,
            required: true
        }
    }
}
</script>