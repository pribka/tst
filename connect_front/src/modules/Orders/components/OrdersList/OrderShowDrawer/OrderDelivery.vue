<template>
    <div class="order_block">
        <h2 v-if="showLabel">Доставка</h2>
        <div class="delivery_info">
            <div 
                v-if="order.delivery_point" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Адрес доставки:
                </div>
                <div>
                    {{ order.delivery_point.name }}
                </div>
            </div>
            <div 
                v-if="order.delivery_date_plan && order.delivery_date_plan.delivery_date_plan_gte || order.delivery_date_plan && order.delivery_date_plan.delivery_date_plan_lte" 
                class="stages_item mb-3">
                <div class="name font-light mb-1">
                    Дата и время доставки:
                </div>
                <div>
                    {{ order.delivery_date_plan.delivery_date_plan_gte && $moment(order.delivery_date_plan.delivery_date_plan_gte).format('DD.MM.YYYY HH.ss') }}
                    {{ order.delivery_date_plan.delivery_date_plan_lte && `- ${$moment(order.delivery_date_plan.delivery_date_plan_lte).format('DD.MM.YYYY HH.ss')}` }}
                </div>
            </div>
            <div v-if="order.delivery_purpose && order.delivery_purpose.purpose" class="stages_item">
                <div class="name font-light mb-1">
                    Назначение доставки:
                </div>
                <div>
                    {{ order.delivery_purpose.purpose }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        order: {
            type: Object,
            required: true
        },
        showLabel: {
            type: Boolean,
            default: true
        }
    }
}
</script>

<style lang="scss" scoped>
.delivery_info{
    background: #eff2f5;
    padding: 15px;
    border-radius: var(--borderRadius);
}
</style>