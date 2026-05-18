<template>
    <ModuleWrapper
        v-if="isSalesOrders"
        pageTitle="Заказы"
        :bodyOHidden="true"
        :bodyPadding="false">
        <template v-slot:h_right>
            <a-button
                class="mr-2"
                :loading="loading"
                @click="loadOrders">
                Обновить
            </a-button>
            <a-button
                type="primary"
                flaticon
                icon="fi-rr-plus-small"
                @click="openCreateOrder()">
                Заказ
            </a-button>
        </template>

        <div class="sales_orders">
            <aside class="sales_orders__aside">
                <section class="sales_orders_panel sales_orders_panel--head" data-guide-id="sales-orders-flow">
                    <div class="sales_orders_panel__caption">Заказы</div>
                    <div class="sales_orders_panel__subcaption">Из интересов</div>
                </section>

                <section class="sales_orders_panel">
                    <div class="sales_orders_panel__title">Выполнение</div>
                    <button
                        v-for="item in executionFilters"
                        :key="item.key"
                        type="button"
                        class="sales_orders_filter"
                        :class="{ 'sales_orders_filter--active': executionFilter === item.key }"
                        @click="executionFilter = item.key">
                        <span>
                            <i class="fi" :class="item.icon" />
                            {{ item.sideTitle || item.title }}
                        </span>
                        <b>{{ countByFilter('execution', item.key) }}</b>
                    </button>
                </section>

                <section class="sales_orders_panel" data-guide-id="sales-orders-rules">
                    <div class="sales_orders_panel__title">Отгрузка</div>
                    <button
                        v-for="item in deliveryFilters"
                        :key="item.key"
                        type="button"
                        class="sales_orders_filter"
                        :class="{ 'sales_orders_filter--active': deliveryFilter === item.key }"
                        @click="deliveryFilter = item.key">
                        <span>
                            <i class="fi" :class="item.icon" />
                            {{ item.sideTitle || item.title }}
                        </span>
                        <b>{{ countByFilter('delivery', item.key) }}</b>
                    </button>
                </section>

                <section class="sales_orders_panel">
                    <div class="sales_orders_panel__title">Оплата</div>
                    <button
                        v-for="item in paymentFilters"
                        :key="item.key"
                        type="button"
                        class="sales_orders_filter"
                        :class="{ 'sales_orders_filter--active': paymentFilter === item.key }"
                        @click="paymentFilter = item.key">
                        <span>
                            <i class="fi" :class="item.icon" />
                            {{ item.sideTitle || item.title }}
                        </span>
                        <b>{{ countByFilter('payment', item.key) }}</b>
                    </button>
                </section>
            </aside>

            <main class="sales_orders__main" data-guide-id="sales-orders-list">
                <div class="sales_orders__head">
                    <div>
                        <h2>Заказы</h2>
                        <p>CRM-заказы по интересам и договорам: клиент, сумма, оплата и отгрузка в одной строке</p>
                    </div>
                    <button
                        type="button"
                        class="sales_orders_head_action"
                        @click="goTo('sales-interest')">
                        К интересам
                    </button>
                </div>

                <div class="sales_orders_toolbar">
                    <label class="sales_orders_search">
                        <i class="fi fi-rr-search" />
                        <input
                            v-model.trim="search"
                            type="search"
                            placeholder="Номер, клиент, интерес, договор" />
                    </label>
                    <select v-model="executionFilter">
                        <option
                            v-for="item in executionFilters"
                            :key="item.key"
                            :value="item.key">
                            {{ item.title }}
                        </option>
                    </select>
                    <select v-model="paymentFilter">
                        <option
                            v-for="item in paymentFilters"
                            :key="item.key"
                            :value="item.key">
                            {{ item.title }}
                        </option>
                    </select>
                    <select v-model="deliveryFilter">
                        <option
                            v-for="item in deliveryFilters"
                            :key="item.key"
                            :value="item.key">
                            {{ item.title }}
                        </option>
                    </select>
                    <span class="sales_orders_count">{{ filteredOrders.length }} из {{ crmOrders.length }}</span>
                </div>

                <a-spin :spinning="loading">
                    <div class="sales_orders_table">
                        <div class="sales_orders_table__row sales_orders_table__row--head">
                            <span>Номер</span>
                            <span>Клиент</span>
                            <span>Интерес</span>
                            <span>Договор</span>
                            <span>Дата</span>
                            <span>Сумма</span>
                            <span>Выполнение</span>
                            <span>Оплата</span>
                            <span>Отгрузка</span>
                            <span>Ответств.</span>
                            <span></span>
                        </div>

                        <article
                            v-for="order in filteredOrders"
                            :key="order.id"
                            class="sales_orders_table__row"
                            role="button"
                            tabindex="0"
                            @click="openOrder(order.id)"
                            @keydown.enter.prevent="openOrder(order.id)"
                            @keydown.space.prevent="openOrder(order.id)">
                            <span class="sales_orders_number">
                                <button type="button" @click.stop="openOrder(order.id)">
                                    {{ getOrderNumber(order) }}
                                </button>
                                <small>{{ getGoodsHint(order) }}</small>
                            </span>
                            <span>
                                <button
                                    v-if="getCustomerId(order)"
                                    type="button"
                                    class="sales_orders_link"
                                    @click.stop="openCustomer(order)">
                                    {{ getClientName(order) }}
                                </button>
                                <template v-else>{{ getClientName(order) || 'Не определен' }}</template>
                            </span>
                            <span>
                                <button
                                    v-if="getInterestId(order)"
                                    type="button"
                                    class="sales_orders_link"
                                    @click.stop="openInterest(order)">
                                    {{ getInterestName(order) }}
                                </button>
                                <template v-else>—</template>
                            </span>
                            <span>{{ getContractName(order) }}</span>
                            <span>{{ formatDate(order.created_at) }}</span>
                            <span class="sales_orders_money">{{ formatMoney(order.amount) }}</span>
                            <span>
                                <i
                                    class="sales_orders_status"
                                    :class="getStatusTone(order.execute_status, 'execution')">
                                    {{ getStatusName(order.execute_status, 'В работе') }}
                                </i>
                            </span>
                            <span>
                                <i
                                    class="sales_orders_status"
                                    :class="getStatusTone(order.payment_status, 'payment')">
                                    {{ getStatusName(order.payment_status, 'Ожидает') }}
                                </i>
                            </span>
                            <span>
                                <i
                                    class="sales_orders_status"
                                    :class="getStatusTone(order.delivery_status, 'delivery')">
                                    {{ getStatusName(order.delivery_status, 'Новая') }}
                                </i>
                            </span>
                            <span>{{ getResponsible(order) || '—' }}</span>
                            <span>
                                <button
                                    type="button"
                                    class="sales_orders_open"
                                    @click.stop="openOrder(order.id)">
                                    Открыть
                                </button>
                            </span>
                        </article>

                        <div v-if="!filteredOrders.length && !loading" class="sales_orders_empty">
                            Заказы по выбранным условиям не найдены.
                        </div>
                    </div>
                </a-spin>

                <div class="sales_orders_footer">
                    <span>{{ crmOrders.length }} CRM-заказов</span>
                    <b>{{ formatMoney(totalAmount) }}</b>
                </div>
            </main>

            <aside class="sales_orders__right" data-guide-id="sales-orders-summary">
                <section class="sales_orders_right_block">
                    <div class="sales_orders_right_title">Итого</div>
                    <div
                        v-for="item in summaryCards"
                        :key="item.key"
                        class="sales_orders_right_stat">
                        <span>{{ item.title }}</span>
                        <b :class="item.tone ? `sales_orders_right_stat--${item.tone}` : null">{{ item.value }}</b>
                    </div>
                    <div class="sales_orders_right_stat sales_orders_right_stat--total">
                        <span>Сумма</span>
                        <b>{{ formatMoney(totalAmount) }}</b>
                    </div>
                </section>

                <section class="sales_orders_right_block">
                    <div class="sales_orders_right_title">Перейти</div>
                    <button type="button" class="sales_orders_rlink" @click="goTo('sales-interest')">
                        <i class="sales_orders_rdot sales_orders_rdot--blue" />
                        Интересы к заказу
                        <span>↗</span>
                    </button>
                    <button type="button" class="sales_orders_rlink" @click="handleSummary({ key: 'delivery' })">
                        <i class="sales_orders_rdot sales_orders_rdot--orange" />
                        К отгрузке
                        <span>{{ summaryDeliveryCount }}</span>
                    </button>
                    <button type="button" class="sales_orders_rlink" @click="handleSummary({ key: 'payment' })">
                        <i class="sales_orders_rdot sales_orders_rdot--amber" />
                        Ожид. оплаты
                        <span>{{ summaryPaymentCount }}</span>
                    </button>
                </section>
            </aside>
        </div>

        <OrderDrawer
            ref="orderDrawer"
            page_name="crm.list_order_page"
            :crmSourceInterestId="crmSourceInterestId"
            :crmCustomerContractId="crmCustomerContractId" />
    </ModuleWrapper>

    <OrdersList
        v-else
        :pageConfig="pageConfig" />
