<template>
    <div class="order_block">
        <h2 v-if="showLabel">Способ оплаты</h2>
        <div class="pay_method_info">
            <div 
                v-if="order.pay_type" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Форма оплаты:
                </div>
                <div>
                    {{ order.pay_type.name }}
                </div>
            </div>
            <div 
                v-if="order.pay_date_plan" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Дата оплаты:
                </div>
                <div>
                    {{ $moment(order.pay_date_plan).format('DD.MM.YYYY') }}
                </div>
            </div>
            <div 
                v-if="order.amount_paid && order.amount_paid !== '0.00'" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Остаток по оплате:
                </div>
                <div>
                    {{ order.amount_paid }}
                </div>
            </div>
            <div 
                v-if="order.cash_pay_recipient" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Получатель:
                </div>
                <div  
                    ref="cash_pay_recipient">
                    <Profiler
                        :user="order.cash_pay_recipient"
                        initStatus
                        :getPopupContainer="() => $refs['cash_pay_recipient']"
                        :avatarSize="22" />
                </div>
            </div>
            <div 
                v-if="order.cash_pay_type" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Способ получения:
                </div>
                <div>
                    {{ order.cash_pay_type.name }}
                </div>
            </div>

            <a-spin :spinning="payLoader">
                <div 
                    v-if="orderPaymentForm" 
                    class="payment_title">
                    <span class="font-light">Форма оплаты:</span> 
                    {{ orderPaymentForm.name }}
                </div>
                <div 
                    v-if="orderStages && orderStages.length" 
                    class="stages mt-3">
                    <div 
                        v-for="item in orderStages" 
                        :key="item.id" 
                        class="stages_item">
                        <div 
                            v-if="item.payment_option && item.payment_option.name" 
                            class="name font-semibold mb-1">
                            {{ item.payment_option.name }}
                        </div>
                        <div 
                            v-if="item.duration" 
                            class="duration mb-1">
                            <span class="font-light">Срок оплаты:</span> {{ payDuration(item.duration) }}
                        </div>
                        <div 
                            v-if="item.payment_percent" 
                            class="duration">
                            <span class="font-light">Процент оплаты:</span> {{ item.payment_percent }}%
                        </div>
                    </div>
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        orderPaymentForm: {
            type: Object,
            default: () => null
        },
        orderStages: {
            type: Array,
            default: () => []
        },
        payLoader: {
            type: Boolean,
            default: false
        },
        order: {
            type: Object,
            required: true
        },
        showLabel: {
            type: Boolean,
            default: true
        },
        isMobile: {
            type: Boolean,
            default: true
        }
    }
}
</script>

<style lang="scss" scoped>
.payment_title{
    font-size: 16px;
}
.pay_method_info{
    background: #eff2f5;
    padding: 15px;
    border-radius: var(--borderRadius);
}
.stages{
    .stages_item{
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
    }
}
</style>