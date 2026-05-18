<template>
    <div>
        <div
            class="order_list order_block"
            :class="isMobile && 'order_list_mobile'">
            <div class="flex items-center mb-2">
                <span class="font-semibold text-base">Информация о заказе</span>
                <template v-if="!isMobile">
                    <a-button
                        v-if="order && order.operation_type && order.operation_type.code=='20'"
                        @click="sendOrder"
                        :loading="loadingBtn"
                        class="ml-2"
                        size="small" type="primary">
                        <!--{{order.button_name}}-->
                        Преобразовать в заказ
                    </a-button>
                </template>
            </div>

            <div
                v-if="order.execute_status"
                class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Статус выполнения:
                </div>
                <div class="value text-right">
                    <Status :status="order.execute_status" />
                    <div class="status_update text-right">
                        от {{ $moment(order.updated_at).format('DD.MM.YYYY') }}
                    </div>
                </div>
            </div>

            <div
                v-if="order.payment_status"
                class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Статус оплаты:
                </div>
                <div class="value text-right">
                    <Status :status="order.payment_status" />
                </div>
            </div>

            <div
                v-if="order.delivery_status"
                class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Статус доставки:
                </div>
                <div class="value text-right">
                    <Status :status="order.delivery_status" />
                </div>
            </div>

            <template v-if="isMobile">
                <a-button
                    v-if="order && order.operation_type && order.operation_type.code=='20'"
                    @click="sendOrder"
                    :loading="loadingBtn"
                    class="mb-4 mt-1"
                    size="large"
                    block
                    type="primary">
                    <!--{{order.button_name}}-->
                    Преобразовать в заказ
                </a-button>
            </template>


            <div
                v-if="order.show_operation_type && order.operation_type"
                class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Статус операции:
                </div>
                <div class="value text-right">
                    {{order.operation_type.name}}
                </div>
            </div>
            <div v-if="order.logistic_task" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Задание на доставку:
                </div>
                <div class="value">
                    <i class="fi fi-rr-map-marker-plus text_green mr-1"></i>
                    Добавлена
                </div>
            </div>
            <div class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Дата создания:
                </div>
                <div class="value">
                    {{ $moment(order.created_at).format('DD.MM.YYYY') }}
                </div>
            </div>
            <div v-if="order.reason" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Источник CRM:
                </div>
                <div class="value">
                    <a-button type="link" class="p-0" @click="openReason(order.reason)">
                        {{ order.reason.name || 'Открыть источник' }}
                    </a-button>
                </div>
            </div>
            <div v-if="order.customer_contract" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    CRM-договор:
                </div>
                <div class="value">
                    {{ order.customer_contract.number || order.customer_contract.string_view || order.customer_contract.id }}
                </div>
            </div>
            <div v-if="crmCustomerName" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    CRM-клиент:
                </div>
                <div class="value">
                    {{ crmCustomerName }}
                </div>
            </div>
            <div v-if="order.customer_contract_progress" class="crm_contract_info">
                <div>
                    <span>Сумма договора</span>
                    <b>{{ priceFormatter(order.customer_contract_progress.contract_amount) }}</b>
                </div>
                <div>
                    <span>Предмет договора</span>
                    <b>{{ priceFormatter(order.customer_contract_progress.subject_amount) }}</b>
                </div>
                <div>
                    <span>Уже заказано</span>
                    <b>{{ priceFormatter(order.customer_contract_progress.ordered_amount) }}</b>
                </div>
                <div>
                    <span>Отгружено</span>
                    <b>{{ formatQuantity(order.customer_contract_progress.delivered_quantity) }}</b>
                </div>
            </div>
            <div v-if="order.contractor && !order.customer_contract" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Клиент:
                </div>
                <div class="value">
                    {{ order.contractor.name }}
                </div>
            </div>
            <div v-if="order.contractor_member && !order.customer_contract" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Контрагент:
                </div>
                <div class="value">
                    {{ order.contractor_member.name }}
                </div>
            </div>
            <div v-if="order.contract && !order.customer_contract" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Договор:
                </div>
                <div class="value">
                    {{ order.contract.name }}
                </div>
            </div>
            <div v-if="order.quantity" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Количество:
                </div>
                <div class="value">
                    {{ order.quantity }}
                </div>
            </div>
            <div v-if="order.show_nds && order.nds_amount" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Сумма НДС:
                </div>
                <div :class="['value', isMobile || 'font-light text-base']">
                    {{ priceFormatter(order.nds_amount) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>
            </div>
            <div v-if="order.amount" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Сумма заказа:
                </div>
                <div class="value font-semibold text-lg">
                    {{ priceFormatter(order.amount) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                </div>
            </div>
            <div v-if="order.user" ref="order_authpr" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Заказ создал:
                </div>
                <div class="value">
                    <Profiler :user="order.user" :avatarSize="22" :getPopupContainer="getPopupContainer('order_authpr')" />
                </div>
            </div>
            <div v-if="order.co_executors && order.co_executors.length" ref="order_authpr" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Соисполнители:
                </div>
                <div class="value">
                    <div v-for="executor in order.co_executors" :key="executor.id">
                        <Profiler :user="executor" :avatarSize="22" :getPopupContainer="getPopupContainer('order_authpr')" />
                    </div>
                </div>
            </div>
            <div v-if="order.user" ref="order_authpr" class="item">
                <div class="label" :class="isMobile && 'my-2'">
                    Заказ отредактировал:
                </div>
                <div class="value grid justify-items-end">
                    <div v-if="order.last_editor">
                        <Profiler :user="order.last_editor" :avatarSize="22" :getPopupContainer="getPopupContainer('order_authpr')" />
                    </div>
                    <div v-if="order.updated_at">
                        {{ $moment(order.updated_at).format('DD.MM.YYYY HH:mm') }}
                    </div>
                </div>
            </div>
            <div v-if="order.comment" class="item comment">
                <div class="label" :class="isMobile && 'my-2'">
                    Комментарий к заказу:
                </div>
                <div class="value">
                    {{ order.comment }}
                </div>
            </div>
        </div>
        <!-- DESKTOP -->
        <template v-if="!isMobile">
            <div
                v-if="order.warehouse || order.delivery_address"
                class="deliviry order_block">
                <h2 v-if="order.delivery_company">Склад погрузки</h2>
                <h2 v-if="order.delivery_address && order.delivery_address.address">Склад погрузки</h2>
                <h2 v-if="order.warehouse">Склад погрузки</h2>
                <div v-if="order.delivery_company" class="warehouse_info">
                    <div class="val">
                        <div v-if="order.delivery_company.name" class="w_item">
                            <div class="item_label">
                                Транспортная компания:
                            </div>
                            <div class="item_val">
                                {{ order.delivery_company.name }}
                            </div>
                        </div>
                        <div v-if="order.delivery_address" class="w_item">
                            <div class="item_label">
                                Адрес доставки:
                            </div>
                            <div class="item_val">
                                {{ order.delivery_address }}
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="order.delivery_address && order.delivery_address.address" class="warehouse_info">
                    <div class="val">
                        <div class="w_item">
                            <div class="item_label">
                                Адрес доставки:
                            </div>
                            <div class="item_val">
                                {{ order.delivery_address.address }}
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="order.warehouse" class="warehouse_info">
                    <div class="val">
                        <div v-if="order.warehouse.name" class="w_item">
                            <div class="item_label">
                                Cклад:
                            </div>
                            <div class="item_val">
                                {{ order.warehouse.name }}
                            </div>
                        </div>
                        <div v-if="order.warehouse.address" class="address w_item">
                            <div class="item_label">
                                Адрес:
                            </div>
                            <div class="item_val">
                                {{ order.warehouse.address }}
                            </div>
                        </div>
                        <div v-if="order.warehouse.manager" class="manager w_item">
                            <div class="item_label">
                                Ответственное лицо:
                            </div>
                            <div ref="warehouse_user" class="item_val">
                                <Profiler
                                    :user="order.warehouse.manager"
                                    :getPopupContainer="getPopupContainer('warehouse_user')"
                                    :avatarSize="22" />
                            </div>
                        </div>
                        <div v-if="order.warehouse.phone" class="phone w_item">
                            <div class="item_label">
                                Контактный телефон:
                            </div>
                            <div class="item_val">
                                <a :href="`tel:${order.warehouse.phone}`">
                                    {{ order.warehouse.phone }}
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <template v-else>
                <div
                    v-if="order.delivery_warehouses && order.delivery_warehouses.length"
                    class="order_block">
                    <h2>Адрес самовывоза</h2>
                    <div class="warehouse_info">
                        <div
                            v-for="item in order.delivery_warehouses"
                            :key="item.id"
                            class="warehouse_info_item">
                            <div class="name font-semibold">
                                {{ item.name }}
                            </div>
                            <div class="address font-light">
                                {{ item.address }}
                            </div>
                            <div
                                v-if="item.manager"
                                class="manager info_item">
                                <div class="lab">
                                    Менеджер:
                                </div>
                                <div class="ival">
                                    {{ item.manager.full_name }}
                                </div>
                            </div>
                            <div
                                v-if="item.phone"
                                class="phone mt-1 info_item">
                                <div class="lab">
                                    Телефон:
                                </div>
                                <div class="ival">
                                    <a :href="`tel:${item.phone}`">
                                        {{ item.phone }}
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </template>

        </template>
        <!-- MOBILE -->
        <template v-else>
            <div class="flex items-center flex-wrap mb-4">
                <a-button
                    v-if="order.has_pay_file || alwaysShowGetPaidButton"
                    block
                    :loading="loadingInvoice"
                    type="primary"
                    size="large"
                    class="flex items-center justify-center"
                    @click="getInvoicePayment">
                    <i class="fi fi-rr-wallet mr-2"></i>
                    Получить счет на оплату
                </a-button>
                <a-button
                    v-if="order.has_print"
                    block
                    class="flex items-center mt-2 justify-center"
                    :loading="loadingPrint"
                    type="primary"
                    size="large"
                    @click="getPrintOrder">
                    <i class="fi fi-rr-print mr-2"></i>
                    Печать
                </a-button>
            </div>

            <a-collapse
                :bordered="false"
                v-model="expandedCollapse"
                class="order_info_collapse_mobile">
                <a-collapse-panel
                    key="warehouse_info"
                    header="Склад погрузки">
                    <div
                        v-if="order.warehouse || order.delivery_address"
                        class="deliviry order_block">
                        <div v-if="order.delivery_company" class="warehouse_info">
                            <div class="val">
                                <div v-if="order.delivery_company.name" class="w_item">
                                    <div class="item_label">
                                        Транспортная компания:
                                    </div>
                                    <div class="item_val">
                                        {{ order.delivery_company.name }}
                                    </div>
                                </div>
                                <div v-if="order.delivery_address" class="w_item">
                                    <div class="item_label">
                                        Адрес доставки:
                                    </div>
                                    <div class="item_val">
                                        {{ order.delivery_address }}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="order.delivery_address && order.delivery_address.address" class="warehouse_info">
                            <div class="val">
                                <div class="w_item">
                                    <div class="item_label">
                                        Адрес доставки:
                                    </div>
                                    <div class="item_val">
                                        {{ order.delivery_address.address }}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="order.warehouse" class="warehouse_info">
                            <div class="val">
                                <div v-if="order.warehouse.name" class="w_item">
                                    <div class="item_label">
                                        Cклад:
                                    </div>
                                    <div class="item_val">
                                        {{ order.warehouse.name }}
                                    </div>
                                </div>
                                <div v-if="order.warehouse.address" class="address w_item">
                                    <div class="item_label">
                                        Адрес:
                                    </div>
                                    <div class="item_val">
                                        {{ order.warehouse.address }}
                                    </div>
                                </div>
                                <div v-if="order.warehouse.manager" class="manager w_item">
                                    <div class="item_label">
                                        Ответственное лицо:
                                    </div>
                                    <div class="item_val">
                                        {{ order.warehouse.manager.full_name }}
                                    </div>
                                </div>
                                <div v-if="order.warehouse.phone" class="phone w_item">
                                    <div class="item_label">
                                        Контактный телефон:
                                    </div>
                                    <div class="item_val">
                                        <a :href="`tel:${order.warehouse.phone}`">
                                            {{ order.warehouse.phone }}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <template v-else>
                        <div
                            v-if="order.delivery_warehouses && order.delivery_warehouses.length"
                            class="order_block">
                            <h2>Адрес самовывоза</h2>
                            <div class="warehouse_info">
                                <div
                                    v-for="item in order.delivery_warehouses"
                                    :key="item.id"
                                    class="warehouse_info_item">
                                    <div class="name font-semibold">
                                        {{ item.name }}
                                    </div>
                                    <div class="address font-light">
                                        {{ item.address }}
                                    </div>
                                    <div
                                        v-if="item.manager"
                                        class="manager info_item">
                                        <div class="lab">
                                            Менеджер:
                                        </div>
                                        <div class="ival">
                                            {{ item.manager.full_name }}
                                        </div>
                                    </div>
                                    <div
                                        v-if="item.phone"
                                        class="phone mt-1 info_item">
                                        <div class="lab">
                                            Телефон:
                                        </div>
                                        <div class="ival">
                                            <a :href="`tel:${item.phone}`">
                                                {{ item.phone }}
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                </a-collapse-panel>
                <a-collapse-panel
                    key="delivery"
                    header="Доставка">
                    <OrderDelivery
                        v-if="order.delivery_date_plan && order.delivery_date_plan.delivery_date_plan_gte || order.delivery_point"
                        :showLabel="!isMobile"
                        :order="order" />
                </a-collapse-panel>
                <a-collapse-panel
                    key="pay"
                    header="Способ оплаты">
                    <OrderPayMethods
                        v-if="order.show_pay_type"
                        :orderPaymentForm="orderPaymentForm"
                        :orderStages="orderStages"
                        :order="order"
                        :showLabel="!isMobile"
                        :payLoader="payLoader" />
                </a-collapse-panel>
            </a-collapse>
        </template>
        <template v-if="!isMobile">
            <OrderDelivery
                v-if="order.delivery_date_plan && order.delivery_date_plan.delivery_date_plan_gte || order.delivery_point"
                :order="order" />
            <OrderPayMethods
                v-if="order.show_pay_type"
                :orderPaymentForm="orderPaymentForm"
                :orderStages="orderStages"
                :order="order"
                :payLoader="payLoader" />
        </template>
        <template v-if="!isMobile">
            <div v-if="orderActions" class="-mt-2 flex gap-x-3 grid grid-cols-9 items-center">
                <a-button
                    v-if="order.has_pay_file || alwaysShowGetPaidButton"
                    :loading="loadingInvoicePayment"
                    type="primary"
                    class="items-center col-span-2"
                    @click="getInvoicePayment">
                    <i class="fi fi-rr-wallet mr-2"></i>
                    Получить счет на оплату
                </a-button>
                <a-button
                    v-if="order.has_print"
                    class="flex items-center col-span-2"
                    :loading="loadingPrint"
                    type="primary"
                    @click="getPrintOrder">
                    <i class="fi fi-rr-print mr-2"></i>
                    Печать
                </a-button>
                <a-button
                    v-if="alwaysShowGetPaidButton && !order.warehouse.default_warehouse"
                    :loading="loadingInvoice"
                    type="primary"
                    class="items-center col-span-2"
                    @click="getInvoice">
                    <i class="fi fi-rr-print mr-2"></i>
                    Печать документов
                </a-button>
            </div>
        </template>


        <div :class="!isMobile && 'mt-8'">
            <a-form-model
                v-if="logisticManagerOnly"
                ref="orderForm"
                :rules="rules"
                :model="orderForm"
                class="order_form">
                <div class="order_form_title text-base font-semibold">
                    Доставка
                </div>
                <div class="order_form_container">
                    <a-form-model-item
                        prop="operator"
                        class="order_form_item_wrapper">
                        <label class="order_form_item">
                            <span>Водитель:</span>
                            <UserDrawer
                                v-model="orderForm.operator"
                                :disabled="isOrderFormDisabled"
                                inputSize="large"
                                class="order_form_control"
                                title="Водитель" />
                        </label>
                    </a-form-model-item>
                    <a-form-model-item
                        prop="car"
                        class="order_form_item_wrapper">
                        <label class="order_form_item">
                            <span>Автомобиль:</span>
                            <a-input
                                v-model="orderForm.car"
                                :disabled="isOrderFormDisabled"
                                size="large"
                                class="order_form_control" />
                        </label>
                    </a-form-model-item>
                </div>
                <a-button
                    v-if="!isOrderFormDisabled"
                    type="primary"
                    class="mt-2"
                    :loading="loading.saveOrder"
                    @click="saveOrder">
                    Сохранить
                </a-button>
            </a-form-model>
        </div>
    </div>
</template>

<script>
import { priceFormatter } from '@/utils'
import { mapState } from 'vuex'
export default {
    components: {
        UserDrawer: () => import('../../../views/CreateOrder/widgets/UserDrawer'),
        Status: () => import('../Status.vue'),
        OrderPayMethods: () => import('./OrderPayMethods.vue'),
        OrderDelivery: () => import('./OrderDelivery.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        order: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            orderPaymentForm: null,
            orderStages: [],
            payLoader: false,
            loadingBtn: false,
            loadingInvoice: false,
            loadingInvoicePayment: false,
            loadingPrint: false,
            expandedCollapse: '',
            isOrderFormDisabled: false,
            crmCustomerFromContract: null,
            orderForm: {
                operator: null,
                car: null
            },
            rules: {
                operator: [
                    { required: true, message: this.$t('task.field_require'), trigger: 'blur' },
                ],
                car: [
                    { required: true, message: this.$t('task.field_require'), trigger: 'blur' },
                    { max: 255, message: this.$t('task.field_min_require'), trigger: 'blur' }
                ]
            },
            loading: {
                saveOrder: false
            }
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            orderActions: state => state.orders.orderActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        logisticManagerOnly() {
            return this.$store.state?.user?.user?.me_logistic_manager_only
        },
        alwaysShowGetPaidButton() {
            return this.config?.order_setting?.always_show_get_paid_button || false
        },
        crmCustomerName() {
            return this.order?.customer_card?.name || this.crmCustomerFromContract?.name || ''
        }
    },
    watch: {
        'order.customer_contract.id'() {
            this.loadCrmContractCustomer()
        }
    },
    created() {
        this.getOrderPay()
        this.initOrderForm()
        this.loadCrmContractCustomer()
    },
    methods: {
        priceFormatter,
        openReason(reason) {
            if (!reason?.id) {
                return
            }
            if (reason.type === 'tasks.TaskModel') {
                this.$router.push({ name: 'sales-interest', query: { task: reason.id } })
            }
        },
        formatQuantity(value) {
            return Number(value || 0).toLocaleString('ru-RU', {
                maximumFractionDigits: 3
            })
        },
        async loadCrmContractCustomer() {
            const contract = this.order?.customer_contract
            const contractId = contract?.id || contract
            this.crmCustomerFromContract = null
            if(!contractId || this.order?.customer_card?.name) {
                return
            }
            try {
                const { data } = await this.$http.get(`/customer_contracts/${contractId}/`)
                this.crmCustomerFromContract = data?.customer_cards?.length === 1 ? data.customer_cards[0] : null
            } catch(e) {
                console.log(e)
            }
        },
        getPopupContainer(refEl) {
            return () => this.$refs[refEl]
        },
        async getInvoicePayment(){
            this.loadingInvoicePayment = true
            await this.getFiles(`crm/orders/${this.id}/pay_file/`)
            this.loadingInvoicePayment = false
        },
        async getInvoice(){
            this.loadingInvoice = true
            await this.getFiles(`crm/orders/${this.id}/doc_sale/`, 'Реализация товаров')
            this.loadingInvoice = false
        },
        async getPrintOrder(){
            this.loadingPrint = true
            await this.getFiles(`crm/orders/${this.id}/order_1c_form/`)
            this.loadingPrint = false
        },
        async getFiles(endoint, docType='Счет'){
            if(typeof this.orderActions.blob_file === 'boolean') {
                try{
                    const { data } = await this.$http.get(endoint)
                    if(data.path) {
                        window.open(data.path, '_blank')
                    } else {
                        this.$message.warning('Нет пути к файлу')
                    }
                }
                catch(error){
                    console.log("error", error)
                    this.$message.warning(error.error_str)
                }
            } else {
                try{
                    const response = await this.$http.get(endoint, {
                        responseType: 'blob'
                    })

                    const url = window.URL.createObjectURL(new Blob([response.data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${docType} - заказ №${this.order.counter} от ${this.$moment().format('DD.MM.YYYY')}.pdf`)
                    document.body.appendChild(link)
                    link.click()
                }
                catch(error){
                    console.log("error", error)
                    this.$message.warning(error.error_str)
                }
            }
        },
        async sendOrder(){
            try{
                this.loadingBtn = true
                const {data} = await this.$http.post('integration_1c/send_order_to_1c/', {order: this.id})
                this.$emit("update:order", data)
            }
            catch(e){
                console.log(e)
            }
            finally{
                setTimeout(() => {
                    this.loadingBtn = false
                }, 200);
            }
        },
        async getOrderPay() {
            if(this.order?.contract?.code) {
                try {
                    this.payLoader = true
                    const { data } = await this.$http.get('/catalogs/contracts/payment/', {
                        params: {
                            code: this.order.contract.code
                        }
                    })
                    if(data) {
                        if(data.payment_form?.name) {
                            this.orderPaymentForm = data.payment_form.name
                        } else {
                            this.orderPaymentForm = {}
                            this.orderPaymentForm.name = 'Любая'
                        }
                        this.orderStages = data.stages
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.payLoader = false
                }
            }
        },
        saveOrder() {
            this.$refs.orderForm.validate(async valid => {
                if(valid)
                    try {
                        this.loading.saveOrder = true
                        const form = Object.assign({}, this.orderForm)
                        form.operator = form.operator.id
                        await this.$http.put(`/crm/orders/${this.order.id}/set_driver/`, form)

                        this.order.car = this.orderForm.car
                        this.order.operator = this.orderForm.operator
                        this.initOrderForm()
                    } catch(error) {
                        this.$message.error(`Ошибка: ${error}`)
                    } finally {
                        this.loading.saveOrder = false
                    }
            })
        },
        initOrderForm() {
            if(this.logisticManagerOnly) {
                if(this.order?.car)
                    this.orderForm.car = this.order.car
                if(this.order?.operator) {
                    this.orderForm.operator = this.order.operator
                    this.isOrderFormDisabled = true
                }
            }
        }
    }
}
</script>
<style lang="scss">
.order_info_collapse_mobile {
    margin: 0 -15px;
    .ant-collapse-content-box {
        padding-top: 5px;
        padding: 15px;
    }
}
.order_form {
    .order_form_item_wrapper.ant-row.ant-form-item {
        @media(max-width: 640px) {
            margin-bottom: 10px;
        }
    }
}
</style>

<style lang="scss" scoped>
.order_list{
    .item{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        .label{
            font-weight: 300;
            color: #000;
        }
        &.comment{
            display: block;
            .label{
                margin-bottom: 10px;
            }
            .value{
                line-height: 24px;
            }
        }
        &:not(:last-child){
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border2);
        }
        .status_update{
            font-size: 12px;
            margin-top: 4px;
            font-weight: 300;
            color: #999;
        }
        .value{
            text-align: left;
        }
    }
}

.order_list_mobile {
    .item{
        &:not(:last-child){
            margin-bottom: 5px;
            padding-bottom: 5px;
            border-bottom: 1px solid var(--border2);
        }
    }
}

.crm_contract_info {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--border2);

    div {
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        padding: 8px;
        min-width: 0;
    }

    span {
        display: block;
        color: var(--grayColor);
        font-size: 12px;
        margin-bottom: 3px;
    }

    b {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 600;
    }
}

.warehouse_info{
    background: #eff2f5;
    padding: 15px;
    border-radius: var(--borderRadius);
    .warehouse_info_item{
        &:not(:last-child){
            margin-bottom: 10px;
            border-bottom: 1px solid #e3e3e3;
            padding-bottom: 10px;
        }
        .info_item{
            .lab{
                font-weight: 300;
            }
        }
        .address{
            &:not(:last-child){
                margin-bottom: 8px;
            }
        }
    }
    .name{
        &:not(:last-child) {
            margin-bottom: 7px;
        }
    }
    .label{
        font-weight: 600;
        margin-bottom: 10px;
    }
    .w_item{
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .item_label{
            font-weight: 300;
        }
    }
}

.order_form {
    border: 1px solid var(--border2);
    position: relative;

    padding: 15px;
    border-radius: var(--borderRadius);

    @media(min-width: 768px) {
        padding: 30px;
    }
    .order_form_title {
        position: absolute;
        top: 0;
        transform: translateY(-50%);
        left: 30px;
        padding: 0 6px;
        background-color: #fff;
    }
    .order_form_container {
        display: grid;
        @media(min-width: 1024px) {
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        .order_form_item_wrapper {
            .order_form_item {
                display: grid;

                @media(min-width: 640px) {
                    grid-template-columns: 140px 1fr;
                    gap: 10px;
                }
                @media(min-width: 1024px) {
                    grid-template-columns: 100px 1fr;
                }

            }
        }
    }
}
</style>
