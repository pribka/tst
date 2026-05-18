<template>
    <div class="create_order_page crm_order_page"
         :class="isMobile ? 'create_order_mobile' : ''">
        <div class="order_wrap crm_order_wrap">
            <h1
                v-if="!edit && showTitle"
                class="crm_order_title">
                Оформление заказа
            </h1>
            <a-result
                v-if="!loading && orderEmpty && !createEmptyOrder && !isCrmOrderFlow"
                title="Для оформления заказа добавьте товар">
                <template #icon>
                    <a-icon
                        type="shopping"
                        theme="twoTone"/>
                </template>
                <template #extra>
                    <a-button
                        type="primary"
                        size="large"
                        @click="openCatalog()">
                        Перейти в каталог
                    </a-button>
                </template>
            </a-result>
            <div
                v-if="loading"
                class="flex justify-center">
                <a-spin/>
            </div>
            <template v-else>
                <template v-if="showOrderForm">
                    <a-spin
                        :spinning="reload"
                        size="large">
                        <div
                            class="crm_order_process"
                            data-guide-id="crm-order-process">
                            <div
                                v-for="(step, index) in orderProcessSteps"
                                :key="step.key"
                                class="crm_order_step"
                                :class="step.state">
                                <div class="crm_order_step_num">
                                    <a-icon
                                        v-if="step.state === 'done'"
                                        type="check" />
                                    <span v-else>{{ index + 1 }}</span>
                                </div>
                                <div class="crm_order_step_label">
                                    {{ step.label }}
                                </div>
                                <div
                                    v-if="index < orderProcessSteps.length - 1"
                                    class="crm_order_step_line"
                                    :class="step.state" />
                            </div>
                        </div>
                        <div
                            v-if="sourceInterestId || sourceCustomerContractId"
                            class="crm_order_source_strip"
                            data-guide-id="crm-order-source">
                            <div class="crm_order_source_main">
                                <i class="fi fi-rr-box-open"></i>
                                <div>
                                    <div class="crm_order_source_title">
                                        Источник заказа
                                    </div>
                                    <div class="crm_order_source_text">
                                        {{ sourceInterestId ? 'Заказ создается из CRM-интереса' : 'Заказ создается вручную' }}
                                    </div>
                                </div>
                            </div>
                            <div
                                v-if="sourceCustomerContractId"
                                class="crm_order_source_badge">
                                CRM-договор привязан
                            </div>
                        </div>
                        <div
                            v-if="sourceInterestId || sourceCustomerContractId"
                            class="crm_order_customer_bridge"
                            data-guide-id="crm-order-customer">
                            <div class="crm_order_customer_item crm_order_customer_item_main">
                                <span>Получатель отгрузки</span>
                                <a-select
                                    v-if="crmCustomerCards.length > 1"
                                    v-model="form.customer_card"
                                    class="crm_order_customer_select"
                                    size="small"
                                    placeholder="Выберите клиента">
                                    <a-select-option
                                        v-for="card in crmCustomerCards"
                                        :key="card.id"
                                        :value="card.id">
                                        {{ card.name }}
                                    </a-select-option>
                                </a-select>
                                <b v-else>{{ crmCustomerName || (crmSourceLoading ? 'Загружаем...' : 'Не определен') }}</b>
                                <small v-if="crmCustomerHint">{{ crmCustomerHint }}</small>
                            </div>
                            <div
                                v-if="crmContractTitle"
                                class="crm_order_customer_item">
                                <span>CRM-договор</span>
                                <b>{{ crmContractTitle }}</b>
                            </div>
                            <div
                                v-if="crmInterestName"
                                class="crm_order_customer_item">
                                <span>Интерес</span>
                                <b>{{ crmInterestName }}</b>
                            </div>
                        </div>
                        <a-alert
                            v-if="sourceInterestId"
                            class="crm_order_source_alert"
                            type="info"
                            show-icon
                            message="Заказ создается из CRM-интереса"
                            description="Позиции заказа заполняются из потребностей интереса. После оформления заказ будет связан с этим интересом как источник сделки." />
                        <a-alert
                            v-if="sourceCustomerContractId"
                            class="crm_order_source_alert"
                            type="success"
                            show-icon
                            message="Заказ связан с CRM-договором"
                            description="После оформления заказ попадет в прогресс договора: будет видно, сколько по договору уже заказано и отгружено." />
                        <div :class="isMobile ? 'crm_order_body crm_order_body_mobile' : 'crm_order_body'">
                            <div class="crm_order_main min-w-0">
                                <a-form-model
                                    ref="orderForm"
                                    class="crm_order_form"
                                    :model="form"
                                    :rules="rules">
                                    <WidgetSwitch
                                        v-for="item in orderFormWidgets"
                                        :ref="item.widget"
                                        :form="form"
                                        :getFormRef="getFormRef"
                                        :changeContract="changeContract"
                                        :key="item.widget"
                                        :reload="reload"
                                        :setOrderLoader="setOrderLoader"
                                        :amount="amount"
                                        :injectContractorFilter="injectContractorFilter"
                                        :sourceCustomerContractId="sourceCustomerContractId"
                                        :edit="edit"
                                        :reloadAmount="reloadAmount"
                                        :item="item"
                                        :setOrderFormCalculated="setOrderFormCalculated"
                                        :payDatePlanRequired="payDatePlanRequired"
                                        :isOrderDrawer="isOrderDrawer"
                                        :createEmptyOrder="createEmptyOrder"/>
                                    <div class="crm_order_extra_grid">
                                        <div
                                            class="crm_order_extra_card"
                                            data-guide-id="crm-order-delivery">
                                            <div class="crm_order_extra_title">
                                                <i class="fi fi-rr-truck-side"></i>
                                                Доставка
                                            </div>
                                            <a-form-model-item class="form_item crm_order_form_item">
                                                <a-radio-group
                                                    v-model="form.pickup"
                                                    button-style="solid"
                                                    size="small"
                                                    @change="setOrderFormCalculated(false)">
                                                    <a-radio-button :value="false">
                                                        Доставка
                                                    </a-radio-button>
                                                    <a-radio-button :value="true">
                                                        Самовывоз
                                                    </a-radio-button>
                                                </a-radio-group>
                                            </a-form-model-item>
                                            <a-form-model-item
                                                v-if="!form.pickup"
                                                label="Адрес и условия доставки"
                                                class="form_item crm_order_form_item">
                                                <a-textarea
                                                    v-model="form.delivery_address_str"
                                                    :auto-size="{ minRows: 2, maxRows: 4 }"
                                                    placeholder="Адрес, контакт получателя, временное окно"
                                                    @change="setOrderFormCalculated(false)" />
                                            </a-form-model-item>
                                            <div
                                                v-else
                                                class="crm_order_hint">
                                                Заказ останется без адреса доставки. Склад отгрузки выбирается в составе заказа.
                                            </div>
                                        </div>

                                        <div
                                            class="crm_order_extra_card"
                                            data-guide-id="crm-order-payment">
                                            <div class="crm_order_extra_title">
                                                <i class="fi fi-rr-wallet"></i>
                                                Оплата и комментарий
                                            </div>
                                            <div class="crm_order_payment_row">
                                                <a-form-model-item
                                                    label="К оплате"
                                                    class="form_item crm_order_form_item">
                                                    <a-input-number
                                                        v-model="form.amount_paid"
                                                        :min="0"
                                                        :precision="2"
                                                        style="width: 100%;"
                                                        @change="setOrderFormCalculated(false)" />
                                                </a-form-model-item>
                                                <a-form-model-item
                                                    label="Плановая дата оплаты"
                                                    class="form_item crm_order_form_item">
                                                    <a-date-picker
                                                        v-model="form.pay_date_plan"
                                                        style="width: 100%;"
                                                        @change="setOrderFormCalculated(false)" />
                                                </a-form-model-item>
                                            </div>
                                            <a-form-model-item
                                                label="Комментарий"
                                                class="form_item crm_order_form_item">
                                                <a-textarea
                                                    v-model="form.comment"
                                                    :auto-size="{ minRows: 2, maxRows: 4 }"
                                                    placeholder="Что важно учесть при оформлении, оплате или отгрузке" />
                                            </a-form-model-item>
                                        </div>
                                    </div>
                                </a-form-model>
                            </div>
                            <div
                                class="crm_order_side_wrap"
                                data-guide-id="crm-order-summary">
                                <div
                                    :class="[
                                        orderForm.aside.sticky && 'sticky',
                                        isMobile ? 'order_aside_mobile' : 'order_aside'
                                    ]">
                                    <div class="crm_order_side_header">
                                        <div class="crm_order_side_title">
                                            Итог заказа
                                        </div>
                                        <div class="crm_order_side_status">
                                            {{ isCalculated ? 'рассчитан' : 'черновик' }}
                                        </div>
                                    </div>
                                    <div class="order_summary">
                                        <a-button
                                            v-if="orderForm.aside && orderForm.aside.calculate_button"
                                            :type="orderForm.aside.calculate_button.type"
                                            :size="orderForm.aside.calculate_button.size"
                                            class="calculate_btn"
                                            block
                                            :loading="priceLoader"
                                            @click="onSubmit(0)">
                                            {{ orderForm.aside.calculate_button.btnText || 'Рассчитать цены' }}
                                        </a-button>

                                        <div
                                            v-if="orderForm.aside.showAmount"
                                            class="summary_info">
                                            <div
                                                v-if="noDiscount"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    Сумма без скидки:
                                                </span>
                                                <div class="value">
                                                    {{ noDisAmount }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                            <div
                                                v-if="discountSum"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    Сумма скидки:
                                                </span>
                                                <div class="value">
                                                    {{ cartDiscountSum }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                            <div class="price flex items-baseline justify-between">
                                                <span>
                                                    Итого:
                                                </span>
                                                <div class="value">
                                                    <a-spin :spinning="cartAmountLoader">
                                                        {{ cartAmount }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                        <span v-else class="ml-1">&#8381;</span>
                                                    </a-spin>
                                                </div>
                                            </div>
                                            <div
                                                v-if="showPrepayment"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    Доступный аванс:
                                                </span>
                                                <div class="value">
                                                    {{ formatPrepayment }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                            <div
                                                v-if="showMustpaid"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    К оплате:
                                                </span>
                                                <div class="value">
                                                    {{ formatMustpaid }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                            <div
                                                v-if="orderForm.aside && orderForm.aside.show_nds && cartNds"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    В т.ч. НДС:
                                                </span>
                                                <div class="value">
                                                    {{ ndsSum }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- <a-button v-if="orderForm.calculated"
                                                  :type="orderForm.aside.orderButton.type"
                                                  :size="orderForm.aside.orderButton.size"
                                                  class="summary_btn"
                                                  block
                                                  :loading="orderLoader"
                                                  @click="onSubmit(20)">

                                            Сформировать КП

                                        </a-button>
                                        <a-button v-else
                                                  :type="orderForm.aside.orderButton.type"
                                                  :size="orderForm.aside.orderButton.size"
                                                  class="summary_btn" disabled
                                                  block
                                                  :loading="orderLoader"
                                                  @click="onSubmit()">

                                            Сформировать КП
                                        </a-button> -->
                                    </div>


                                    <!--<OrderOffer-->
                                    <!--:orderForm="orderForm"-->
                                    <!--:form="form" />-->
                                    <template v-if="orderForm && orderForm.aside && orderForm.aside.showAmountBanner && edit && showAmountBanner && Number(oldAmount) != Number(amount) && user.can_create_logistic_task">
                                        <a-alert class="mt-3" :message="`Внимание! Сумма заказа составляла ${oldAmount} ${cartCurrency.icon}. После редактирования составляет ${cartAmount} ${cartCurrency.icon}. Согласуйте с покупателем новую стоимость`" banner />
                                    </template>

                                    <div
                                        class="order-summary"
                                        data-guide-id="crm-order-submit">
                                        <div
                                            v-if="orderForm.aside && orderForm.aside.offer && orderForm.aside.offer.show"
                                            class="offer_block mt-3">
                                            <template v-if="orderForm.aside && orderForm.aside.calculate_button">
                                                <a-button v-if="isCalculated"
                                                          :type="orderForm.aside.orderButton.type"
                                                          :size="orderForm.aside.orderButton.size"
                                                          class="summary_btn"
                                                          block
                                                          :loading="orderLoader"
                                                          @click="onSubmit(40)">
                                                    <template v-if="edit">
                                                        Сохранить
                                                    </template>
                                                    <template v-else>
                                                        {{ orderForm.aside.orderButton.btnText || 'Сформировать заказ' }}
                                                    </template>
                                                </a-button>
                                                <a-button v-else
                                                          :type="orderForm.aside.orderButton.type"
                                                          :size="orderForm.aside.orderButton.size"
                                                          class="summary_btn"
                                                          disabled
                                                          block
                                                          :loading="orderLoader"
                                                          @click="onSubmit()">
                                                    <template v-if="edit">
                                                        Сохранить
                                                    </template>
                                                    <template v-else>
                                                        {{ orderForm.aside.orderButton.btnText || 'Сформировать заказ' }}
                                                    </template>
                                                </a-button>
                                            </template>
                                            <template v-else>
                                                <a-button
                                                    :type="orderForm.aside.orderButton.type"
                                                    :size="orderForm.aside.orderButton.size"
                                                    class="summary_btn"
                                                    block
                                                    :loading="orderLoader"
                                                    @click="onSubmit(40)">
                                                    <template v-if="edit">
                                                        Сохранить
                                                    </template>
                                                    <template v-else>
                                                        {{ orderForm.aside.orderButton.btnText || 'Сформировать заказ' }}
                                                    </template>
                                                </a-button>
                                            </template>

                                            <template v-if="edit">
                                                <a-button
                                                    v-if="form.has_pay_file || alwaysShowGetPaidButton"
                                                    :loading="loadingInvoicePayment"
                                                    block
                                                    class="items-center mt-3"
                                                    @click="getInvoicePayment">
                                                    <i class="fi fi-rr-wallet mr-2"></i>
                                                    Получить счет на оплату
                                                </a-button>
                                                <a-button
                                                    v-if="alwaysShowGetPaidButton && !form.warehouse.default_warehouse"
                                                    :loading="loadingInvoice"
                                                    block
                                                    class="items-center mt-1"
                                                    @click="getInvoice">
                                                    <i class="fi fi-rr-print mr-2"></i>
                                                    Печать документов
                                                </a-button>
                                            </template>
                                        </div>
                                    </div>

                                    <!-- Блок информации о доступном остатке и лимиту по договору -->
                                    <div class="order_summary">
                                        <div
                                            v-if="showLimits"
                                            class="summary_info"
                                            style="margin-top: 10px;">
                                            <div
                                                v-if="contractLimit"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    Лимит по договору:
                                                </span>
                                                <div class="value">
                                                    {{ formatContractLimit }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                            <div
                                                v-if="availableBalance"
                                                class="oth_price flex items-baseline justify-between">
                                                <span>
                                                    Доступный остаток:
                                                </span>
                                                <div class="value">
                                                    {{ formatAvailableBalance }} <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="order_summary">

                                        <!-- <a-button
                                            :type="orderForm.aside.orderButton.type"
                                            :size="orderForm.aside.orderButton.size"
                                            class="calculate_btn"
                                            block
                                            :loading="priceLoader"
                                            @click="onSubmit(0)">
                                            Рассчитать цены
                                        </a-button> -->

                                    </div>
                                    <div
                                        class="crm_order_after_submit"
                                        data-guide-id="crm-order-after-submit">
                                        <div class="crm_order_after_title">
                                            После оформления
                                        </div>
                                        <div class="crm_order_after_text">
                                            Заказ попадет в список продаж и будет готов к передаче в логистику. По CRM-договору обновится сумма заказанного.
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a-spin>
                </template>
            </template>
        </div>
    </div>
</template>

<script>
import {mapState} from 'vuex'
import {priceFormatter} from '@/utils'
import eventBus from '@/utils/eventBus.js'
//import OrderOffer from './widgets/OrderOffer.vue'
import warehouse from '../../mixins/warehouse'
let timer;
export default {
    components: {
        WidgetSwitch: () => import('./widgets/WidgetSwitch.vue'),
        // OrderOffer
    },
    props: {
        contractorID: {
            type: String,
            default: ''
        },
        contrsctorDeliveryPoint: {
            type: String,
            default: ''
        },
        isOrderDrawer: {
            type: Boolean,
            default: false
        },
        edit: {
            type: Boolean,
            default: false
        },
        injectOrder: {
            type: Object,
            default: () => {}
        },
        injectContractor: {
            type: Object,
            default: () => {}
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        showTitle: {
            type: Boolean,
            default: true
        },
        injectContractorFilter: {
            type: Object,
            default: () => {}
        },
        pageName: {
            type: String,
            default: "crm.GoodsOrderModel_list"
        },
        crmSourceInterestId: {
            type: String,
            default: ''
        },
        crmCustomerContractId: {
            type: String,
            default: ''
        }
    },
    mixins: [
        warehouse
    ],
    metaInfo() {
        return {
            title: this.pageTitle
        }
    },
    computed: {
        ...mapState({
            cartCurrency: state => state.orders.orderCurrency,
            cartList: state => state.orders.orderList,
            firstOrderLoading: state => state.orders.firstOrderLoading,
            orderEmpty: state => state.orders.orderEmpty,
            config: state => state.config.config,
            user: state => state.user.user,
            newOrders: state => state.orders.create_orders,
            orderActions: state => state.orders.orderActions
        }),
        logisticManagerOnly() {
            return this.$store.state?.user?.user?.me_logistic_manager_only
        },
        alwaysShowGetPaidButton() {
            return this.config?.order_setting?.always_show_get_paid_button || false
        },
        visible: {
            get() {
                return this.createVisible
            },
            set(val) {
                this.$store.commit('orders/SET_CREATE_VISIBLE', val)
            }
        },
        calculationButton() {
            return this.config?.order_setting?.calculationButton || true
        },
        multipleWarehousesInOrder() {
            return this.config?.order_setting?.multiple_warehouses_in_order || true
        },
        orderProcessSteps() {
            return [
                {
                    key: 'customer',
                    label: this.sourceCustomerContractId ? 'CRM-клиент' : 'Клиент',
                    state: (this.crmCustomerName || this.form.customer_card || (!this.sourceCustomerContractId && this.form.contractor)) ? 'done' : 'future'
                },
                { key: 'interest', label: 'Интерес', state: this.sourceInterestId ? 'done' : 'future' },
                { key: 'goods', label: 'Товары', state: this.cartList?.results?.length ? 'active' : 'future' },
                { key: 'delivery', label: 'Доставка', state: this.form.pickup || this.form.delivery_address_str ? 'active' : 'future' },
                { key: 'payment', label: 'Оплата', state: this.isCalculated ? 'active' : 'future' },
                { key: 'submit', label: 'Оформить', state: this.isCalculated ? 'active' : 'future' }
            ]
        },
        orderFormWidgets() {
            return (this.orderForm?.orderForm || [])
                .filter(item => !(this.sourceCustomerContractId && item.widget === 'OrderType'))
                .map(item => ({
                    ...item,
                    crmCompact: item.widget === 'OrderCart'
                }))
        },
        cartAmount() {
            return priceFormatter(this.amount)
        },
        noDisAmount() {
            return priceFormatter(this.noDiscount)
        },
        cartDiscountSum() {
            return priceFormatter(this.discountSum)
        },
        ndsSum() {
            return priceFormatter(this.cartNds)
        },
        formatPrepayment() {
            return priceFormatter(this.prepayment)
        },
        formatMustpaid() {
            return priceFormatter(this.mustpaid)
        },
        siteName() {
            if (this.config?.site_setting?.site_name)
                return this.config.site_setting.site_name
            else
                return 'BPMS'
        },
        pageTitle() {
            if (this.$route?.meta?.title) {
                return `${this.$route.meta.title} | ${this.siteName}`
            } else {
                return this.siteName
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        availableBalance () { // Вернет true если доступный остаток не равен null или undefined
            return this.availableBalanceValue !== null && this.availableBalanceValue !== undefined
        },
        contractLimit () { // Вернет true если лимит по договору не равен null или undefined
            return this.contractLimitValue !== null && this.contractLimitValue !== undefined
        },
        formatAvailableBalance() { // Добавляет разделитель разрядов
            return this.availableBalanceValue ? this.availableBalanceValue.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") : null
        },
        formatContractLimit() { // Добавляет разделитель разрядов
            return this.contractLimitValue ? this.contractLimitValue.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") : null
        },
        showPrepayment() { 
            return this.orderForm.aside.showPrepayment && this.prepayment
        },
        showMustpaid() {
            return this.orderForm.aside.showMustpaid && this.mustpaid
        },
        sourceInterestId() {
            return this.crmSourceInterestId || this.$route?.query?.interest || ''
        },
        sourceCustomerContractId() {
            return this.crmCustomerContractId || this.$route?.query?.customer_contract || ''
        },
        isCrmOrderFlow() {
            return Boolean(this.sourceInterestId || this.sourceCustomerContractId)
        },
        crmSourceInterest() {
            return this.crmSourceContext?.interest || null
        },
        crmSourceContracts() {
            return this.crmSourceContext?.contracts || []
        },
        crmSourceContract() {
            if (!this.crmSourceContracts?.length) {
                return null
            }
            return this.crmSourceContracts.find(item => item.id === this.sourceCustomerContractId) || this.crmSourceContracts[0]
        },
        crmCustomerCards() {
            const cards = []
            const pushCard = card => {
                if(!card?.id || cards.some(item => item.id === card.id)) {
                    return
                }
                cards.push(card)
            }
            const contractCards = this.crmSourceContract?.customer_cards || []
            contractCards.forEach(pushCard)
            if(!this.form.customer_contract) {
                pushCard(this.crmSourceInterest?.customer_card)
            }
            return cards
        },
        selectedCrmCustomerCard() {
            const customerCardId = this.form.customer_card
            if(!customerCardId) {
                return null
            }
            return this.crmCustomerCards.find(card => card.id === customerCardId) || null
        },
        crmCustomerHint() {
            if(!this.form.customer_contract) {
                return ''
            }
            if(this.crmCustomerCards.length === 1 && this.form.customer_card) {
                return 'Выбран единственный клиент договора'
            }
            if(this.crmCustomerCards.length > 1) {
                return 'Клиент сохраняется в заказе как получатель отгрузки'
            }
            if(!this.crmCustomerCards.length) {
                return 'В договоре нет обслуживаемых CRM-клиентов'
            }
            return ''
        },
        crmCustomerName() {
            return (
                this.selectedCrmCustomerCard?.name ||
                (!this.form.customer_contract ? this.crmSourceInterest?.customer_card?.name : '') ||
                (!this.form.customer_contract ? this.crmSourceInterest?.customer_card_name : '') ||
                ''
            )
        },
        crmContractTitle() {
            if (!this.crmSourceContract) {
                return ''
            }
            return this.crmSourceContract.number || this.crmSourceContract.string_view || this.crmSourceContract.id
        },
        crmInterestName() {
            return this.crmSourceInterest?.name || this.crmSourceInterest?.counter || ''
        },
        createEmptyOrder() {
            if(this.edit)
                return false
            else {
                return this.orderForm?.orderSetting?.createEmptyOrder ? true : false
            }
        },
        showOrderForm() {
            if(this.createEmptyOrder || this.isCrmOrderFlow) {
                return true
            } else {
                if(this.orderForm && !this.orderEmpty) {
                    return true
                } else
                    return false
            }
        }
    },
    data() {
        return {
            form: {},
            rules: {},
            loadingInvoicePayment: false,
            loadingInvoice: false,
            reload: false,
            loading: false,
            cartAmountLoader: false,
            priceLoader: false,
            orderLoader: false,
            orderForm: null,
            currentContract: null,
            amount: '0',
            noDiscount: null,
            discountSum: null,
            cartNds: null,
            formRef: null,
            showLimits: false,
            contractLimitValue: null,
            availableBalanceValue: null,
            mustpaid: null,
            prepayment: null,
            payDatePlanRequired: false,
            oldAmount: '0',
            isCalculated: this.edit ? true : false,
            showAmountBanner: false,
            crmSourceContext: null,
            crmSourceLoading: false
        }
    },
    created() {
        this.$nextTick(() => {
            this.getOrderList()
        })
    },
    methods: {
        async getInvoicePayment(){
            try {
                this.loadingInvoicePayment = true
                await this.getFiles(`crm/orders/${this.form.id}/pay_file/`)
            } catch(e) {
                console.log(e)
            } finally {
                this.loadingInvoicePayment = false
            }
        },
        async getInvoice(){
            try {
                this.loadingInvoice = true
                await this.getFiles(`crm/orders/${this.form.id}/doc_sale/`, 'Реализация товаров')
            } catch(e) {
                console.log(e)
            } finally {
                this.loadingInvoice = false
            }
        },
        async getActions() {
            try {
                await this.$store.dispatch('orders/getOrderActions', {
                    id: this.form.id
                })
            } catch(e) {
                console.log(e)
            }
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
        setOrderFormCalculated(val=false) {
            this.isCalculated = val
        },
        setOrderLoader(value) {
            this.orderLoader = value
            this.priceLoader = value
        },
        getShowLimits () {
            // Показать блок с лимитом по договору и доступным остатком
            if (this.contractLimitValue || this.availableBalanceValue) {
                this.showLimits = true
            }
        },
        getFormRef() {
            return this.$refs.orderForm
        },
        changeContract(val, contractList) {
            const find = contractList.find(f => f.code === val)
            if (find) {
                this.$store.commit('orders/SET_CURRENT_CONTRCAT', find.id)
            }
            this.getOrderListReload()
        },
        async getOrderListReload() {
            try {
                this.reload = true
                await this.$store.dispatch('orders/getOrderListReload')
                this.$message.info('Цена в заказе пересчитана в соответствии с выбранным соглашением')
            } catch (e) {
                console.log(e)
                this.reload = false
            } finally {
                this.reload = false
            }
        },
        async getOrderList() {
            if(this.isCrmOrderFlow && !this.edit) {
                await this.getForm()
                await this.seedCrmOrderLines()
                return
            }
            if (this.cartList.next && !this.loading) {
                try {
                    this.loading = true
                    if(this.edit) {
                        const data = await this.$store.dispatch('orders/getOrderGoodsList', {
                            id: this.injectOrder.id
                        })
                        if (data?.results?.length) {
                            this.amount = data.amount
                            this.oldAmount = data.amount
                            await this.getWarehouseFormInfo()
                        }
                    } else {
                        const data = await this.$store.dispatch('orders/getOrderList')
                        if (data?.results?.length) {
                            this.amount = data.amount
                            await this.getWarehouseFormInfo()
                        }
                    }

                    await this.getForm()
                } catch (e) {
                    console.log(e)
                    this.loading = false
                } finally {
                    this.loading = false
                }
            }
        },
        async reloadAmount() {
            try {
                this.cartAmountLoader = true
                const { data } = await this.$http.get('/crm/shopping_cart/', {
                    params: {
                        page: 1,
                        page_size: 1
                    }
                })
                if(data) {
                    this.amount = data.amount
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.cartAmountLoader = false
            }
        },
        async getForm() {
            try {
                const {data} = await this.$http.get('/crm/orders/form_info/')
                if (data) {
                    this.orderForm = data
                    this.form = data.orderFormData
                    this.rules = data.orderFormRules

                    if(this.edit && Object.keys(this.injectOrder)?.length) {
                        const inject = this.injectOrder
                        this.form = {
                            ...this.form,
                            ...inject
                        }
                        this.getActions()
                    }
                    if(this.isOrderDrawer && this.injectContractor && Object.keys(this.injectContractor)?.length) {
                        const inject = this.injectContractor
                        this.form = {
                            ...this.form,
                            ...inject
                        }
                    }
                    this.applyCrmSource()
                    await this.loadCrmSourceContext()
                }
            } catch (e) {
                console.log(e)
            }
        },
        applyCrmSource() {
            if(this.edit) {
                return
            }
            if(this.sourceInterestId) {
                this.$set(this.form, 'reason', this.sourceInterestId)
            }
            if(this.sourceCustomerContractId) {
                this.$set(this.form, 'customer_contract', this.sourceCustomerContractId)
                this.$set(this.form, 'contractor', null)
                this.$set(this.form, 'contractor_member', null)
                if(!this.form.customer_card) {
                    this.$set(this.form, 'customer_card', null)
                }
                if(!this.form.contract) {
                    this.$set(this.form, 'contract', 'default')
                }
            }
            if((this.sourceInterestId || this.sourceCustomerContractId) && !this.form.comment) {
                this.$set(this.form, 'comment', 'Заказ оформлен из CRM-интереса')
            }
        },
        async loadCrmSourceContext() {
            if(!this.sourceInterestId && this.sourceCustomerContractId) {
                try {
                    this.crmSourceLoading = true
                    const { data } = await this.$http.get(`/customer_contracts/${this.sourceCustomerContractId}/`)
                    this.crmSourceContext = {
                        interest: null,
                        needs: [],
                        contracts: data ? [data] : []
                    }
                    this.applyDefaultCrmCustomerCard()
                } catch(e) {
                    console.log(e)
                    this.crmSourceContext = null
                } finally {
                    this.crmSourceLoading = false
                }
                return
            }
            if(!this.sourceInterestId) {
                this.crmSourceContext = null
                return
            }
            try {
                this.crmSourceLoading = true
                const { data } = await this.$http.get('/customer_contracts/for_interest/', {
                    params: {
                        interest: this.sourceInterestId
                    }
                })
                this.crmSourceContext = data || null
                this.applyDefaultCrmCustomerCard()
            } catch(e) {
                console.log(e)
                this.crmSourceContext = null
            } finally {
                this.crmSourceLoading = false
            }
        },
        applyDefaultCrmCustomerCard() {
            if(!this.form.customer_contract) {
                return
            }
            const cards = this.crmCustomerCards
            const current = this.form.customer_card
            if(current && cards.some(card => card.id === current)) {
                return
            }
            if(cards.length === 1) {
                this.$set(this.form, 'customer_card', cards[0].id)
            } else if(current) {
                this.$set(this.form, 'customer_card', null)
            }
        },
        buildCrmOrderLinePayload(sourceLine) {
            const goods = sourceLine?.goods || {}
            return {
                goods: goods.id || sourceLine?.goods_id,
                quantity: sourceLine?.quantity || 1,
                measure_unit: sourceLine?.measure_unit?.id || goods.base_measure_unit?.id || null,
                coefficient: sourceLine?.coefficient || 1,
                custom_price: sourceLine?.price || goods.price_by_catalog || 0,
                goods_for_print: goods.id || sourceLine?.goods_id
            }
        },
        async seedCrmOrderLines() {
            if(this.cartList.results?.length) {
                return
            }
            const contract = this.crmSourceContract
            const contractLines = contract?.subject_items || []
            const needLines = this.crmSourceContext?.needs || []
            const sourceLines = (this.sourceCustomerContractId && contractLines.length)
                ? contractLines
                : needLines
            const payload = sourceLines
                .map(line => this.buildCrmOrderLinePayload(line))
                .filter(line => line.goods)
            if(!payload.length) {
                this.$store.commit('orders/SET_ORDER_SOURCE_LINES', [])
                return
            }
            try {
                const orderSourceLines = await Promise.all(
                    payload.map(line => this.$http.post('/crm/orders/build_order_line/', line))
                )
                this.$store.commit('orders/SET_ORDER_SOURCE_LINES', orderSourceLines.map(({ data }) => data))
            } catch(e) {
                console.log(e)
                this.$store.commit('orders/SET_ORDER_SOURCE_LINES', [])
                this.$message.error('Не удалось заполнить состав заказа')
            }
        },
        openCatalog() {
            this.$router.push({name: 'goods'})
        },
        clear() {

        },
        checkPvhValid() {
            if(this.$refs['PvhWidget']?.[0]?.$refs?.['widgetSwitch'].$refs?.['pvh_form']) {
                return this.$refs['PvhWidget'][0].$refs['widgetSwitch'].$refs['pvh_form'].partsCheck()
            } else
                return true
        },
        async submitSuccess(data) {
            const pvhForm = this.$refs['PvhWidget']?.[0]?.$refs?.['widgetSwitch'].$refs?.['pvh_form']
            if(pvhForm) {
                await pvhForm.createForm({
                    act: 'save',
                    posted: false,
                    postedStatus: true,
                    injectId: data.id
                })
            }
        },
        reloadFinalPrices() {

        },
        onSubmit(operType = 0) {
            eventBus.$emit('change_in_goods_list')
            if(this.form.customer_contract && !this.form.customer_card) {
                this.$message.error('Выберите CRM-клиента, которому оформляется отгрузка')
                return
            }
            this.$refs.orderForm.validate(async (valid, validFields) => {
                if (valid && this.checkPvhValid()) {
                    let newOrdersCount = Object.keys(this.newOrders).length
                    try {
                        this.form.oper_type = operType

                        if(operType > 0)
                            this.orderLoader = true
                        else {
                            this.showAmountBanner = false
                            this.priceLoader = true
                        }

                        let data = null

                        if(this.edit) {
                            data = await this.$store.dispatch('orders/updateOrder', this.form)
                        } else {
                            data = await this.$store.dispatch('orders/createOrder', this.form)
                        }

                        if (data) {
                            if (operType === 0) {
                                this.orderForm.calculated = data.calculated
                                this.isCalculated = data.calculated
                                this.amount = data.amount
                                this.noDiscount = data.amount_no_discount
                                this.cartNds = data.amount_nds
                                this.contractLimitValue = data.limitcontract //Лимит по договору.
                                this.availableBalanceValue = data.remcontract //Доступный остаток.
                                this.prepayment = data.prepayment //Доступный аванс
                                this.mustpaid = data.must_paid //К оплате
                                if (data.must_paid && Number(data.must_paid) >= 0) {
                                    this.form['amount_paid'] = data.must_paid
                                    // Если к оплате больше 0 делаем поле "Дата оплаты" обязательным для ввода
                                    this.payDatePlanRequired = true
                                }

                                if(data.must_paid) {
                                    this.form['must_paid'] = data.must_paid
                                }

                                this.getShowLimits() // Показать блок с лимитом по договору и доступным остатком.


                                if(data.amount_no_discount && data.amount) {
                                    this.discountSum = Number(data.amount_no_discount) - Number(data.amount)
                                }
                                // В чем отличие полей amount_paid и mustpaid приходящих с бэка?
                                // if(data.amount_paid) {
                                //     this.form.amount_paid = data.amount_paid
                                // }

                                if(this.config?.order_setting?.calculate_warehouse_tp !== 'undefined') {
                                    if(this.config.order_setting.calculate_warehouse_tp) {
                                        this.$store.commit('orders/SET_ORDER_GOOD_LIST_ONLY_RELOAD', data.tp_goods)
                                    } else {
                                        this.$store.commit('orders/SET_ORDER_GOOD_LIST_ONLY_RELOAD_NO_CALCULATE', data.tp_goods)
                                    }
                                } else {
                                    this.$store.commit('orders/SET_ORDER_GOOD_LIST_ONLY_RELOAD', data.tp_goods)
                                }
                                if(this.edit) {
                                    this.showAmountBanner = true
                                }
                            } else {
                                let action = 'create'
                                if(this.edit) {
                                    await this.submitSuccess(data)
                                    this.showAmountBanner = false
                                    this.$message.info(`Заказ ${this.form.counter} обновлен`, 5)
                                    if(newOrdersCount) {
                                        this.$message.info(`Созданы новые заказы (${newOrdersCount} шт)`, 5)
                                    }
                                    eventBus.$emit('update_order_list')
                                    this.closeDrawer()
                                    eventBus.$emit('LOGISTIC_ORDER_RELOAD')
                                    if(this.$route.query?.order) {
                                        eventBus.$emit('OPEN_ORDER_RELOAD')
                                        eventBus.$emit('update_ow_list')
                                    }
                                    action = 'update'
                                } else if(this.isOrderDrawer) {
                                    if(Array.isArray(data)) {
                                        for(let i in data) {
                                            await this.submitSuccess(data[i])
                                        }
                                    } else {
                                        await this.submitSuccess(data)
                                    }
                                    this.$message.info('Ваш заказ создан')
                                    this.showAmountBanner = false
                                    this.closeDrawer()
                                    eventBus.$emit('need_update_contractor_list')
                                    eventBus.$emit('LOGISTIC_ORDER_RELOAD')
                                    if(this.$route.query?.order) {
                                        eventBus.$emit('OPEN_ORDER_RELOAD')
                                    }

                                } else {
                                    if(Array.isArray(data)) {
                                        const redirectId = data[0].id
                                        for(let i in data) {
                                            await this.submitSuccess(data[i])
                                        }

                                        this.showAmountBanner = false
                                        eventBus.$emit('update_order_list')
                                        this.$message.info('Ваш заказ создан')

                                        if(window?.ReactNativeWebView) {
                                            window.ReactNativeWebView.postMessage(JSON.stringify({
                                                type: 'openOrders'
                                            }))
                                        } else {
                                            if(this.orderForm?.orderSetting?.redirectType) {
                                                if(this.orderForm.orderSetting.redirectType === 'orderPage')
                                                    this.$router.push({name: 'orders'})
                                                else
                                                    this.$router.push({name: 'orders', query: {order: redirectId}})
                                            } else {
                                                if(redirectId)
                                                    this.$router.push({name: 'orders', query: {order: redirectId}})
                                            }
                                        }
                                    } else {
                                        await this.submitSuccess(data)
                                        this.$message.info('Ваш заказ создан')
                                        this.showAmountBanner = false
                                        if(window?.ReactNativeWebView) {
                                            window.ReactNativeWebView.postMessage(JSON.stringify({
                                                type: 'openOrders'
                                            }))
                                        } else {
                                            if(this.orderForm?.orderSetting?.redirectType) {
                                                if(this.orderForm.orderSetting.redirectType === 'orderPage')
                                                    this.$router.push({name: 'orders'})
                                                else
                                                    this.$router.push({name: 'orders', query: {order: data.id}})
                                            } else {
                                                this.$router.push({name: 'orders', query: {order: data.id}})
                                            }
                                        }

                                        eventBus.$emit('update_order_list')
                                    }
                                }
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: action,
                                    row: data
                                })

                                if(window?.ReactNativeWebView) {
                                    window.ReactNativeWebView.postMessage(JSON.stringify({
                                        type: 'clearCart'
                                    }))
                                }

                            }
                        }
                    } catch (e) {
                        console.log(e)
                        this.$message.error('Ошибка оформления заказа')
                    } finally {
                        if(operType > 0)
                            this.orderLoader = false
                        else
                            this.priceLoader = false
                    }
                } else {

                    if(Object.keys(validFields)?.length) {
                        const keys = Object.keys(validFields)

                        if(keys?.[0]) {
                            const selector = document.getElementById(`field_${keys[0]}`)
                            if(selector)
                                selector.scrollIntoView({behavior: "smooth", block: "center"})
                        }
                    }

                    this.$message.warning('Заполните обязательные поля')
                    return false
                }
            })
        }
    },
    mounted() {
        eventBus.$on('contractor_is_change', () => {
            this.form['pay_type'] = null
            this.form['pay_date_plan'] = null
            this.form['amount_paid'] = 0
        })
        eventBus.$on('edit_update_price', () => {
            clearTimeout(timer)

            setTimeout(() => {
                if(this.cartList.results?.length) {
                    let am = 0
                    this.cartList.results.forEach(item => {
                        const price = item.custom_price ? parseFloat(item.custom_price) : item.price ? parseFloat(item.price) : parseFloat(item.goods.price)
                        am = am + (price * Number(item.quantity))
                    })

                    if(am) {
                        this.amount = String(am)
                    }
                } else {
                    this.amount = '0'
                }
            }, 500)
            this.setOrderFormCalculated(false)
        })
    },
    beforeDestroy() {
        this.$store.commit('orders/CLEAR_ORDER_CREATE_PAGE')
        this.$store.commit('orders/SET_IS_EMPTY_ORDER', false)
        eventBus.$off('contractor_is_change')
        eventBus.$off('edit_update_price')
    }
}
</script>

<style lang="scss" scoped>
    .radio_item {
        &:not(:last-child) {
            margin-bottom: 10px;
        }
        .form_item {
            margin-top: 10px;
        }
    }

    .create_order_page {
        .crm_order_source_alert {
            margin-bottom: 12px;
        }
        .wrap_grid {
            @media(min-width: 1360px) {
                grid-template-columns: 1fr 290px;
            }
        }
        .order_aside {
            @media(min-width: 787px) {
                margin-left: auto;
                max-width: 300px;
            }
            &.sticky {
                position: sticky;
                top: 20px;
                z-index: 10;
            }
        }
        .order_summary {
            background: #eff2f5;
            border-radius: var(--borderRadius);
            .calculate_btn {
                border-radius: var(--borderRadius) var(--borderRadius) 0 0;
                font-weight: 300;
                text-transform: uppercase;
                font-size: 14px;
            }
            .summary_btn {
                border-radius: 0 0 var(--borderRadius) var(--borderRadius);
                font-weight: 300;
                text-transform: uppercase;
                font-size: 14px;
            }
            .summary_info {
                padding: 20px;
                .flex{
                    &:not(:last-child){
                        margin-bottom: 10px;
                    }
                }
            }
            .price{
                .value {
                    font-size: 20px;
                    font-weight: 600;
                }
            }
            .oth_price{
                .value {
                    font-size: 16px;
                }
            }
        }
        .order_wrap {
            max-width: 1200px;
            margin: 0 auto;
            h1 {
                font-weight: 300;
                font-size: 24px;
                margin-bottom: 30px;
            }
        }
        .order_block {
            .form_item {
                &:last-child {
                    margin-bottom: 0px;
                }
            }
        }
    }
    .create_order_mobile {
        padding: 15px;

        .order_aside_mobile {
            margin-top: 15px;
            .calculate_btn {
                border-radius: var(--borderRadius);
            }
            .summary_info {
                padding: 15px 0;
            }
        }
    }

    .crm_order_page {
        min-height: 100%;
        padding: 0;
        background: #f3f4f6;

        .crm_order_wrap {
            max-width: none;
            margin: 0;
        }

        .crm_order_title {
            margin: 0;
            padding: 14px 16px 10px;
            border-bottom: 1px solid #e5e7eb;
            background: #fff;
            font-size: 20px;
            font-weight: 500;
            color: #111827;
        }

        .crm_order_source_alert {
            display: none;
        }

        .crm_order_process {
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            padding: 10px 16px;
            background: #fff;
            border-bottom: 1px solid #e5e7eb;
        }

        .crm_order_step {
            display: flex;
            align-items: center;
            gap: 6px;
            min-width: 110px;
            flex: 1;
            color: #8c8c85;
        }

        .crm_order_step_num {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 1px solid #d7d7d0;
            background: #f5f5f4;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 11px;
            font-weight: 600;
        }

        .crm_order_step_label {
            white-space: nowrap;
            font-size: 12px;
        }

        .crm_order_step_line {
            height: 1px;
            min-width: 18px;
            flex: 1;
            background: #e0dfd8;
        }

        .crm_order_step.done,
        .crm_order_step.active {
            color: #1f2937;
        }

        .crm_order_step.done .crm_order_step_num {
            border-color: #2d7a3a;
            background: #2d7a3a;
            color: #fff;
        }

        .crm_order_step.active .crm_order_step_num {
            border-color: #e67e2e;
            background: #e67e2e;
            color: #fff;
        }

        .crm_order_step_line.done {
            background: #2d7a3a;
        }

        .crm_order_source_strip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin: 12px 12px 0;
            padding: 10px 12px;
            border: 1px solid #cfe2f3;
            border-radius: 8px;
            background: #f2f8ff;
        }

        .crm_order_source_main {
            display: flex;
            align-items: center;
            min-width: 0;
            gap: 10px;
            color: #0c447c;
        }

        .crm_order_source_main > i {
            width: 26px;
            height: 26px;
            border-radius: 6px;
            background: #e6f1fb;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .crm_order_source_title {
            color: #6b7280;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: .02em;
        }

        .crm_order_source_text {
            color: #0c447c;
            font-size: 12px;
            font-weight: 500;
        }

        .crm_order_source_badge {
            flex-shrink: 0;
            border-radius: 8px;
            padding: 3px 8px;
            background: #eaf3de;
            color: #27500a;
            font-size: 11px;
            font-weight: 500;
        }

        .crm_order_customer_bridge {
            display: grid;
            grid-template-columns: minmax(220px, 1.4fr) minmax(180px, .8fr) minmax(220px, 1fr);
            gap: 8px;
            margin: 8px 12px 0;
        }

        .crm_order_customer_item {
            min-width: 0;
            border: 1px solid #e0dfd8;
            border-radius: 8px;
            padding: 8px 10px;
            background: #fff;
        }

        .crm_order_customer_item span {
            display: block;
            margin-bottom: 3px;
            color: #99998f;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: .02em;
        }

        .crm_order_customer_item b {
            display: block;
            overflow: hidden;
            color: #1f2937;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.35;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .crm_order_customer_item small {
            display: block;
            margin-top: 4px;
            color: #7b7b72;
            font-size: 10px;
            line-height: 1.25;
        }

        .crm_order_customer_select {
            width: 100%;
        }

        .crm_order_customer_item_main {
            border-color: #cfe2f3;
            background: #f7fbff;
        }

        .crm_order_body {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 300px;
            gap: 12px;
            align-items: start;
            padding: 12px;
        }

        .crm_order_body_mobile {
            display: flex;
            flex-direction: column;
        }

        .crm_order_main,
        .crm_order_form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .crm_order_extra_grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 10px;
        }

        .crm_order_extra_card {
            border: 1px solid #e0dfd8;
            border-radius: 8px;
            overflow: hidden;
            background: #fff;
        }

        .crm_order_extra_title {
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 8px 12px;
            border-bottom: 1px solid #e0dfd8;
            background: #f5f5f4;
            color: #1f2937;
            font-size: 12px;
            font-weight: 600;
        }

        .crm_order_extra_card .crm_order_form_item {
            margin: 10px 12px;
        }

        .crm_order_payment_row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 10px;
            padding: 0 12px;
        }

        .crm_order_payment_row .crm_order_form_item {
            margin-right: 0;
            margin-left: 0;
        }

        .crm_order_hint {
            margin: 10px 12px;
            padding: 8px 10px;
            border-radius: 6px;
            background: #f5f5f4;
            color: #666660;
            font-size: 12px;
            line-height: 1.45;
        }

        .crm_order_side_wrap {
            min-width: 0;
        }

        .order_aside {
            max-width: none;
            margin-left: 0;
            border: 1px solid #e0dfd8;
            border-radius: 8px;
            overflow: hidden;
            background: #fff;

            &.sticky {
                top: 12px;
            }
        }

        .crm_order_side_header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 9px 12px;
            border-bottom: 1px solid #e0dfd8;
            background: #f5f5f4;
        }

        .crm_order_side_title {
            font-size: 12px;
            font-weight: 600;
            color: #1f2937;
        }

        .crm_order_side_status {
            border-radius: 8px;
            padding: 2px 7px;
            background: #eef2ff;
            color: #3c3489;
            font-size: 10px;
            font-weight: 500;
        }

        .order_summary {
            border-radius: 0;
            border-bottom: 1px solid #e0dfd8;
            background: #fff;

            .calculate_btn,
            .summary_btn {
                height: 34px;
                border-radius: 0;
                font-size: 12px;
                font-weight: 500;
                text-transform: none;
            }

            .summary_info {
                padding: 12px;
            }

            .price .value {
                font-size: 18px;
            }

            .oth_price {
                color: #666660;
                font-size: 12px;

                .value {
                    color: #1f2937;
                    font-size: 12px;
                    font-weight: 500;
                }
            }
        }

        .order-summary {
            .offer_block {
                margin-top: 0;
            }
        }

        .crm_order_after_submit {
            padding: 10px 12px;
            background: #fff;
        }

        .crm_order_after_title {
            margin-bottom: 4px;
            color: #99998f;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: .02em;
        }

        .crm_order_after_text {
            color: #666660;
            font-size: 12px;
            line-height: 1.45;
        }

        ::v-deep .order_block {
            margin-bottom: 0;
            padding: 0;
            border: 1px solid #e0dfd8;
            border-radius: 8px;
            overflow: hidden;
            background: #fff;
        }

        ::v-deep .order_block .label {
            position: static;
            margin: 0;
            padding: 8px 12px;
            border-bottom: 1px solid #e0dfd8;
            background: #f5f5f4;
            color: #1f2937;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.3;
        }

        ::v-deep .order_block .form {
            padding: 12px;
        }

        ::v-deep .ant-form-item {
            margin-bottom: 10px;
        }

        ::v-deep .ant-form-item-label {
            line-height: 1.35;
        }

        ::v-deep .ant-form-item-label > label {
            color: #666660;
            font-size: 11px;
        }

        ::v-deep .product_list.table_bordered {
            border: 1px solid #e0dfd8;
            border-radius: 6px;
            overflow: hidden;
        }

        ::v-deep .header_labels {
            top: 0;
            background: #f5f5f4;
            color: #99998f;
            font-size: 10px;
            font-weight: 600;
        }

        ::v-deep .table_header_cell {
            border-color: #e0dfd8;
            background: #f5f5f4;
            padding: 6px 8px;
        }

        ::v-deep .order_p_item {
            border-bottom: 1px solid #e0dfd8;
            background: #fff;
        }

        ::v-deep .crm_order_product_row {
            align-items: stretch;
            min-height: 92px;
        }

        ::v-deep .order_p_item:last-child {
            border-bottom: none;
        }

        ::v-deep .table_data_cell {
            border-color: #e0dfd8;
            padding: 8px;
            font-size: 12px;
        }

        ::v-deep .crm_order_product_row .table_data_cell {
            min-height: 92px;
            padding: 9px 8px;
        }

        ::v-deep .crm_order_product_row .cart_info {
            display: flex;
            align-items: center;
            height: 100%;
        }

        ::v-deep .cart_info h3 {
            margin-bottom: 2px;
            color: #1f2937;
            font-size: 12px;
            font-weight: 600;
        }

        ::v-deep .crm_order_cart_warehouse {
            margin-top: 6px;
        }

        ::v-deep .custom_article,
        ::v-deep .cart_warehouse {
            color: #8c8c85;
            font-size: 10px;
        }

        ::v-deep .crm_order_product_row .price,
        ::v-deep .crm_order_product_row .count,
        ::v-deep .crm_order_product_row .price_end {
            align-items: center;
        }

        ::v-deep .crm_order_product_row .count .max-w-full {
            width: 100%;
        }

        ::v-deep .crm_order_product_row .count_input {
            width: 100%;
            justify-content: center;
        }

        ::v-deep .crm_order_product_row .count_input .ant-input-number {
            width: 82px;
            max-width: 82px;
        }

        ::v-deep .crm_order_product_row .crm_compact_quantity {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
        }

        ::v-deep .crm_order_product_row .crm_compact_quantity .ant-input-number {
            width: 88px;
            max-width: 88px;
        }

        ::v-deep .crm_order_product_row .crm_compact_quantity .ant-input-number-input {
            height: 28px;
            text-align: center;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 4px;
            margin-top: 6px;
            justify-content: center;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form .form_field {
            margin: 0;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form .ant-form-item-label {
            display: none;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form .ant-form-item-control {
            line-height: 24px;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form .ant-select-selection,
        ::v-deep .crm_order_product_row .crm_order_quantity_form .ant-input,
        ::v-deep .crm_order_product_row .crm_order_quantity_form .field_width {
            height: 24px;
            font-size: 11px;
        }

        ::v-deep .crm_order_product_row .crm_order_quantity_form .ant-select-selection__rendered {
            line-height: 22px;
        }

        ::v-deep .count_input .c_btn {
            border-radius: 5px;
        }
    }

    @media(max-width: 1180px) {
        .crm_order_page {
            .crm_order_customer_bridge {
                grid-template-columns: minmax(0, 1fr);
            }

            .crm_order_body {
                grid-template-columns: minmax(0, 1fr);
            }

            .order_aside {
                position: static;
            }
        }
    }

    @media(max-width: 760px) {
        .crm_order_page {
            .crm_order_process {
                padding: 8px 10px;
            }

            .crm_order_step {
                min-width: 96px;
                flex: 0 0 auto;
            }

            .crm_order_body {
                padding: 8px;
            }

            .crm_order_extra_grid,
            .crm_order_payment_row {
                grid-template-columns: minmax(0, 1fr);
            }

            .crm_order_source_strip {
                margin: 8px 8px 0;
                align-items: flex-start;
                flex-direction: column;
            }
        }
    }
</style>
