<template>
    <div class="cart_item">
        <div class="cart_content w-full">
            <div
                v-if="itemNumber"
                class="cart_item_number mr-3">
                {{ itemNumber }}.
            </div>
            <div
                v-if="goods.image"
                class="img"
                @click="openDetailt()">
                <div class="img_wrap">
                    <img
                        v-if="goods.image"
                        :data-src="goods.image"
                        class="lazyload"
                        :alt="goods.name" />
                    <img
                        v-else
                        :data-src="require('../../assets/noimage_product.svg')"
                        class="lazyload"
                        :alt="goods.name" />
                </div>
            </div>
            <div class="cart_info w-full">
                <div class="w-full">
                    <h3 @click="openDetailt()">
                        {{ goods.name }}
                    </h3>
                    <div
                        v-if="checkStock && warehouse"
                        class="cart_warehouse">
                        Склад: {{ warehouse.name }}
                    </div>
                    <div class="custom_article cart_article mt-1">
                        {{ goods.article_number }}
                    </div>
                    <div class="price_info flex items-center justify-between mt-3 w-full">
                        <template v-if="!remnantControl || goods.available_count">
                            <div class="w-full grid grid-cols-3 gap-3 flex items-center">
                                <div class="price_start price">
                                    <template v-if="cartPriceEdit && user && user.has_full_access_to_order_editing">
                                        <div class="font-normal price_info_label mb-2">
                                            цена<span v-if="goods.default_price_currency"> в {{ goods.default_price_currency }}.</span>:
                                        </div>
                                        <PriceEditor
                                            ref="price_editor"
                                            :changeCount="changeCount"
                                            :oldPrice="item.goods.price"
                                            :inlineForm="false"
                                            :showEditPrice="showEditPrice"
                                            :updateQuantityItems="updateQuantityItems"
                                            :goods="item"/>

                                    </template>
                                    <template v-else>
                                        <div class="font-normal price_info_label mb-2">
                                            цена<span v-if="goods.default_price_currency"> в {{ goods.default_price_currency }}.</span>:
                                        </div>
                                        {{ price }} {{ goods.currency.icon }}
                                    </template>
                                </div>
                                <div class="count">
                                    <div class="mb-2 price_info_label">
                                        кол-во<span v-if="item.measure_unit"> в {{ item.measure_unit.name_short }}</span>:
                                    </div>

                                    <div v-if="cartCountEdit || user.has_full_access_to_order_editing" class="count_input flex items-center">
                                        <div
                                            class="c_btn minus"
                                            @click="minus()">
                                            <a-spin
                                                v-if="minusLoader"
                                                size="small" />
                                            <a-icon
                                                v-else
                                                type="minus" />
                                        </div>
                                        <a-input-number
                                            v-if="remnantControl"
                                            :value="count"
                                            size="small"
                                            :precision=3
                                            :min="min_count()"
                                            :max="goods.available_count"
                                            :parser="countParser"
                                            :formatter="countFormatter"
                                            @change="countInputChange"
                                            @pressEnter="inputBlur"
                                            @blur="inputBlur" />
                                        <a-input-number
                                            v-else
                                            :value="count"
                                            size="small"
                                            :precision=3
                                            :min="min_count()"
                                            :parser="countParser"
                                            :formatter="countFormatter"
                                            @change="countInputChange"
                                            @pressEnter="inputBlur"
                                            @blur="inputBlur" />
                                        <div
                                            class="c_btn plus"
                                            @click="plus()">
                                            <a-spin
                                                v-if="plusLoader"
                                                size="small" />
                                            <a-icon
                                                v-else
                                                type="plus" />
                                        </div>
                                    </div>
                                    <div v-else class="count_input flex items-center justify-center">
                                        {{ count }}
                                    </div>
                                </div>
                                <div class="price_end justify-self-start self-start">
                                    <div class="price_info_label font-normal mb-2">
                                        Стоимость<span v-if="goods.default_price_currency"> в {{ goods.default_price_currency }}.</span>:
                                    </div>
                                    {{ quantityItems }} {{ goods.currency.icon }}
                                </div>
                            </div>
                        </template>
                        <div class="available_count_empty" v-else>
                            Нет в наличии
                        </div>
                    </div>
                    <template v-if="warehouseFormInfo && Object.keys(warehouseFormInfo).length">
                        <WarehouseForm
                            :ref="`form_${goods.id}`"
                            :uniqKey="goods.id"
                            inputSize="small"
                            :checkRules="false"
                            :defaultValues="item"
                            :actionId="goods.id"
                            :smallForm="true"
                            :count="count"
                            isCart
                            :changeCount="changeCount"
                            :inputBlur="inputBlur"
                            :countInputChange="countInputChange"
                            :liveUpdate="true"
                            :updateInjectQuantity="updateInjectQuantity"
                            style="max-width: 400px;"
                            class="mt-3" />
                    </template>
                </div>
            </div>
        </div>
        <a-button
            class="item_remove text-current"
            icon="close"
            size="small"
            :loading="deleteLoader"
            type="link"
            @click="deleteCart()" />
    </div>
