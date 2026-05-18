<template>
    <div
        :class="[widgetData.nds_column ? 'grid-cols-[40px,1fr,120px,120px,100px,120px]' : 'grid-cols-[40px,1fr,120px,120px,120px]', compactOrderForm && 'crm_order_product_row']"
        :style="compactOrderForm ? crmOrderGridStyle : null"
        class="warehouse_select order_p_item table_row grid">
        <div class="table_data_cell flex items-center justify-center">
            <div class="flex flex-col items-center justify-center">
                {{goods.number || itemNumber}}
                <a-checkbox v-if="edit" @change="checkBoxOnChange" :value="item.id" />
            </div>
        </div>
        <!-- <div class="table_data_cell article flex items-start justify-center">
            <span v-if="goods.article_number">
                {{ goods.article_number }}
            </span>
        </div> -->
        <div class="table_data_cell flex items-start">
            <!-- <div
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
                        :data-src="require('../assets/noimage_product.svg')"
                        class="lazyload"
                        :alt="goods.name" />
                </div>
            </div> -->
            <div class="cart_info w-full">
                <div class="w-full cursor-pointer">
                    <h3 @click="openDetailt()">
                        {{ goods.name }}
                    </h3>
                    <span
                        v-if="goods.article_number"
                        class="custom_article">
                        АРТ.{{ goods.article_number }}
                    </span>
                    <div
                        :class="compactOrderForm ? 'cart_warehouse crm_order_cart_warehouse' : 'cart_warehouse mt-5'">
                        Склад: {{ warehouse.name }}
                    </div>
                    <!-- <div v-show="!hideWarehouse">
                        <div
                            v-if="disabled"
                            class="cart_warehouse mt-5">
                            Склад: {{ warehouse.name }}
                        </div>
                        <div v-else class="mt-5">
                            <a-form-model-item
                                label="Склад:"
                                class="custom_article max-w-[300px]" >
                                <a-select
                                    v-model="warehouseSelected"
                                    size="small"
                                    :disabled="!user.warehouse_select_is_available"
                                    :not-found-content="null"
                                    :loading="warehouseLoader"
                                    :getPopupContainer="getPopupContainer"
                                    @dropdownVisibleChange="dropdownVisibleChange"
                                    @change="changeWarehouse(warehouseSelected, goods)">
                                    <a-select-option
                                        v-for="item in warehouseList"
                                        :value="item.id"
                                        :key="item.id">
                                        {{ item.name }}
                                    </a-select-option>
                                </a-select>
                            </a-form-model-item>
                        </div>
                    </div> -->
                    <a-form-model-item 
                        v-if="showPrintForm && user.has_full_access_to_order_editing" 
                        label="Печатная форма"
                        class="mt-5">
                        <div class="flex flex-row">
                            <div 
                                class="ant-input cursor-pointer truncate max-w-[300px] flex items-center" 
                                @click="openProductDrawer()">
                                <span class="truncate mr-2">{{ goodsForPrintName }}</span>
                                <a-icon 
                                    v-if="changeCountLoader" 
                                    type="loading" />
                                <i 
                                    v-else 
                                    class="fi fi-rr-edit blue_color" />
                            </div>
                            <component 
                                :is="productDrawer" 
                                :addProduct="addProduct"
                                :embdedCheckStock="false"
                                addText="Выбрать"
                                :createEmptyOrder="false"
                                page_name="catalogs.goodsmodel_list_page_select"
                                ref="productDrawer" />
                            <a-tooltip>
                                <template slot="title">
                                    Применить ко всем
                                </template>
                                <a-button
                                    icon="sync"
                                    class="ml-2"
                                    @click="setGoodsForPrintToAll"/>
                            </a-tooltip>
                        </div>
                        </a-form-model-item>
                    <div v-if="checkDelete">
                        <a-button 
                            class="ant-btn-icon-only"
                            ghost
                            type="danger"
                            @click="deleteItem(item)">
                            <i class="fi fi-rr-trash"></i>
                        </a-button>
                    </div>
                </div>
            </div>
        </div>
        <div class="table_data_cell price flex items-center justify-center">
            <template v-if="cartPriceEdit && user && user.has_full_access_to_order_editing">
                <PriceEditor
                    ref="price_editor"
                    :changeCount="changeCount"
                    :oldPrice="item.goods.price"
                    :showEditPrice="showEditPrice"
                    storeList="orderList"
                    :inlineForm="false"
                    :updateQuantityItems="updateQuantityItems"
                    :setOrderFormCalculated="setOrderFormCalculated"
                    :goods="item" />

            </template>
            <template v-else>
                {{ price }} {{ goods.currency.icon }}
            </template>
        </div>
        <div class="table_data_cell count flex items-center justify-center">
            <div
                v-if="cartEdit"
                class="max-w-full">
                <div
                    v-if="compactOrderForm"
                    class="crm_compact_quantity">
                    <a-input-number
                        v-if="!disabled"
                        :value="count"
                        size="small"
                        :min="min_count()"
                        :max="max_count()"
                        :formatter="plainCountFormatter"
                        :parser="countParser"
                        @change="countInputChange"
                        @pressEnter="inputBlur"
                        @blur="inputBlur" />
                    <span v-else>{{ plainCountFormatter(count) }}</span>
                </div>
                <div v-else-if="!disabled" class="count_input flex items-center">
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
                        :value="count"
                        size="small"
                        :min="min_count()"
                        :max="max_count()"
                        :precision=3
                        :formatter="countFormatter"
                        :parser="countParser"
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
                <div v-else class="flex justify-center">
                    {{ count }}
                </div>
                <template v-if="warehouseFormInfo && Object.keys(warehouseFormInfo).length && !compactOrderForm">
                    <WarehouseForm
                        :ref="`form_${goods.id}`"
                        :uniqKey="goods.id"
                        inputSize="small"
                        :inlineForm="compactOrderForm"
                        :checkRules="false"
                        :count="count"
                        :inputBlur="inputBlur"
                        :countInputChange="countInputChange"
                        :smallForm="true"
                        :changeCount="changeCount"
                        :defaultValues="item"
                        :actionId="goods.id"
                        :liveUpdate="true"
                        :edit="edit"
                        :setOrderFormCalculated="setOrderFormCalculated"
                        :updateInjectQuantity="updateInjectQuantity"
                        :class="compactOrderForm ? 'crm_order_quantity_form' : 'mt-2'" />
                </template>
            </div>
            <template v-else>
                {{ item.quantity }}
            </template>
        </div>
        <div
            v-if="widgetData.nds_column"
            class="table_data_cell count flex items-center justify-center">
            {{ item.amount_nds }}
        </div>
        <div class="table_data_cell price_end flex items-center justify-center font-semibold flex-wrap content-center">
            <!-- Нужна консультация. Так будет выводиться quantityItems, но в ПРСТ нужно выводить закомиченый кусок,
            т.к. там нет возможности редактировать товар в табчасти. А в ЦОТН нужно оставить так, т.к. там она есть. -->
            <template>
                {{ quantityItems }}
            </template>
            <!-- <template v-if="item.amount_no_discount">
                <template v-if="item.amount_no_discount === item.amount">
                    {{ item.amount }}
                </template>
                <template v-else>
                    <div class="old_sum line-through mb-1">
                        {{ item.amount_no_discount }}
                    </div>
                    <div class="new_sum">
                        {{ item.amount }}
                    </div>
                </template>
            </template>
            <template v-else>
                {{ quantityItems }}
            </template> -->
        </div>
    </div>
