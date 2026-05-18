<template>
    <div class="flex items-center">
        <Status
            icon
            statusType="Статус выполнения"
            iconType="fi-rr-time-past"
            :status='record.execute_status'/>
        <Status
            v-if="record.payment_status"
            icon
            class="ml-1"
            statusType="Статус оплаты"
            extraInfo="Печать документа"
            :id="record.id"
            :statusRecord="record"
            :click="getInvoicePayment"
            iconType="fi-rr-wallet"
            :status='record.payment_status'/>
        <Status
            v-if="record.delivery_status"
            icon
            class="ml-1"
            statusType="Статус доставки"
            iconType="fi-rr-truck-side"
            :status='record.delivery_status'/>
    </div>
</template>

<script>
export default {
    components: {
        Status: () => import('@apps/Orders/components/OrdersList/Status.vue' )
    },
    props: {
        record: {
            type: Object,
            required: true
        },
        getInvoicePayment: {
            type: Function,
            required: true
        }
    }
}
</script>