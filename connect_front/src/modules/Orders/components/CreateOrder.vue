<template>
    <a-drawer
        title="Оформление заказа"
        placement="right"
        class="order_drawer"
        :width="windowWidth > 900 ? 900 : '100%'"
        :visible="visible"
        :zIndex="1100"
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div class="drawer_body" ref="orderBody">
            <a-form-model
                ref="orderForm"
                :model="form"
                :rules="rules">
                <div class="order_block">
                    <div class="label">
                        <a-icon type="file-text" class="icon" />
                        Тип заказа
                    </div>
                    <div class="form">
                        <a-form-model-item 
                            ref="contractor" 
                            label="Контрагент"
                            class="form_item"
                            prop="contractor">
                            <a-select 
                                size="large"
                                :getPopupContainer="getPopupContainer"
                                v-model="form.contractor">
                                <a-select-option value="jack">
                                    Jack
                                </a-select-option>
                                <a-select-option value="lucy">
                                    Lucy
                                </a-select-option>
                                <a-select-option value="disabled" disabled>
                                    Disabled
                                </a-select-option>
                                <a-select-option value="Yiminghe">
                                    yiminghe
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item 
                            ref="contract" 
                            label="Соглашение"
                            class="form_item"
                            prop="contract">
                            <a-select 
                                size="large"
                                :getPopupContainer="getPopupContainer"
                                v-model="form.contract">
                                <a-select-option value="jack">
                                    Jack
                                </a-select-option>
                                <a-select-option value="lucy">
                                    Lucy
                                </a-select-option>
                                <a-select-option value="disabled" disabled>
                                    Disabled
                                </a-select-option>
                                <a-select-option value="Yiminghe">
                                    yiminghe
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                </div>
                <div class="order_block">
                    <div class="label">
                        <a-icon type="environment" class="icon" />
                        Доставка
                    </div>
                    <div class="form">
                        <a-form-model-item 
                            ref="delivery_address" 
                            label="Адрес"
                            class="form_item"
                            prop="delivery_address">
                            <a-select 
                                size="large"
                                :getPopupContainer="getPopupContainer"
                                v-model="form.delivery_address">
                                <a-select-option value="jack">
                                    Jack
                                </a-select-option>
                                <a-select-option value="lucy">
                                    Lucy
                                </a-select-option>
                                <a-select-option value="disabled" disabled>
                                    Disabled
                                </a-select-option>
                                <a-select-option value="Yiminghe">
                                    yiminghe
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                </div>
                <div class="order_block">
                    <div class="label">
                        <a-icon type="user" class="icon" />
                        Покупатель
                    </div>
                    <div class="form">
                        <a-form-model-item 
                            ref="comment" 
                            label="Комментарии к заказу"
                            class="form_item"
                            prop="comment">
                            <a-textarea
                                v-model="form.comment"
                                size="large" 
                                :auto-size="{ minRows: 3, maxRows: 7 }"/>
                        </a-form-model-item>
                    </div>
                </div>
            </a-form-model>
        </div>
        <div class="drawer_footer flex justify-between">
            <div></div>
            <div>
                <div class="cart_summary_item summary flex items-baseline">
                    <div class="label">
                        Сумма заказа
                    </div>
                    <div class="val">
                        {{ cartAmount }}  <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                    </div>
                </div>
                <div class="mt-4 actions_btn flex justify-end">
                    <a-button 
                        size="large"
                        class="px-8"
                        type="primary"
                        :loading="loading"
                        @click="onSubmit()">
                        Оформить заказ
                    </a-button>
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
import { priceFormatter } from '@/utils'
import eventBus from '@/utils/eventBus.js'
export default {
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            createVisible: state => state.orders.createVisible,
            cartCurrency: state => state.orders.cartCurrency,
            cartList: state => state.orders.cartList
        }),
        visible: {
            get() {
                return this.createVisible
            },
            set(val) {
                this.$store.commit('orders/SET_CREATE_VISIBLE', val)
            }
        },
        cartAmount() {
            return priceFormatter(this.cartList.amount)
        }
    },
    data() {
        return {
            form: {
                comment: '',
                delivery_address: null,
                contractor: null,
                contract: null
            },
            rules: {

            },
            loading: false
        }
    },
    methods: {
        clear() {
            this.form = {
                comment: '',
                delivery_address: null,
                contractor: null,
                contract: null
            }
        },
        getPopupContainer() {
            return this.$refs['orderBody']
        },
        onSubmit() {
            this.$refs.orderForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const data = await this.$store.dispatch('orders/createOrder', this.form)
                        if(data) {
                            this.$message.info('Ваш заказ создан')
                            this.$router.push({query: {order: data.id}})
                            eventBus.$emit('update_order_list')
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.loading = false
                    }
                } else {
                    console.log('error submit!!')
                    return false
                }
            })
        },
        afterVisibleChange() {

        }
    }
}
</script>

<style lang="scss">
.order_drawer{
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
}
</style>

<style lang="scss" scoped>
.order_drawer{
    .order_block{
        border: 1px solid var(--border2);
        position: relative;
        padding: 30px;
        border-radius: var(--borderRadius);
        .form_item{
            &:last-child{
                margin-bottom: 0px;
            }
        }
        .label{
            font-weight: 600;
            font-size: 17px;
            background: #fff;
            padding: 0 10px;
            position: absolute;
            top: 0;
            left: 20px;
            z-index: 1;
            line-height: 18px;
            margin-top: -9px;
            color: #000;
            display: flex;
            align-items: center;
            .icon{
                margin-right: 10px;
                color: var(--blue);
            }
        }
        &:not(:last-child){
            margin-bottom: 30px;
        }
    }
    .drawer_footer{
        border-top: 1px solid var(--border2);
        padding: 20px;
        height: 128px;
        .cart_summary_item{
            .label{
                margin-right: 15px;
            }
            .val{
                font-size: 20px;
                font-weight: 600;
            }
        }
    }
    .drawer_body{
        height: calc(100% - 128px);
        overflow-x: hidden;
        overflow-y: auto;
        padding: 30px 20px;
    }
}
</style>