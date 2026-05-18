<template>
    <History 
        :related_object="ticket.id" 
        filterPrefix="ticket"
        injectContainer
        modelLabel="help_desk.HelpDeskTicketModel" />
</template>

<script>
export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
    },
    components: {
        History: () => import('@apps/History/index.vue')
    }
}
</script>