</template>

<script>
import axios from '@/config/axios'
import eventBus from '@/utils/eventBus'
import pageMeta from '@/mixins/pageMeta'

const DONE_EXECUTION_CODES = ['completed', 'processed']
const CANCELED_EXECUTION_CODES = ['canceled', 'cancelled', 'partially_canceled']
const PAID_CODES = ['paid']
const PARTIAL_PAYMENT_CODES = ['partially_paid']
const DELIVERED_CODES = ['delivered']
const PARTIAL_DELIVERY_CODES = ['partially_delivered']
const TRANSIT_DELIVERY_CODES = ['in_transit', 'formed']

export default {
    name: 'OrderPage',
    mixins: [pageMeta],
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        OrdersList: () => import('@apps/Orders/components/OrdersList'),
        OrderDrawer: () => import('@apps/Orders/views/CreateOrder/OrderDrawer.vue')
    },
    data() {
        return {
            pageName: 'crm.GoodsOrderModel_list',
            loading: false,
            orders: [],
            search: '',
            executionFilter: 'all',
            paymentFilter: 'all',
            deliveryFilter: 'all',
            crmSourceInterestId: '',
            crmCustomerContractId: ''
        }
    },
    computed: {
        pageConfig() {
            return this.$route.meta?.pageConfig ? this.$route.meta.pageConfig : null
        },
        isSalesOrders() {
            return this.$route.name === 'sales-orders'
        },
        crmOrders() {
            return this.orders.filter(order => order.customer_contract)
        },
        filteredOrders() {
            const query = this.search.toLowerCase()
            return this.crmOrders.filter(order => {
                const haystack = [
                    this.getOrderNumber(order),
                    this.getClientName(order),
                    this.getInterestName(order),
                    this.getContractName(order),
                    order.goods_content
                ].join(' ').toLowerCase()
                return (!query || haystack.includes(query))
                    && this.matchExecution(order, this.executionFilter)
                    && this.matchPayment(order, this.paymentFilter)
                    && this.matchDelivery(order, this.deliveryFilter)
            })
        },
        totalAmount() {
            return this.filteredOrders.reduce((total, order) => total + this.toNumber(order.amount), 0)
        },
        summaryPaymentCount() {
            return this.crmOrders.filter(order => this.matchPayment(order, 'wait')).length
        },
        summaryDeliveryCount() {
            return this.crmOrders.filter(order => this.matchDelivery(order, 'wait')).length
        },
        summaryCards() {
            return [
                {
                    key: 'all',
                    title: 'Заказов',
                    value: this.crmOrders.length,
                    active: this.executionFilter === 'all' && this.paymentFilter === 'all' && this.deliveryFilter === 'all'
                },
                {
                    key: 'delivery',
                    title: 'К отгрузке',
                    value: this.summaryDeliveryCount,
                    tone: 'green',
                    active: this.deliveryFilter === 'wait'
                },
                {
                    key: 'payment',
                    title: 'Ожид. оплаты',
                    value: this.summaryPaymentCount,
                    tone: 'amber',
                    active: this.paymentFilter === 'wait'
                },
                {
                    key: 'done',
                    title: 'Завершены',
                    value: this.crmOrders.filter(order => this.matchExecution(order, 'done')).length,
                    active: this.executionFilter === 'done'
                }
            ]
        },
        executionFilters() {
            return [
                { key: 'all', title: 'Выполнение: все', sideTitle: 'Все', icon: 'fi-rr-box' },
                { key: 'processing', title: 'В работе', icon: 'fi-rr-settings' },
                { key: 'done', title: 'Завершены', sideTitle: 'Выполнен', icon: 'fi-rr-check' },
                { key: 'canceled', title: 'Отменены', sideTitle: 'Отменен', icon: 'fi-rr-cross-small' }
            ]
        },
        paymentFilters() {
            return [
                { key: 'all', title: 'Оплата: все', sideTitle: 'Все', icon: 'fi-rr-wallet' },
                { key: 'wait', title: 'Ожидают оплаты', sideTitle: 'Ожид. оплаты', icon: 'fi-rr-time-fast' },
                { key: 'partial', title: 'Частично оплачены', sideTitle: 'Частично', icon: 'fi-rr-chart-pie-simple' },
                { key: 'paid', title: 'Оплачены', sideTitle: 'Оплачено', icon: 'fi-rr-check-circle' }
            ]
        },
        deliveryFilters() {
            return [
                { key: 'all', title: 'Отгрузка: все', sideTitle: 'Все', icon: 'fi-rr-box-open' },
                { key: 'wait', title: 'К отгрузке', icon: 'fi-rr-bell' },
                { key: 'transit', title: 'В процессе', sideTitle: 'В пути', icon: 'fi-rr-truck-side' },
                { key: 'delivered', title: 'Отгружены', sideTitle: 'Отгружено', icon: 'fi-rr-check' }
            ]
        }
    },
    watch: {
        '$route.name'(value) {
            if (value === 'sales-orders') {
                this.loadOrders()
            }
        },
        '$route.query.createOrder': {
            immediate: true,
            handler(value) {
                if (value && this.isSalesOrders) {
                    this.$nextTick(this.openCreateOrderFromQuery)
                }
            }
        }
    },
    created() {
        if (this.isSalesOrders) {
            this.loadOrders()
        }
    },
    mounted() {
        eventBus.$on('update_order_list', this.handleOrderListUpdate)
    },
    beforeDestroy() {
        eventBus.$off('update_order_list', this.handleOrderListUpdate)
    },
    methods: {
        handleOrderListUpdate() {
            if (this.isSalesOrders) {
                this.loadOrders()
            }
        },
        async loadOrders() {
            this.loading = true
            try {
                const { data } = await axios.get('/crm/orders/', {
                    params: {
                        page: 1,
                        page_size: 200,
                        page_name: this.pageName,
                        crm_only: 1
                    }
                })
                this.orders = data?.results || []
            } catch (e) {
                this.orders = []
                this.$message.error('Не удалось загрузить CRM-заказы')
            } finally {
                this.loading = false
            }
        },
        openCreateOrder(sourceInterestId = '', customerContractId = '') {
            this.crmSourceInterestId = sourceInterestId
            this.crmCustomerContractId = customerContractId
            this.$nextTick(() => {
                this.$refs.orderDrawer?.toggleDrawer()
            })
        },
        openCreateOrderFromQuery(attempt = 0) {
            if (!this.$refs.orderDrawer && attempt < 80) {
                window.setTimeout(() => this.openCreateOrderFromQuery(attempt + 1), 150)
                return
            }
            if (!this.$refs.orderDrawer) {
                return
            }
            this.openCreateOrder(this.$route.query.interest || '', this.$route.query.customer_contract || '')
            const query = { ...this.$route.query }
            delete query.createOrder
            delete query.interest
            delete query.customer_contract
            this.$router.replace({ query })
        },
        handleSummary(item) {
            if (item.key === 'all') {
                this.executionFilter = 'all'
                this.paymentFilter = 'all'
                this.deliveryFilter = 'all'
                return
            }
            if (item.key === 'payment') this.paymentFilter = 'wait'
            if (item.key === 'delivery') this.deliveryFilter = 'wait'
            if (item.key === 'done') this.executionFilter = 'done'
        },
        countByFilter(type, key) {
            return this.crmOrders.filter(order => {
                if (type === 'execution') return this.matchExecution(order, key)
                if (type === 'payment') return this.matchPayment(order, key)
                return this.matchDelivery(order, key)
            }).length
        },
        matchExecution(order, key) {
            const code = this.getStatusCode(order.execute_status)
            if (key === 'all') return true
            if (key === 'done') return DONE_EXECUTION_CODES.includes(code)
            if (key === 'canceled') return CANCELED_EXECUTION_CODES.includes(code)
            return !DONE_EXECUTION_CODES.includes(code) && !CANCELED_EXECUTION_CODES.includes(code)
        },
        matchPayment(order, key) {
            const code = this.getStatusCode(order.payment_status)
            if (key === 'all') return true
            if (key === 'paid') return PAID_CODES.includes(code)
            if (key === 'partial') return PARTIAL_PAYMENT_CODES.includes(code)
            return !PAID_CODES.includes(code) && !PARTIAL_PAYMENT_CODES.includes(code)
        },
        matchDelivery(order, key) {
            const code = this.getStatusCode(order.delivery_status)
            if (key === 'all') return true
            if (key === 'delivered') return DELIVERED_CODES.includes(code)
            if (key === 'transit') return TRANSIT_DELIVERY_CODES.includes(code) || PARTIAL_DELIVERY_CODES.includes(code)
            return !DELIVERED_CODES.includes(code) && !TRANSIT_DELIVERY_CODES.includes(code) && !PARTIAL_DELIVERY_CODES.includes(code)
        },
        openOrder(id) {
            if (!id) return
            const query = { ...this.$route.query, order: id }
            this.$router.push({ query })
        },
        openInterest(order) {
            const id = this.getInterestId(order)
            if (!id) return
            this.$router.push({ name: 'sales-interest', query: { task: id } })
        },
        openCustomer(order) {
            const id = this.getCustomerId(order)
            if (!id) return
            this.$router.push({ name: 'sales-clients', query: { client: id } })
        },
        goTo(name) {
            if (!name || this.$route.name === name) return
            this.$router.push({ name })
        },
        getOrderNumber(order) {
            return order.number_1c || order.counter || order.id || '—'
        },
        getClientName(order) {
            return order.customer_card?.name
                || order.customer_contract?.external_customer?.name
                || 'Не определен'
        },
        getCustomerId(order) {
            return order.customer_card?.id || ''
        },
        getInterest(order) {
            return order.customer_contract?.source_interest || null
        },
        getInterestId(order) {
            return this.getInterest(order)?.id || ''
        },
        getInterestName(order) {
            const interest = this.getInterest(order)
            if (!interest) return ''
            const counter = interest.counter ? `#${interest.counter}` : ''
            return [counter, interest.name].filter(Boolean).join(' · ')
        },
        getContractName(order) {
            const contract = order.customer_contract
            return contract?.number || contract?.string_view || contract?.id || '—'
        },
        getGoodsHint(order) {
            return order.goods_content || `${this.formatQuantity(order.quantity)} поз.`
        },
        getResponsible(order) {
            return order.user?.full_name
                || order.user?.name
                || order.operator?.full_name
                || order.operator?.name
                || ''
        },
        getStatusCode(status) {
            return status?.code || status?.id || ''
        },
        getStatusName(status, fallback) {
            return status?.name || fallback
        },
        getStatusTone(status, type) {
            const code = this.getStatusCode(status)
            if (type === 'execution') {
                if (DONE_EXECUTION_CODES.includes(code)) return 'sales_orders_status--success'
                if (CANCELED_EXECUTION_CODES.includes(code)) return 'sales_orders_status--danger'
                return 'sales_orders_status--info'
            }
            if (type === 'payment') {
                if (PAID_CODES.includes(code)) return 'sales_orders_status--success'
                if (PARTIAL_PAYMENT_CODES.includes(code)) return 'sales_orders_status--warning'
                return 'sales_orders_status--danger'
            }
            if (DELIVERED_CODES.includes(code)) return 'sales_orders_status--success'
            if (TRANSIT_DELIVERY_CODES.includes(code) || PARTIAL_DELIVERY_CODES.includes(code)) {
                return 'sales_orders_status--info'
            }
            return 'sales_orders_status--warning'
        },
        toNumber(value) {
            const number = Number(String(value || 0).replace(/\s/g, '').replace(',', '.'))
            return Number.isFinite(number) ? number : 0
        },
        formatMoney(value) {
            const number = this.toNumber(value)
            if (!number) return '—'
            return `${new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 0
            }).format(number)} ₸`
        },
        formatQuantity(value) {
            const number = this.toNumber(value)
            if (!number) return '0'
            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 3
            }).format(number)
        },
        formatDate(value) {
            if (!value) return '—'
            const date = new Date(value)
            if (Number.isNaN(date.getTime())) return '—'
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: '2-digit'
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.sales_orders {
    display: grid;
    grid-template-columns: 178px minmax(0, 1fr) 220px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    background: #eeedea;
    color: #1a1a1a;
}

.sales_orders__aside {
    min-height: 0;
    overflow-y: auto;
    border-right: 1px solid #e0dfd8;
    background: #fff;
}

.sales_orders__right {
    min-height: 0;
    overflow-y: auto;
    border-left: 1px solid #e0dfd8;
    background: #fff;
}

.sales_orders__main {
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 12px;
}

.sales_orders__head,
.sales_orders_toolbar,
.sales_orders_table,
.sales_orders_footer {
    border: 1px solid #e0dfd8;
    background: #fff;
}

.sales_orders__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    padding: 12px;
    border-radius: 8px 8px 0 0;
    border-bottom: 0;
}