</template>

<script>
let time;
import 'lazysizes'
import { priceFormatter } from '@/utils'
import { mapState } from 'vuex'
export default {
    components: {
        WarehouseForm: () => import('../WarehouseForm'),
        PriceEditor: () => import('../PriceEditor.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        cartCountUpdate: {
            type: Function,
            default: () => {}
        },
        remnantControl: {
            type: Boolean,
            default: true
        },
        itemNumber: {
            type: Number,
            defalut: null
        },
        storeName: {
            type: String,
            default: 'orders'
        },
        cartTypeText: {
            type: String,
            default: 'корзины'
        },
        setUpdateLoader: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            warehouseFormInfo: state => state.orders.warehouseFormInfo,
            user: state => state.user.user,
            config: state => state.config.config
        }),
        goods() {
            return this.item.goods
        },
        price() {
            if(this.item.custom_price)
                return priceFormatter(this.item.custom_price)
            else
                return priceFormatter(this.goods.price)
        },
        warehouse() {
            if(this.item.warehouse)
                return this.item.warehouse
            else
                return null
        },
        checkStock() {
            if(this.config?.order_setting?.check_stock)
                return true
            else
                return false
        },
        checkMinusDelete() {
            if(this.config?.order_setting?.cartMinusDelete)
                return true
            else
                return false
        },
        cartPriceEdit() {
            return this.config?.order_setting?.cartPriceEdit || false
        },
        cartDecimalCount() {
            return this.config?.order_setting?.cartDecimalCount
        },
        cartCountEdit() {
            return this.config?.order_setting?.cartCountEdit || false
        }
    },
    data() {
        return {
            count: Number(JSON.stringify(JSON.parse(this.item.quantity))),
            deleteLoader: false,
            plusLoader: false,
            minusLoader: false,
            minusDelLoader: false,
            quantityItems: '',
            priceEdit: false,
            injectQuantity: 0
        }
    },
    created() {
        this.$nextTick(() => {
            this.updateQuantityItems()
        })
    },
    methods: {
        min_count() {
            return this.cartDecimalCount ? 0 : 1
        },
        showEditPrice() {
            this.priceEdit = !this.priceEdit
        },
        updateInjectQuantity(value) {
            this.injectQuantity = value
            this.updateQuantityItems()
        },
        updateQuantityItems() {
            let value = 0
            if(this.item.custom_price) {
                value = String(parseFloat(this.item.custom_price) * this.count)
            } else {
                value = String(parseFloat(this.goods.price) * this.count)
            }

            // if(this.injectQuantity)
            //     value = value * this.injectQuantity

            this.quantityItems = priceFormatter(value)
        },
        inputBlur() {
            this.updateQuantityItems()
            this.changeCount()
        },
        openDetailt() {
            this.$router.push({query: {viewGoods: this.goods.id}})
        },
        async summaryUpdate() {
            try {
                await this.$store.dispatch(`${this.storeName}/getCartSummary`)
            } catch(e) {
                console.log(e)
            }
        },
        priceFormat(price) {
            const integerPart = price.toString().split('.')[0] || '0'
            const decimalPart = price.toString().split('.')[1] || ''
            if (decimalPart.length > 3)
                return `${integerPart}.${decimalPart.slice(0, 3)}`
            return price
        },
        countParser(value) {
            value = value.replace(/[^0-9.,]/g, "")
            value = value.replace(',', '.')
            if(this.cartDecimalCount) {
                return this.priceFormat(value)
            } else {
                if(Number(value) < 1)
                    value = 1
                return Number(value).toFixed(0)
            }
        },
        countFormatter(value) {
            if(this.remnantControl && this.goods.available_count) {
                if(value >= this.goods.available_count)
                    return this.goods.available_count
                else
                    return value
            } else
                return value
        },
        countInputChange(value) {
            if(!this.cartDecimalCount)
                value = Math.round(value)
            this.count = value
        },
        plus() {
            if(this.remnantControl) {
                if(this.goods.available_count) {
                    if(this.count < this.goods.available_count) {
                        this.count += 1
                        this.updateQuantityItems()
                        this.changeCount('plusLoader')
                    }
                } else {
                    this.count += 1
                    this.changeCount('plusLoader')
                }
            } else {
                this.count += 1
                this.updateQuantityItems()
                this.changeCount('plusLoader')
            }
        },
        async minus() {
            if(this.count > 1) {
                this.count -= 1
                this.updateQuantityItems()
                this.changeCount('minusLoader')
            } else {
                if(this.checkMinusDelete) {
                    try {
                        this.minusLoader = true
                        this.minusDelLoader = true
                        this.count = 1
                        await this.deleteCart()
                        await this.cartCountUpdate()
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.minusLoader = false
                        this.minusDelLoader = false
                    }
                } else {
                    this.count = 1
                }
            }
        },
        changeCount(loader = null, formData = null) {
            this.setUpdateLoader(true)
            clearTimeout(time)

            if(!this.minusDelLoader) {
                time = setTimeout(async () => {
                    try {
                        await this.$store.dispatch(`${this.storeName}/cartCountUpdate`, {
                            goods: this.item,
                            quantity: this.count,
                            formData
                        })
                        this.cartCountUpdate()
                        this.$nextTick(() => {
                            if(this.$refs['price_editor']) {
                                this.$refs['price_editor'].updateStartPrice()
                            }
                        })
                    } catch(error) {
                        if(error?.non_field_errors?.length) {
                            error.non_field_errors.forEach(item => {
                                let message = ''
                                if(item === 'Incorrect custom_price.') {
                                    message = 'Указанная цена ниже минимально допустимой цены'
                                    this.$nextTick(() => {
                                        if(this.$refs['price_editor']) {
                                            this.$refs['price_editor'].setStartPrice()
                                        }
                                    })
                                }
                                this.$message.error(message)
                            })
                        }
                        console.log(error)
                    } finally {
                        this.setUpdateLoader(false)
                    }
                }, 1000)
            }
        },
        async deleteCart() {
            try {
                this.deleteLoader = true
                await this.$store.dispatch(`${this.storeName}/deleteProductCart`, {
                    goods: this.item,
                    count: this.count
                })
                this.cartCountUpdate()
                this.$message.info(`Товар удален из ${this.cartTypeText}`)
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка удаления товара')
            } finally {
                this.deleteLoader = false
            }
        }
    }
}
</script>

