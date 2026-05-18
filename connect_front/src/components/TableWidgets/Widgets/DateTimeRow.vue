<template>
    <div>
        <span>{{ cellText }}</span>
        <template v-if="isDeliveryDatePlanField">
            <span 
                v-if="deliveryDatePlan.delivery_date_plan_lte !== null ||
                    deliveryDatePlan.delivery_date_plan_gte !== null" 
                class="flex items-center">
                <a-icon type="clock-circle" />
                От {{$moment(deliveryDatePlan.delivery_date_plan_gte).format('D MMMM, HH:mm')}} <br>
                До {{$moment(deliveryDatePlan.delivery_date_plan_lte).format('D MMMM, HH:mm')}}
            </span>
        </template>
        <component 
            :is="dateWidget" 
            :date="record.created_at" 
            noColor />
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object]
        },
        record: {
            type: Object
        },
        model: {
            type: String
        },
        column: {
            type: Object
        },
    },
    computed: {
        isOrder() {
            return this.model === 'crm.GoodsOrderModel'
        },
        isAccountingReports() {
            return this.model === 'accounting_reports.AccountingReportModel'
        },
        isDeliveryDatePlanField() {
            return this.column?.key === 'delivery_date_plan'
        },
        deliveryDatePlan() {
            return this.record.delivery_date_plan
        },
        cellText() {
            if(this.isOrder)
                if(['delivery_date_plan', 'created_at'].includes(this.column?.key))
                    return ''
                else if(this.column?.key === 'pay_date_plan')
                    return this.text ? this.$moment(this.text).format('DD.MM.YYYY') : ''
            
            if(this.isAccountingReports) {
                return this.text ? this.$moment(this.text).format('DD.MM.YYYY') : ''
            }
            if (this.model === 'meetings.PlannedMeetingModel') {
                return this.text ? this.$moment(this.text).format('DD.MM.YYYY HH:mm') : ''
            }
            if (this.column.format) {
                return this.text ? this.$moment(this.text).format(this.$t('date_format')) : ''
            }

            return this.text ? this.$moment(this.text).format('DD.MM.YYYY HH:mm') : ''
        },
        dateWidget() {
            if(this.isOrder)
                if(this.column?.key === 'created_at')
                    return () => import('@apps/Orders/components/OrdersList/DateWidget.vue')
            return null
        }
    }
}
</script>