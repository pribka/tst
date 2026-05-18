<template>
    <div
        class="h-full flex flex-col"
        ref="wrapRef">
        <UniversalTable 
            :model="model"
            class="flex-grow"
            :pageName="page_name"
            tableType="helpdesk_tickets"
            :params="{
                customer_card: ticket.customer_card.id,
                exclude: ticket.id
            }"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
            :endpoint="endpoint" />
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
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
    },
    data() {
        return {
            endpoint: '/help_desk/tickets/'
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.wrapRef
        }
    }
}
</script>