<style lang="scss">
.count_input{

    .ant-input-number {
        flex-grow: 1;
        max-width: max-content;
    }
    .ant-input-number-input{
        border-radius: 0px;
        text-align: center;
    }
    .ant-input-number-handler-wrap{
        display: none;
    }
    .ant-input-number{
        border-radius: 0px;
        // max-width: 50px;
        border-left: 0px;
        border-right: 0px;
        &:hover,
        &:focus{
            border-color: #e1e7ec;
        }
    }
    .c_btn{
        border: 1px solid #e1e7ec;
        cursor: pointer;
        padding: 0 4px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
        font-size: 12px;
        -moz-user-select: none;
        -khtml-user-select: none;
        user-select: none;
        &.plus{
            border-left: 0px;
            border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
        }
        &.minus{
            border-radius: var(--borderRadius) 0 0 var(--borderRadius);
            border-right: 0px;
        }
        &:hover{
            background: #eff2f5;
            color: var(--blue);
        }
        .ant-spin{
            display: flex;
            align-items: center;
            justify-content: center;
            .ant-spin-dot-item{
                width: 4px;
                height: 4px;
            }
            .ant-spin-dot{
                width: 10px;
                height: 10px;
            }
        }
    }
}
.cart_item{
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    position: relative;
    .cart_warehouse{
        margin-top: 5px;
        font-weight: 300;
        font-size: 14px;
    }
    .item_remove{
        position: absolute;
        top: 5px;
        right: 8px;
        z-index: 5;
        width: 20px;
        height: 20px;
        font-size: 12px;
    }
    &:hover{
        .item_remove{
            display: block;
        }
    }
    .cart_content{
        display: flex;
        align-items: flex-start;
        h3{
            font-size: 14px;
            transition: all 0.3s color;
            line-height: 20px;
            padding-right: 10px;
            word-break: break-word;
            &:hover{
                color: var(--blue);
            }
        }
        .img{
            width: 80px;
            height: 80px;
            overflow: hidden;
            border-radius: 5px;
            margin-right: 15px;
            cursor: pointer;
            position: relative;
            .img_wrap{
                margin: 0;
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            img{
                object-fit: contain;
                vertical-align: middle;
                -o-object-fit: contain;
                opacity: 0;
                transition: opacity 0.15s ease-in-out;
                max-height: 100%;
                &.lazyloaded{
                    opacity: 1;
                }
            }
        }
        .price_start.price{
                font-weight: 600;
                min-width: 160px;
        }
        .price_end{
            font-weight: 600;
        }
    }
}
</style>

<style lang="scss" scoped>
.cart_item_number {
    display: flex;
    align-items: center;
    justify-content: center;

    height: 100%;
    font-size: 1rem;
}
.available_count_empty{
    color: var(--errorRed);
}

.price_info {
    .price_info_label {
        color: rgba(0, 0, 0, 0.85);
    }
}
</style>