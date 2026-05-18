<template>
    <div class="logistic_orders w-[300px] 2xl:w-[350px] relative">
        <div class="logistic_orders__header flex justify-between items-center">
            <span>
                {{ config.orders && config.orders.name ? config.orders.name : 'Список заказов' }}
            </span>
            <a-button
                v-if="config.orders && config.orders.close_button"
                type="link"
                class="ant-btn-icon-only text_current"
                @click="toggleOrderSidebar()">
                <i class="fi fi-rr-arrow-square-left"></i>
            </a-button>
        </div>
        <div class="logistic_orders_wrapper">
            <div class="pb-3 actions_wrapper">
                <div class="filter_wrapper">
                    <PageFilter
                        v-if="config.orders && config.orders.show_filter"
                        class="w-full"
                        :model="model"
                        :key="page_name"
                        size="large"
                        :excludeFields="['without_logistic_task_filter', 'is_daily_filter', 'is_daily_created_filter', 'is_daily_delivery_filter']"
                        :page_name="page_name" />
                    <a-button
                        type="link"
                        v-tippy="{ inertia : true}"
                        content="Обновить список"
                        class="ant-btn-icon-only text_current pl-1 pr-0"
                        @click="listInit()">
                        <i class="fi-rr-rotate-right flex items-center justify-center"></i>
                    </a-button>
                </div>
                <div
                    v-if="config.orders && config.orders.show_filter_isnull"
                    class="orders_check check_button mt-2">
                    <swiper
                        :options="swiperOption">
                        <swiper-slide class="slide_1">
                            <a-checkbox
                                :checked="filters['without_logistic_task_filter']"
                                @change="checkboxHandler($event, 'without_logistic_task_filter')">
                                Нераспределенные
                            </a-checkbox>
                        </swiper-slide>
                        <swiper-slide class="slide_2">
                            <a-checkbox
                                :checked="filters['is_daily_created_filter']"
                                @change="checkboxHandler($event, 'is_daily_created_filter')">
                                Сегодня создан
                            </a-checkbox>
                        </swiper-slide>
                        <swiper-slide class="slide_3">
                            <a-checkbox
                                :checked="filters['is_daily_delivery_filter']"
                                @change="checkboxHandler($event, 'is_daily_delivery_filter')">
                                Сегодня отгрузка
                            </a-checkbox>
                        </swiper-slide>
                        <div class="swiper_ar_prev swiper_ar" slot="button-prev"><i class="fi fi-rr-angle-small-left"></i></div>
                        <div class="swiper_ar_next swiper_ar" slot="button-next"><i class="fi fi-rr-angle-small-right"></i></div>
                    </swiper>
                </div>
            </div>
            <template>
                <a-checkbox-group
                    v-model="selectOrder"
                    class="w-full">
                    <div
                        v-if="orderListEmpty"
                        class="pt-3">
                        <a-empty description="Нет данных" />
                    </div>
                    <draggable
                        v-model="orderList"
                        class="list-group"
                        ghost-class="ghost"
                        draggable=".active_card"
                        :group="{ name: 'card_points', pull: true, put: false }"
                        @start="dragging = true"
                        @end="dragging = false"
                        @change="change">
                        <div
                            v-for="order in orderList"
                            :key="order.id"
                            class="order_card" :class="(!order.logistic_task && !order.warehouse?.default_warehouse && !order.delivery_date_fact && !order.pickup && order.delivery_point && order.start_delivery_point) && 'active_card'">
                            <div class="flex items-center justify-between truncate">
                                <div
                                    class="truncate cursor-pointer blue_color"
                                    @click="openOrder(order)">
                                    #{{ order.counter }}
                                </div>
                                <div class="flex items-center content-center pl-2">
                                    <Status
                                        icon
                                        statusType="Статус выполнения"
                                        iconType="fi-rr-time-past"
                                        :status='order.execute_status'/>
                                    <Status
                                        v-if="order.payment_status"
                                        icon
                                        class="ml-1"
                                        statusType="Статус оплаты"
                                        iconType="fi-rr-wallet"
                                        :status='order.payment_status'/>
                                    <Status
                                        v-if="order.delivery_status"
                                        icon
                                        class="ml-1"
                                        statusType="Статус доставки"
                                        iconType="fi-rr-truck-side"
                                        :status='order.delivery_status'/>
                                    <!--<a-checkbox
                                        v-if="!order.logistic_task"
                                        class="ml-3"
                                        :value="order.id" />-->
                                    <a-button v-if="order.logistic_task" :loading="loading" type="link" class="fi ant-btn-icon-only show_task ml-1" @click="showTask(order)">
                                        <i class="fi fi-rr-eye"></i>
                                    </a-button>
                                    <a-button v-else-if="order.logistic_task === null" :loading="loaderOW" type="link" class="fi ant-btn-icon-only show_task ml-1" @click="showPopup(order)">
                                        <i class="fi fi-rr-eye"></i>
                                    </a-button>
                                    <Actions :record="order" class="fi"/>
                                </div>
                            </div>
                            <div class="flex items-center justify-between truncate mb-1">
                                <div v-if="order.warehouse && order.warehouse.name" class="truncate gray pr-2">
                                    Склад: {{ order.warehouse.name }}
                                </div>
                            </div>
                            <div class="flex items-center justify-between gap-x-2">
                                <div class="mb-1">
                                    <div v-if="order.goods_content" class="gray pr-2">
                                        {{ order.goods_content }}
                                    </div>
                                </div>
                                <div class="mb-1">
                                    <div v-if="order.quantity" class="truncate gray pr-2">
                                        {{ order.quantity }}
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center justify-between truncate">
                                <div class="truncate">
                                    {{ order.contractor_member && order.contractor_member.name }}
                                </div>
                                <div class="pl-2">
                                    {{ priceFormatter(Number(order.amount)) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                                </div>
                            </div>
                            <div v-if="order.pickup" class="truncate mt-1 text-yellow-700">
                                Самовывоз
                            </div>
                            <template v-else>
                                <div v-if="!order.delivery_point || !order.start_delivery_point" class="text-yellow-700">
                                    <div v-if="!order.delivery_point">нет точки отгрузки</div>
                                    <div v-if="!order.start_delivery_point">нет точки загрузки</div>
                                </div>
                            </template>
                        </div>
                    </draggable>
                </a-checkbox-group>
                <infinite-loading
                    ref="infiniteLoading"
                    @infinite="getOrders"
                    v-bind:distance="10">
                    <div
                        slot="spinner"
                        class="flex items-center justify-center inf_spinner">
                        <a-spin />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </template>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import InfiniteLoading from 'vue-infinite-loading'
import draggable from "vuedraggable"
import Status from './Status.vue'
import { priceFormatter } from '@/utils'
import PageFilter from '@/components/PageFilter'
import { mapState } from 'vuex'
import Actions from './Actions.vue'
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import 'swiper/css/swiper.css'
export default {
    props: {
        toggleOrderSidebar: {
            type: Function,
            default: () => {}
        },
        changeActiveTab: {
            type: Function,
            default: () => {}
        },
        openTask: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        InfiniteLoading,
        draggable,
        Status,
        PageFilter,
        Actions,
        Swiper,
        SwiperSlide
    },
    computed: {
        ...mapState({
            config: state => state.monitor.config,
            filters: state => state.monitor.orderFilters,
            orderNext: state => state.monitor.orderNext,
            orderListEmpty: state => state.monitor.orderListEmpty,
            orderListMoved: state => state.monitor.orderListMoved,
            orderListRequest: state => state.monitor.orderListRequest,
            loading: state => state.monitor.taskListLoader,
            loaderOW: state => state.monitor.loaderOW
        }),
        orderList: {
            get() {
                return this.$store.state.monitor.orderList
            },
            set(val) {
                this.$store.commit('monitor/UPDATE_ORDER_LIST', val)
            }
        }
    },
    data() {
        return {
            swiperOption: {
                slidesPerView: 'auto',
                spaceBetween: 10,
                navigation: {
                    nextEl: '.swiper_ar_next',
                    prevEl: '.swiper_ar_prev'
                }
            },
            visible: false,
            drawerWidth: 400,
            listLoading: false,
            dragging: false,
            selectOrder: [],
            page_name: "crm.GoodsOrderModel_list_monitor",
            model: "crm.GoodsOrderModel",
            selectItem: null
        }
    },
    methods: {
        priceFormatter,
        showTask(sOrder) {
            if(this.$route?.query?.active_tab === 'couriers') {
                this.openTask(sOrder.logistic_task)
            } else {
                this.changeActiveTab(sOrder)
                eventBus.$emit('OPEN_ORDER_TASK', sOrder.logistic_task)
            }
        },
        showPopup(order) {
            if(order?.delivery_point?.id)
                eventBus.$emit('show_popup', order.delivery_point)
        },
        checkOrderRequest() {
            if(this.orderListRequest) {
                this.orderListRequest.cancel()
                this.$store.commit('monitor/SET_ORDER_LIST_REQUEST', null)
            }
        },
        change(e) {
            if(e.removed) {
                this.$store.commit('monitor/ADD_ORDER_REMOVED', {
                    ...e.removed.element,
                    oldIndex: e.removed.oldIndex
                })
            }
        },
        openOrder(order) {
            const query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== order.id) {
                query.order = order.id
                this.$router.push({query})
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                eventBus.$emit('SET_START_POSITION')
                this.selectOrder = []
            }
        },
        async getOrders($state){
            if(!this.listLoading && this.orderNext) {
                try{
                    this.listLoading = true

                    await this.$store.dispatch('monitor/getOrderList', {
                        page_name: this.page_name
                    })

                    if(this.orderNext)
                        $state.loaded()
                    else
                        $state.complete()

                } catch(e){
                    console.error(e)
                } finally{
                    this.listLoading = false
                }
            } else {
                $state.complete()
            }
        },
        checkboxHandler(e, key) {
            const value = e.target.checked

            this.$store.commit('monitor/SET_ORDERS_FILTER_BY_KEY', {
                value,
                key
            })

            eventBus.$emit(`send_include_fields_${this.page_name}`, {
                fields: {
                    without_logistic_task_filter: {
                        active: this.filters.without_logistic_task_filter ? true : false,
                        values: {
                            value: this.filters.without_logistic_task_filter
                        }
                    },
                    is_daily_created_filter: {
                        active: this.filters.is_daily_created_filter ? true : false,
                        values: {
                            value: this.filters.is_daily_created_filter
                        }
                    },
                    is_daily_delivery_filter: {
                        active: this.filters.is_daily_delivery_filter ? true : false,
                        values: {
                            value: this.filters.is_daily_delivery_filter
                        }
                    }
                },
                others: {
                    ...this.filters
                }
            })
        },
        reloadList() {
            this.$store.commit('monitor/ORDER_CLEAR')
            this.$nextTick(() => {
                if(this.$refs.infiniteLoading)
                    this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        listInit() {
            this.checkOrderRequest()
            this.reloadList()
        },
        reloadButton() {
            this.reloadList()
        }
    },
    mounted() {
        eventBus.$on('OPEN_ORDER_LIST_DRAWER', () => {
            this.visible = true
            eventBus.$emit('SET_LEFT_PADDING', this.drawerWidth)
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.checkOrderRequest()
            this.reloadList()
        })
        eventBus.$on('LOGISTIC_ORDER_RELOAD', () => {
            this.reloadList()
        })
        eventBus.$on(`filter_others_${this.page_name}`, data => {
            this.$store.commit('monitor/SET_ORDERS_FILTER', {
                pickup: data?.pickup || false,
                task_delivery_point__isnull: data?.task_delivery_point__isnull || false,
                is_daily_filter: data?.is_daily_filter || false
            })
        })
    },
    beforeDestroy() {
        eventBus.$off('OPEN_ORDER_LIST_DRAWER')
        eventBus.$off('LOGISTIC_ORDER_RELOAD')
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off(`filter_others_${this.page_name}`)
    }
}
</script>

<style lang="scss" scoped>
.show_task{
    width: 22px;
}
.logistic_orders{
    background-color: #eff2f5;
    height: 100%;
    overflow: hidden;
    .logistic_orders__header{
        height: 44px;
        background: #fff;
        border-bottom: 1px solid var(--border2);
        padding-left: 15px;
        padding-right: 15px;
        span{
            font-size: 14px;
            line-height: 1.5;
        }
    }
}
.logistic_orders_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    overflow-y: auto;
    height: calc(100% - 44px);
    .actions_wrapper{
        margin-left: -15px;
        margin-right: -15px;
        padding-left: 15px;
        padding-right: 15px;
        padding-top: 15px;
        position: sticky;
        top: 0;
        z-index: 5;
        background: rgba(239, 242, 245, 0.95);
        .filter_wrapper{
            display: flex;
            align-items: center;
        }
    }
}
.order_card{
    box-shadow: 0 1px 0 rgb(9 30 66 / 15%);
    position: relative;
    border-radius: var(--borderRadius);
    padding: 6px 12px;
    margin-bottom: 10px;
    &.active_card{
        cursor: move;
        background: #ffffff;
    }
    &:not(.active_card) {
        background: #ebebeb;
    }
    .ant-btn-icon-only{
        height: 20px;
    }
}
</style>

<style lang="scss">
.orders_check{
    .ant-checkbox-wrapper{
        margin-left: 0px!important;
    }
    .slide_1{
        width: 149px;
    }
    .slide_2{
        width: 125px;
    }
    .slide_3{
        width: 135px;
    }
    .swiper_ar{
        width: 25px;
        height: 25px;
        position: absolute;
        top: 1px;
        border-radius: 50%;
        background: #ffffff;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.8;
        &:hover{
            opacity: 1;
        }
        &.swiper-button-disabled{
            display: none;
        }
        &.swiper_ar_prev{
            left: 0;
        }
        &.swiper_ar_next{
            right: 0;
        }
    }
}
</style>