.sales_orders__head h2 {
    margin: 0 0 3px;
    font-size: 14px;
    line-height: 1.2;
    font-weight: 500;
}

.sales_orders__head p {
    margin: 0;
    font-size: 12px;
    line-height: 1.35;
    color: #666660;
}

.sales_orders_head_action,
.sales_orders_filter,
.sales_orders_open,
.sales_orders_rlink {
    font: inherit;
    border: 1px solid #cccbc3;
    border-radius: 6px;
    background: #fff;
    color: #1a1a1a;
    cursor: pointer;
}

.sales_orders_head_action {
    min-height: 28px;
    padding: 0 9px;
    color: #e67e2e;
    white-space: nowrap;
}

.sales_orders_panel {
    padding: 10px 8px 8px;
    border-bottom: 1px solid #eeedea;
}

.sales_orders_panel--head {
    padding: 10px 12px;
}

.sales_orders_panel__caption {
    font-size: 13px;
    font-weight: 500;
}

.sales_orders_panel__subcaption {
    margin-top: 2px;
    color: #666660;
    font-size: 11px;
}

.sales_orders_panel__title {
    margin-bottom: 7px;
    padding: 0 4px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .4px;
    text-transform: uppercase;
    color: #99998f;
}

.sales_orders_filter {
    width: 100%;
    min-height: 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
    padding: 0 8px;
    border-color: transparent;
    background: transparent;
    color: #666660;
    text-align: left;
}

