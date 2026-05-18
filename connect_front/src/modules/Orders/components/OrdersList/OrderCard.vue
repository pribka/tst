<template>
    <a-card
        class="item"
        style="border-radius: var(--borderRadius);"
        v-touch:longtap="longtapHandler"
        size="small"
        :bordered="false">
        <div class="flex items-start justify-between item_row">
            <div class="flex open_order" @click="openOrder(order.id)">
                <span class="blue_color">
                    {{ '№' + order.counter}}
                </span>
            </div>
            <div class="flex">
                <span class="mr-2">
                    на сумму
                </span>
                <span class="font-semibold">
                    {{ priceFormatter(Number(order.amount)) }} 
                    <template v-if="order.currency">{{ order.currency.icon }}</template>
                </span>
            </div>
        </div>
        <div class="flex items-start justify-between item_row">
            <div class="flex">
                <span>
                    {{ order.customer_contract ? 'CRM-клиент' : 'Клиент' }}
                </span>
            </div>
            <div class="flex">
                <span class="font-semibold">
                    {{ orderCustomerName }}
                </span>
            </div>
        </div>
        <!--<div class="flex items-start justify-between item_row">
                <div class="flex">
                    <span class="green_text">
                        {{order.operation_type.name}}
                    </span>
                </div>
                <div class="flex">
                    <span>
                        <DateWidget :date="order.created_at" noColor/>
                    </span>
                </div>
            </div>-->
        <div class="flex items-center justify-between item_row">
            <div class="flex">
                <span>
                    <Status :status='order.execute_status'/>
                </span>
            </div>
            <div class="flex">
                <span>
                    <Actions :ref="`order_mobile_act_${order.id}`" :record="order" :openOrder="openOrder" />
                </span>
            </div>
        </div>
    </a-card>
</template>

<script>
import Status from './Status.vue'
import Actions from './Actions.vue'
import { priceFormatter } from '@/utils'
export default {
    components: {
        Status,
        Actions
    },
    props: {
        order: {
            type: Object,
            required: true
        }
    },
    computed: {
        orderCustomerName() {
            return this.order?.customer_card?.name || this.order?.contractor?.name || ''
        }
    },
    methods: {
        priceFormatter,
        longtapHandler() {
            // console.log(this.$refs[`order_mobile_act_${this.order.id}`].$refs['order_menu'].openDrawer())
            this.$refs[`order_mobile_act_${this.order.id}`].$refs['order_menu'].openDrawer()
        },
        openOrder(id){
            let query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== id) {
                query.order = id
                this.$router.push({query})
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.item{
    -webkit-user-select: none; 
    -khtml-user-select: none; 
    -moz-user-select: none; 
    -ms-user-select: none; 
    user-select: none;
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
    .item_row {
        &:not(:last-child) {
            margin-bottom: 5px;
        }
    }
    .open_order {
        cursor: pointer;
    }

    .green_text {
        color: var(--green)
    }
}
</style>