</template>

<script>
let time;
import 'lazysizes'
import { priceFormatter } from '@/utils'
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
export default {
    components: {
        WarehouseForm: () => import('./WarehouseForm'),
        PriceEditor: () => import('./PriceEditor.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        reloadAmount: {
            type: Function,
            default: () => {}
        },
        itemNumber: {
            type: Number,
            default: null
        },
        widgetData: {
            type: Object,
            required: true
        },
        compactOrderForm: {
            type: Boolean,
            default: false
        },
        markedWarehouse: {
            type: Object,
            required: true
        },
        setOrderLoader: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        hideWarehouse: {
            type: Boolean,
            default: false
        },
        deleteItem: {
            type: Function,
            default: () => {}
        }, 
        checkBoxOnChange: {
            type: Function,
            default: () => {}
        },
        crmDirectOrder: {
            type: Boolean,
            default: false
        },
        showPrintForm: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            warehouseFormInfo: state => state.orders.warehouseFormInfo,
            user: state => state.user.user,
            cartList: state => state.orders.orderList
        }),
        checkDelete() {
            return this.cartList?.results?.length > 1 ? true : false
        },
        crmOrderGridStyle() {
            if(this.widgetData?.nds_column) {
                return {
                    gridTemplateColumns: '40px minmax(300px, 1fr) 130px 190px 110px 130px'
                }
            }
            return {
                gridTemplateColumns: '40px minmax(300px, 1fr) 130px 190px 130px'
            }
        },
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
        config() {
            return this.$store.state.config.config
        },
        cartEdit() {
            if(this.config?.order_setting?.orderCartEdit)
                return true
            else
                return false
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
        disabled() {
            return !this.$store.state.user.user.has_full_access_to_order_editing
        },
        productDrawer() {
            return () => import('@apps/Products/ProductDrawer.vue')
        },
        cartDecimalCount() {
            return this.config?.order_setting?.cartDecimalCount
        },
        remnantControl() {
            if(this.config?.order_setting?.remnant_control)
                return true
            else
                return false
        },
        goodsForPrintName() {
            if(this.item.goods_for_print) {
                return this.item.goods_for_print.name ? this.item.goods_for_print.name : this.item.goods_for_print.goods.name
            } else {
                return this.goods.name ? this.goods.name : this.goods.goods.name
            }
        }
    },
    data() {
        return {
            count: Number(JSON.stringify(JSON.parse(this.item.quantity))),
            deleteLoader: false,
            plusLoader: false,
            minusLoader: false,
            minusDelLoader: false,
            warehouseLoader: false,
            quantityItems: '',
            quantity: null,
            priceEdit: false,
            injectQuantity: 0,
            warehouseList: [],
            warehouseSelected: null,
            changeCountLoader: false
        }
    },
    created() {
        this.$nextTick(() => {
            this.updateQuantityItems()
        })
        this.warehouseSelected = this.warehouse.name
    },
    watch: {
        'markedWarehouse'() {
            this.warehouseSelected = this.markedWarehouse.name
        }
    },
    methods: {
        setGoodsForPrintToAll() {
            let goodsForPrint = {}

            if(this.item.goods_for_print) {
                goodsForPrint = this.item.goods_for_print || this.item.goods_for_print.goods
            } else {
                goodsForPrint = this.goods || this.goods.goods
            }

            this.$store.commit('orders/SET_GOODG_FOR_PRINT_TO_ALL', goodsForPrint)
        },
        max_count() {
            return this.remnantControl ? this.goods.available_count : undefined
        },
        min_count() {
            return this.cartDecimalCount ? 0 : 1
        },
        getPopupContainer() {
            return document.querySelector('.warehouse_select')
        },
        addProduct({ goods }) {
            if(goods) {
                if(this.edit) {
                    this.$store.commit('orders/ORDER_CART_UPDATE_FIELD', {
                        goods: this.item, 
                        fieldKey: 'goods_for_print', 
                        fieldValue: goods
                    })
                } else {
                    this.changeCount(null, {goods_for_print: goods.id})
                }
                this.openProductDrawer()
            }
        },
        openProductDrawer() {
            this.$nextTick(() => {
                if(this.$refs['productDrawer']) {
                    this.$refs['productDrawer'].toggleDrawer()
                }
            })
        },
        async changeWarehouse(val, goods) {
            try {
                this.setOrderLoader(true)
                this.warehouseLoader = true

                if(this.edit || this.crmDirectOrder) {
                    const find = this.warehouseList.find(f => f.id === val)
                    if(find) {
                        this.$store.commit('orders/ORDER_CART_UPDATE_FIELD', {
                            goods: this.item, 
                            fieldKey: 'warehouse', 
                            fieldValue: find
                        })
                    }
                } else {
                    await this.$http.patch(`/crm/shopping_cart/${this.item.id}/`, { "warehouse": val })
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.warehouseLoader = false
                this.setOrderLoader(false)
            }
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
                if(this.goods.price?.length)
                    value = String(parseFloat(this.goods.price) * this.count)
                else
                    value = '0.00'
            }

            // if(this.goods.price?.length && this.injectQuantity)
            //     value = value * this.injectQuantity

            // ОСТОРОЖНО! КИРПИЧ
            // this.quantityItems = priceFormatter(value)
            if(this.cartDecimalCount) {
                this.quantityItems = Number(value).toFixed(2)
            } else {
                this.quantityItems = Number(value).toFixed(0)
            }
        },
        inputBlur() {
            this.updateQuantityItems()
            this.changeCount()
        },
        openDetailt() {
            let query = Object.assign({}, this.$route.query)

            if(!query?.viewGoods || query.viewGoods !== this.goods.id) {
                query.viewGoods = this.goods.id
                this.$router.push({query})
            }
        },
        async summaryUpdate() {
            try {
                await this.$store.dispatch('orders/getCartSummary')
            } catch(e) {
                console.log(e)
            }
        },
        countParser(value) {
            value = value.replace(/[^0-9.,]/g, "")
            value = value.replace(',', '.')
            if(this.cartDecimalCount) {
                const integerPart = value.toString().split('.')[0] || '0'
                const decimalPart = value.toString().split('.')[1] || ''
                if (decimalPart.length > 3)
                    return `${integerPart}.${decimalPart.slice(0, 3)}`
                return value
            } else {
                if(Number(value) < 1)
                    value = 1
                return Number(value).toFixed(0)
            }
        },
        countFormatter(value) {
            if(!this.remnantControl) {
                return value
            }
            if(this.goods.available_count) {
                if(value >= this.goods.available_count)
                    return this.goods.available_count
                else
                    return value
            } else
                return value
        },
        plainCountFormatter(value) {
            if(value === null || value === undefined || value === '') {
                return ''
            }
            const normalized = String(value).replace(',', '.')
            const numberValue = Number(normalized)
            if(!Number.isFinite(numberValue)) {
                return value
            }
            return String(numberValue)
        },
        countInputChange(value) {
            if(!this.cartDecimalCount)
                value = Math.round(value)
            this.count = value
            this.setOrderFormCalculated(false)
        },
        plus() {
            this.setOrderFormCalculated(false)
            if(!this.remnantControl) {
                this.count += 1
                this.updateQuantityItems()
                this.changeCount('plusLoader')
            } else {
                if(this.goods.available_count) {
                    if(this.count < this.goods.available_count) {
                        if((this.count + 1) < this.goods.available_count)
                            this.count += 1
                        else
                            this.count = this.goods.available_count
                        this.updateQuantityItems()
                        this.changeCount('plusLoader')
                    }
                } else {
                    this.count += 1
                    this.updateQuantityItems()
                    this.changeCount('plusLoader')
                }
            }
        },
        async minus() {
            this.setOrderFormCalculated(false)
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
            clearTimeout(time)

            if(!this.minusDelLoader) {
                if(this.edit || this.crmDirectOrder) {
                    this.updateQuantityItems()
                    this.$store.commit('orders/ORDER_GOODS_UPDATE_COUNT', {
                        goods: this.item,
                        quantity: this.count,
                    })
                }

                time = setTimeout(async () => {
                    try {
                        this.changeCountLoader = true
                        if(this.edit || this.crmDirectOrder) {
                            eventBus.$emit('edit_update_price')
                        } else {
                            await this.$store.dispatch('orders/cartCountUpdate', {
                                goods: this.item,
                                quantity: this.count,
                                formData
                            })

                            this.reloadAmount()
                            this.$nextTick(() => {
                                if(this.$refs['price_editor']) {
                                    this.$refs['price_editor'].updateStartPrice()
                                }
                            })
                            eventBus.$emit('update_cart_count')
                        }
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
                        this.changeCountLoader = false
                    }
                }, 1000)
            }
        },
        dropdownVisibleChange(val) {
            if(val) {
                this.getWarehouseList()
            }
        },
        async getWarehouseList() {
            try {
                this.warehouseLoader = true
                const { data } = await this.$http.get("/catalogs/warehouses/")
                if(data.results) {
                    this.warehouseList = data.results
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.warehouseLoader = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.order_p_item{
    .cart_warehouse{
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
    h3{
        font-size: 14px;
        transition: all 0.3s color;
        line-height: 20px;
        padding-right: 10px;
        word-break: break-word;
        -webkit-hyphens: auto;
        -ms-hyphens: auto;
        hyphens: auto;
        font-weight: 400;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        &:hover{
            color: var(--blue);
        }
    }
    .img{
        width: 60px;
        height: 60px;
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
    .price_start{
        .price{
            font-weight: 600;
            min-width: 160px;
        }
    }
    .price_end{
        font-weight: 600;
        .old_sum{
            font-weight: 400;
            color: rgba(0, 0, 0, 0.45);
        }
    }
}

.table_data_cell {
    padding: 5px 5px;

    &:not(:last-child) {
        border-right: 1px solid var(--border2);
    }
}
.table_row {
    &:not(:last-child) {
        border-bottom: 1px solid var(--border2);
    }
}
</style>

<style>
.table_data_cell .count_input .ant-input-number {
    flex-grow: 1;
    max-width: max-content;
}
</style>
