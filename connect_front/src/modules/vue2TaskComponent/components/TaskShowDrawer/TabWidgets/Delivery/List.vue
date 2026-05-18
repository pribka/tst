<template>
    <div class="points_list pt-3">
        <div v-if="paymentInfoList.length" class="payment-info mb-5">
            <div class="font-semibold mb-1">{{ $t('task.delivery.paid_suppliers') }}</div>
            <div v-for="(rec, index) in paymentInfoList" :key=index class="ml-1">
                {{ rec.name }} - {{ rec.amount_paid }}
            </div>
        </div>
        <div v-else class="text-center">
            <a-spin :spinning="paymentInfoLoader" size="small" />
        </div>
        <a-timeline>
            <a-timeline-item 
                v-for="(item, index) in waypoints" 
                :key="item.id"
                :color="pointColor(index, item)">
                <template 
                    v-if="index > 0 && deliveryTime(item, 'fact') && deliveryTime(item, 'fact') !== 'Invalid date'"
                    slot="dot">
                    <a-icon 
                        type="check-circle"
                        style="color: #52c41a;" />
                </template>
                <div>
                    <div class="font-semibold mb-1">
                        <span 
                            v-if="index > 0" 
                            class="cursor-pointer"
                            @click="showMap(item)">
                            {{ pointLabel(index, item) }} 
                        </span>
                        <span v-else>
                            {{ pointLabel(index, item) }} 
                        </span>
                    </div>
                    <div>
                        <span>{{ $t('task.delivery.address') }}:</span> {{ item.name }}
                    </div>
                    <template v-if="!item.is_start">
                        <div 
                            v-if="pointDesc(item) && pointDesc(item).length" 
                            class="mt-1 points_list_contact">
                            <div>
                                <div 
                                    v-for="elem in pointDesc(item)" :key="elem.id"
                                    class="">
                                    <div
                                        v-for="order in elem.orders" 
                                        :key="order.id"
                                        class="client_item cursor-pointer" @click="openOrder(order.id)">
                                        <div class="list_item">
                                            {{ $t('task.delivery.order') }}: {{ order.counter }}
                                        </div>
                                        <div class="list_item">
                                            {{ $t('task.delivery.client') }}: {{ order.contractor.name }}
                                        </div>
                                        <div 
                                            v-if="order.contractor.phone" 
                                            class="list_item">
                                            {{ $t('task.delivery.phone') }}: <a :href="`tel:${order.contractor.phone}`">{{ order.contractor.phone }}</a>
                                        </div> 
                                        <div 
                                            v-if="order.contractor.email" 
                                            sclass="list_item">
                                            {{ $t('task.delivery.email') }}: {{ order.contractor.email }}
                                        </div>  
                                        <div 
                                            v-if="(order.delivery_date_plan?.delivery_date_plan_gte || order.delivery_date_plan?.delivery_date_plan_lte)" 
                                            class="delivery_time mt-1">
                                            <div class="label">
                                                {{ $t('task.delivery.delivery_date_and_time') }}:
                                            </div>
                                            <div class="flex">
                                                {{ order.delivery_date_plan.delivery_date_plan_gte && $moment(order.delivery_date_plan.delivery_date_plan_gte).format('DD.MM.YYYY HH:mm') }} - 
                                                {{ order.delivery_date_plan.delivery_date_plan_lte && ` ${$moment(order.delivery_date_plan.delivery_date_plan_lte).format('DD.MM.YYYY HH:mm')}` }}
                                            </div>
                                        </div>
                                        <div 
                                            v-if="order.delivery_date_fact" 
                                            class="delivery_time mt-1">
                                            <div class="label">
                                                {{ $t('task.delivery.fact_delivery_date') }}:
                                            </div>
                                            <div class="flex">
                                                {{ $moment(order.delivery_date_fact).format('DD.MM.YYYY HH:mm') }}
                                            </div>
                                        </div>
                                        <div v-if="(order.delivery_status.code === 'delivered' || order.delivery_status.code === 'partially_delivered')" class="mt-1">
                                            <a-tag :color="order.delivery_status.color">
                                                {{ order.delivery_status.name }}
                                            </a-tag>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <div 
                            v-if="pointDesc(item) && pointDesc(item).length" 
                            class="mt-1 points_list_contact">
                            <div>
                                <div 
                                    v-for="elem in pointDesc(item)" :key="elem.id" 
                                    class="">
                                    <div
                                        v-if="user.can_set_pay_sum" 
                                        class="list_item flex">
                                        {{ $t('task.delivery.pay') }}:
                                        <a-spin :spinning="needAmountPaySpinning">
                                            <a-input-number
                                                v-model="elem.need_amount_pay"
                                                class="ml-1"
                                                size="small"
                                                :min="0"
                                                :precision=2
                                                :show-button="false"
                                                :parser="countParser"
                                                @pressEnter="setValue(elem, elem.orders[0])"
                                                @blur="setValue(elem, elem.orders[0])" />
                                        </a-spin>
                                    </div>
                                    <div 
                                        v-if="user.is_driver"
                                        class="list_item flex">
                                        {{ $t('task.delivery.pay') }}: {{ elem.need_amount_pay }}
                                    </div>
                                    <div
                                        v-for="order in elem.orders" 
                                        :key="order.id"
                                        class="client_item  cursor-pointer mt-1" @click="openOrder(order.id)">
                                        <div class="list_item">
                                            {{ $t('task.delivery.order') }}: {{ order.counter }}
                                        </div>
                                        <div class="list_item">
                                            {{ $t('task.delivery.client') }}: {{ order.contractor.name }}
                                        </div>
                                        <div 
                                            v-if="order.contractor.phone" 
                                            class="list_item">
                                            {{ $t('task.delivery.phone') }}: <a :href="`tel:${order.contractor.phone}`">{{ order.contractor.phone }}</a>
                                        </div>
                                        
                                        <div v-if="(order.delivery_status.code === 'delivered' || order.delivery_status.code === 'partially_delivered')" class="mt-1">
                                            <a-tag :color="order.delivery_status.color">
                                                {{ order.delivery_status.name }}
                                            </a-tag>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </a-timeline-item>
        </a-timeline>

    </div>
