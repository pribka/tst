<template>
    <div ref="calls_tab" :class="isMobile ? '' : 'h-full flex flex-col min-h-0'">
        <component
            :is="callsComponent"
            ref="callsListWidget"
            :ticket="ticket"
            :actions="actions"
            :model="model"
            :page_name="page_name" />
    </div>
</template>

<script>
export default {
    name: 'TicketCallsTab',
    props: {
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            model: 'meetings.CallModel',
            page_name: `meetings.CallModel.Tickets_${this.ticket.id}`,
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        callsComponent() {
            return this.isMobile
                ? () => import('./Calls/List.vue')
                : () => import('./Calls/Table.vue')
        }
    }
}
</script>
