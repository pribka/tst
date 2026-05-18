<template>
    <Kanban 
        :useScrollDummy="false" 
        :page_name="page_name"
        :queryParams="{
            customer_card: ticket.customer_card.id,
            exclude: ticket.id
        }" />
</template>

<script>
export default {
    components: {
        Kanban: () => import('../../../Kanban/index.vue')
    },
    props: {
        page_name: {
            type: String,
            default: ""
        },
        model: {
            type: String,
            default: ""
        },
        actions: {
            type: Object,
            required: true
        },
        ticket: {
            type: Object,
            required: true
        }
    }
}
</script>