.sales_orders_filter:hover,
.sales_orders_filter--active {
    background: #f5f5f4;
    color: #1a1a1a;
}

.sales_orders_filter--active {
    box-shadow: inset 2px 0 0 #e67e2e;
}

.sales_orders_filter span {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 7px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sales_orders_filter b {
    min-width: 22px;
    padding: 1px 6px;
    border-radius: 9px;
    background: #f5f5f4;
    color: #666660;
    font-size: 10px;
    text-align: center;
}

.sales_orders_toolbar {
    display: grid;
    grid-template-columns: minmax(220px, 1fr) 150px 160px 150px auto;
    gap: 7px;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 0;
}

.sales_orders_search {
    min-width: 0;
    height: 30px;
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 0 9px;
    border: 1px solid #d9d8d1;
    border-radius: 6px;
    background: #fafaf8;
    color: #99998f;
}

.sales_orders_search input,
.sales_orders_toolbar select {
    width: 100%;
    min-width: 0;
    height: 28px;
    border: 0;
    outline: 0;
    background: transparent;
    color: #1a1a1a;
    font: inherit;
    font-size: 12px;
}

.sales_orders_toolbar select {
    padding: 0 7px;
    border: 1px solid #d9d8d1;
    border-radius: 6px;
    background: #fff;
}

.sales_orders_count {
    color: #666660;
    font-size: 12px;
    white-space: nowrap;
}

.sales_orders_table {
    min-height: 0;
    overflow: auto;
    border-radius: 0;
}

.sales_orders_table__row {
    min-width: 1120px;
    min-height: 45px;
    display: grid;
    grid-template-columns: 108px minmax(130px, 1.05fr) minmax(150px, 1.25fr) minmax(120px, .9fr) 78px 92px 112px 106px 106px 88px 86px;
    align-items: center;
    gap: 9px;
    padding: 0 12px;
    border-bottom: 1px solid #eeedea;
    background: #fff;
    color: #1a1a1a;
}

.sales_orders_table__row:not(.sales_orders_table__row--head) {
    cursor: pointer;
}

.sales_orders_table__row:not(.sales_orders_table__row--head):hover {
    background: #fffaf5;
}

.sales_orders_table__row--head {
    min-height: 31px;
    position: sticky;
    top: 0;
    z-index: 1;
    background: #fafaf8;
    color: #99998f;
    cursor: default;
}

.sales_orders_table__row span {
    min-width: 0;
    overflow: hidden;
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sales_orders_table__row--head span {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}

.sales_orders_number {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.sales_orders_number button,
.sales_orders_link {
    max-width: 100%;
    padding: 0;
    border: 0;
    background: transparent;
    color: #185fa5;
    font: inherit;
    font-size: 12px;
    text-align: left;
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sales_orders_number small {
    overflow: hidden;
    color: #99998f;
    font-size: 10px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sales_orders_money {
    font-weight: 500;
}

.sales_orders_status {
    max-width: 100%;
    display: inline-flex;
    align-items: center;
    min-height: 22px;
    padding: 0 7px;
    border-radius: 5px;
    font-style: normal;
    font-size: 11px;
}

.sales_orders_status--success {
    background: #effaf3;
    color: #1f7a45;
}

.sales_orders_status--info {
    background: #eef6ff;
    color: #185fa5;
}

.sales_orders_status--warning {
    background: #fff7e6;
    color: #9a5c00;
}

.sales_orders_status--danger {
    background: #fff1f1;
    color: #a32d2d;
}

.sales_orders_open {
    min-height: 27px;
    padding: 0 9px;
    color: #185fa5;
    font-size: 11px;
}

.sales_orders_empty {
    padding: 28px 12px;
    color: #666660;
    font-size: 12px;
}

.sales_orders_footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 12px;
    border-top: 0;
    border-radius: 0 0 8px 8px;
    color: #666660;
    font-size: 12px;
}

.sales_orders_footer b {
    color: #1a1a1a;
    font-weight: 600;
}

.sales_orders_right_block {
    padding: 12px;
    border-bottom: 1px solid #eeedea;
}

.sales_orders_right_title {
    margin-bottom: 8px;
    color: #99998f;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .4px;
    text-transform: uppercase;
}

.sales_orders_right_stat {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 4px 0;
    color: #666660;
    font-size: 11px;
}

.sales_orders_right_stat b {
    color: #1a1a1a;
    font-weight: 600;
}

.sales_orders_right_stat--total {
    margin-top: 7px;
    padding-top: 8px;
    border-top: 1px solid #eeedea;
}

.sales_orders_right_stat--green {
    color: #1f7a45 !important;
}

.sales_orders_right_stat--amber {
    color: #9a5c00 !important;
}

.sales_orders_rlink {
    width: 100%;
    min-height: 32px;
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    padding: 0 9px;
    border-color: transparent;
    background: transparent;
    text-align: left;
}

.sales_orders_rlink:hover {
    background: #f5f5f4;
}

.sales_orders_rlink span {
    color: #99998f;
}

.sales_orders_rdot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
}

.sales_orders_rdot--blue {
    background: #185fa5;
}

.sales_orders_rdot--orange {
    background: #e67e2e;
}

.sales_orders_rdot--amber {
    background: #d08a00;
}

@media (max-width: 1100px) {
    .sales_orders {
        grid-template-columns: 1fr;
        overflow: auto;
    }

    .sales_orders__aside {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        border-right: 0;
        border-bottom: 1px solid #e0dfd8;
        overflow: visible;
    }

    .sales_orders__right {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        border-left: 0;
        border-top: 1px solid #e0dfd8;
        overflow: visible;
    }

    .sales_orders_toolbar {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 760px) {
    .sales_orders__aside,
    .sales_orders__right,
    .sales_orders_toolbar {
        grid-template-columns: 1fr;
    }

    .sales_orders__head {
        flex-direction: column;
    }
}
</style>
