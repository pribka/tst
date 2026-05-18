<template>
    <div 
        class="cursor-pointer reply_message truncate w-full mt-2 mb-2 pt-1 lg:pt-3 pb-1 lg:pb-3 pr-2" 
        @click="openOrder()">
        <div class="label truncate mb-2">
            <template v-if="order.operation_type && order.operation_type.code == '40'">
                {{ $t('chat.order_message', { counter: order.counter, created_at: $moment(order.created_at).format('DD.MM.YYYY'), amount: priceFormatter(order.amount) }) }}
                <template v-if="order.currency">{{ order.currency.icon }}</template>
            </template>
            <template v-if="order.operation_type && order.operation_type.code == '20'">
                {{ $t('chat.commercial_proposal_message', { counter: order.counter, created_at: $moment(order.created_at).format('DD.MM.YYYY'), amount: priceFormatter(order.amount) }) }}
                <template v-if="order.currency">{{ order.currency.icon }}</template>
            </template>
        </div>
        <div class="order_rows">
            <div 
                v-if="order.contractor" 
                class="row">
                {{ $t('chat.client') }}: {{order.contractor.name}}
            </div>
            <div 
                v-if="order.contract" 
                class="row">
                {{ $t('chat.contract') }}: {{order.contract.name}}
            </div>
            <div class="row">
                {{ $t('chat.created') }}: {{$moment(order.created_at).format('DD.MM.YYYY')}}
            </div>
            <div 
                v-if="order.execute_status" 
                class="row">
                {{ $t('chat.status') }}: {{order.execute_status.name}}
            </div>
        </div>
    </div>
</template>

<script>
import { priceFormatter } from '@/utils'
export default {
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    computed: {
        order() {
            return this.messageItem.share
        }
    },
    methods: {
        priceFormatter,
        openOrder() {
            let query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== this.messageItem.share.id) {
                query.order = this.messageItem.share.id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.order_rows{
    .row{
        &:not(:last-child){
            margin-bottom: 8px;
        }
    }
}
</style>