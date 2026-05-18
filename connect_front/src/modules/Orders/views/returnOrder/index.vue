<template>
    <div class="create_order_page pj_padding"
         :class="isMobile ? 'create_order_mobile' : 'pj_padding'">
        <div class="order_wrap">
            <h1>
                Оформление возврата
            </h1>

            <a-result
                v-if="orderEmpty"
                title="Для оформления возврата добавьте товар в корзину возврата">
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
                <template v-if="orderForm">
                    <a-spin
                        :spinning="reload"
                        size="large">
                        <div :class="isMobile || 'grid gap-5 wrap_grid'">
                            <div>
                                <a-form-model
                                    ref="orderForm"
                                    :model="form"
                                    :rules="rules">
                                    <WidgetSwitch
                                        v-for="item in orderForm.orderForm"
                                        :form="form"
                                        :changeContract="changeContract"
                                        :key="item.widget"
                                        :reload="reload"
                                        :item="item"/>
                                </a-form-model>
                            </div>
                            <div>
                                <div
                                    :class="[
                                        orderForm.aside.sticky && 'sticky', 
                                        isMobile ? 'order_aside_mobile' : 'order_aside'
                                    ]">
                                    <div class="order_summary">

                                        <a-button
                                            :type="orderForm.aside.orderButton.type"
                                            :size="orderForm.aside.orderButton.size"
                                            class="calculate_btn"
                                            block
                                            :loading="priceLoader"
                                            @click="onSubmit(0)">
                                            Рассчитать цены
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
                                                    </a-spin>
                                                </div>
                                            </div>
                                            <div 
                                                v-if="cartNds" 
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

                                    <div class="order-summary">
                                        <div
                                            v-if="orderForm.aside && orderForm.aside.offer && orderForm.aside.offer.show"
                                            class="offer_block mt-3">
                                            <a-button v-if="orderForm.calculated"
                                                      :type="orderForm.aside.orderButton.type"
                                                      :size="orderForm.aside.orderButton.size"
                                                      class="summary_btn"
                                                      block
                                                      :loading="orderLoader"
                                                      @click="onSubmit(40)">
                                                Сформировать возврат
                                                <!--{{ orderForm.aside.orderButton.btnText }}-->
                                            </a-button>
                                            <a-button v-else
                                                      :type="orderForm.aside.orderButton.type"
                                                      :size="orderForm.aside.orderButton.size"
                                                      class="summary_btn" disabled
                                                      block
                                                      :loading="orderLoader"
                                                      @click="onSubmit()">
                                                Сформировать возврат
                                                <!--{{ orderForm.aside.orderButton.btnText }}-->
                                            </a-button>
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

export default {
    components: {
        WidgetSwitch: () => import('./widgets/WidgetSwitch.vue'),
        // OrderOffer
    },
    metaInfo() {
        return {
            title: this.pageTitle
        }
    },
    computed: {
        ...mapState({
            cartCurrency: state => state.return.orderCurrency,
            cartList: state => state.return.orderList,
            firstOrderLoading: state => state.return.firstOrderLoading,
            orderEmpty: state => state.return.orderEmpty,
            config: state => state.config.config
        }),
        visible: {
            get() {
                return this.createVisible
            },
            set(val) {
                this.$store.commit('return/SET_CREATE_VISIBLE', val)
            }
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
        }
    },
    data() {
        return {
            form: {},
            rules: {},
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
            cartNds: null
        }
    },
    created() {
        this.getOrderList()
    },
    methods: {
        changeContract(val, contractList) {
            const find = contractList.find(f => f.code === val)
            if (find) {
                this.$store.commit('return/SET_CURRENT_CONTRCAT', find.id)
            }
            this.getOrderListReload()
        },
        async getOrderListReload() {
            try {
                this.reload = true
                await this.$store.dispatch('return/getOrderListReload')
                this.$message.info('Цена в заказе пересчитана в соответствии с выбранным соглашением')
            } catch (e) {
                console.log(e)
                this.reload = false
            } finally {
                this.reload = false
            }
        },
        async getOrderList() {
            if (this.cartList.next && !this.loading) {
                try {
                    this.loading = true
                    const data = await this.$store.dispatch('return/getOrderList')
                    if (data?.results?.length) {
                        this.amount = data.amount
                        await this.getForm()
                    }
                } catch (e) {
                    console.log(e)
                    this.loading = false
                } finally {
                    this.loading = false
                }
            }
        },
        async getForm() {
            try {
                const {data} = await this.$http.get('/crm/returns/form_info/')
                if (data) {
                    this.orderForm = data
                    this.form = data.orderFormData
                    this.rules = data.orderFormRules
                }
            } catch (e) {
                console.log(e)
            }
        },
        openCatalog() {
            this.$router.push({name: 'goods'})
        },
        clear() {

        },
        onSubmit(operType = 0) {
            this.$refs.orderForm.validate(async valid => {
                if (valid) {
                    try {
                        this.form.oper_type = operType

                        if(operType > 0)
                            this.orderLoader = true
                        else
                            this.priceLoader = true
                        
                        const data = await this.$store.dispatch('return/createOrder', this.form)
                        if (data) {
                            if (operType > 0) {
                                this.$message.info('Ваш заказ создан')
                                

                                if(this.orderForm?.orderSetting?.redirectType) {
                                    if(this.orderForm.orderSetting.redirectType === 'orderPage')
                                        this.$router.push({name: 'orders'})
                                    else
                                        this.$router.push({name: 'orders', query: {order: data.id}})
                                } else {
                                    this.$router.push({name: 'orders', query: {order: data.id}})
                                }

                                eventBus.$emit('update_order_list')
                            } else {
                                this.$message.info('Цены рассчитаны')
                                this.orderForm.calculated = data.calculated
                                this.amount = data.amount
                                this.noDiscount = data.amount_no_discount
                                this.cartNds = data.amount_nds

                                if(data.amount_no_discount && data.amount) {
                                    this.discountSum = Number(data.amount_no_discount) - Number(data.amount)
                                }

                                if(this.config?.order_setting?.calculate_warehouse_tp !== 'undefined') {
                                    if(this.config.order_setting.calculate_warehouse_tp)
                                        this.$store.commit('return/SET_ORDER_GOOD_LIST_ONLY_RELOAD', data.tp_goods)
                                    else
                                        this.$store.commit('return/SET_ORDER_GOOD_LIST_ONLY_RELOAD_NO_CALCULATE', data.tp_goods)
                                } else
                                    this.$store.commit('return/SET_ORDER_GOOD_LIST_ONLY_RELOAD', data.tp_goods)
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
                    console.log('error submit!!')
                    this.$message.warning('Заполните обязательные поля')
                    return false
                }
            })
        }
    },
    beforeDestroy() {
        this.$store.commit('return/CLEAR_ORDER_CREATE_PAGE')
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

        .wrap_grid {
            grid-template-columns: 1fr 290px;
        }
        .order_aside {
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
</style>