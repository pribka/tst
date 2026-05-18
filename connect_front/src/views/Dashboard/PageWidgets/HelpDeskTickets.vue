<template>
    <HelpDeskTickets />
</template>

<script>
export default {
    components: {
        HelpDeskTickets: () => import('@apps/HelpDesk/views/Tickets/indexMobile.vue')
    }
}
</script>