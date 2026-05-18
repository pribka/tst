<template>
    <Kanban 
        :useScrollDummy="false" 
        :page_name="page_name"
        :queryParams="{
            customer_card: client.id
        }" />
</template>

<script>
export default {
    components: {
        Kanban: () => import('@apps/HelpDesk/components/Tickets/Kanban/index.vue')
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
        client: {
            type: Object,
            required: true
        }
    }
}
</script>