</template>

<script>
import { uniqBy } from 'lodash'
import {mapState} from 'vuex'
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        deliveryPoints: {
            type: Array,
            required: true
        },
        waypoints: {
            type: Array,
            default: () => []
        },
        showMap: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            activeOrder: null,
            toPay: 0,
            needAmountPaySpinning: false,
            paymentInfoLoader: false,
            paymentInfoList: []
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    mounted() {
        this.getPaymentInfo()
    },
    methods: {
        async getPaymentInfo() {
            try {
                this.paymentInfoLoader = true

                const { data } = await this.$http.get(`tasks/${this.task.id}/payment_to_warehouses/`)

                if(data) {
                    this.paymentInfoList = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.paymentInfoLoader = false
            }

        },
        countParser(value) {
            value = value.replace(/[^0-9.,]/g, "")
            value = value.replace(',', '.')
            const integerPart = value.toString().split('.')[0] || '0'
            const decimalPart = value.toString().split('.')[1] || ''
            if (decimalPart.length > 2)
                return `${integerPart}.${decimalPart.slice(0, 2)}`
            return value
        },
        async setValue(point, order) {
            try {
                this.needAmountPaySpinning = true
                const { data } = await this.$http.put(`/tasks/delivery_points/${point.id}/need_amount_pay/`, {
                    "need_amount_pay": +point.need_amount_pay
                })
                if(data) {
                    this.$message.info(`${this.$t('task.delivery.order')} ${order.counter} ${this.$t('task.delivery.updated')}`)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.needAmountPaySpinning = false
            }
        },
        deliveryTime(point, type = 'plan') {
            if(this.task.date_start_plan) {
                let time = type === 'plan' ? this.$moment(this.task.date_start_plan) : this.$moment(this.task.date_start_fact)
                const index = this.waypoints.findIndex(f => f.id === point.id)

                if(index !== -1) {
                    for (let i = 0; i <= index; i++) {
                        if(i > 0) {
                            if(this.waypoints[i].delivery_date)
                                time = this.$moment(this.waypoints[i].delivery_date).add(this.waypoints[i].duration, 'minutes')
                            else
                                time = time.add(this.waypoints[i].duration, 'minutes')
                        }
                    }

                    return this.$moment(time).format('HH:mm')
                } else
                    return null
            } else
                return null
        },
        pointLabel(index, item) {
            if(item.is_start) {
                return this.$t('task.delivery.warehouseLoading')
            } else {
                return this.$t('task.delivery.deliveryPoint')
            }
        },
        pointColor(index, item) {
            const checkColor = (index, delivered) => {
                switch(index) {
                case 0:
                    return '#a02de5'
                default:
                    if(delivered) {
                        return '#54d91c'
                    } else {
                        return '#1d65c0'
                    }
                }
            }

            let delivered = false

            if(index > 0 && item.orders?.length) {
                const filterd = item.orders.filter(f => f.delivery_status.code === 'delivered')
                if(filterd?.length === item.orders.length)
                    delivered = true
            }

            return checkColor(index, delivered)
        },
        pointDesc(point) {
            const filter = this.deliveryPoints.filter(f => f.id === point.id)
            return filter?.length ? filter : ''
        },
        ordersDesc(orders) {
            const uniq = uniqBy(orders, order => order.contractor.id)
            return uniq?.length ? uniq : ''
        },

        openOrder(id){
            let query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== id) {
                query.order = id
                query.logistic = true
                this.$router.push({query})
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.payment-info{
    h5{
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
}
.points_list{
    .item{
        &:not(:last-child){
            border-bottom: 1px solid var(--borderColor);
            margin-bottom: 10px;
            padding-bottom: 10px;
        }
    }
    .points_list_contact{
        display: flex;
        .client_item{
            background: #fafafa;
            padding: 10px;
            border-radius: var(--borderRadius);
            box-shadow: 0 1px 0 0 #dce1e6,0 0 0 1px #e7e8ec;
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
        .list_item{
            &:not(:last-child){
                margin-bottom: 3px;
            }
        }
    }
}
</style>