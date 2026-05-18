<template>
    <Accounting :event="event" :actions="actions" />
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    components: {
        Accounting: () => import('../../Accounting/index.vue')
    }
}
</script>