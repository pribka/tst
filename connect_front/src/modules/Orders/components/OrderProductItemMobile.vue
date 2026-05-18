<template>
    <a-card class="order_p_item warehouse_select">
        <div class="flex items-center">
            {{goods.number || itemNumber}}
        </div>
        <div class="flex items-start">
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
                        :data-src="require('../assets/noimage_product.svg')"
                        class="lazyload"
                        :alt="goods.name" />
                </div>
            </div>
            <div class="cart_info w-full">
                <div class="w-full cursor-pointer">
                    <h3 @click="openDetailt()">
                        {{ goods.name }}
                    </h3>
                    <div v-if="checkDelete">
                        <a-button 
                            class="ant-btn-icon-only" 
                            ghost
                            type="danger"
                            @click="deleteItem(item)">
                            <i class="fi fi-rr-trash"></i>
                        </a-button>
                    </div>
                    <template v-if="disabled">
                        <div 
                            v-if="checkStock && warehouse" 
                            class="cart_warehouse">
                            Склад: {{ warehouse.name }}
                        </div>
                    </template>
                    <div v-else class="mt-5">
                        <!--<a-form-model-item
                            label="Склад:"
                            class="custom_article max-w-[300px] mb-2">
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
                        </a-form-model-item>-->
                    </div>
                    <div class="article mt-1">
                        <span v-if="goods.article_number">
                            Арт. {{ goods.article_number }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        <div class="price mt-1">
            Цена: 
            <template v-if="cartPriceEdit && user && user.has_full_access_to_order_editing">
                <template v-if="priceEdit">
                    <PriceEditor
                        ref="price_editor"
                        :changeCount="changeCount"
                        :oldPrice="item.goods.price"
                        :showEditPrice="showEditPrice"
                        storeList="orderList"
                        :updateQuantityItems="updateQuantityItems"
                        :setOrderFormCalculated="setOrderFormCalculated"
                        :goods="item" />
                </template>
                <span 
                    v-else 
                    @click="showEditPrice()">
                    {{ price }}
                    <a-button 
                        icon="edit" 
                        type="link" 
                        size="small" />
                </span>
            </template>
            <template v-else>
                {{ price }}
            </template>
        </div>
        <div class="count mt-1">
            Кол-во: 
            <div v-if="cartEdit">
                <div
                    v-if="crmDirectOrder"
                    class="crm_compact_quantity">
                    <a-input-number
                        :value="count"
                        size="small"
                        :min="1"
                        :max="goods.available_count"
                        :formatter="plainCountFormatter"
                        @change="countInputChange"
                        @blur="inputBlur" />
                </div>
                <div v-else class="count_input flex items-center">
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
                        :min="1" 
                        :max="goods.available_count"
                        :formatter="countFormatter"
                        @change="countInputChange"
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
                <template v-if="warehouseFormInfo && Object.keys(warehouseFormInfo).length && !crmDirectOrder">
                    <WarehouseForm
                        :ref="`form_${goods.id}`"
                        :uniqKey="goods.id"
                        inputSize="small"
                        :inlineForm="false"
                        :checkRules="false"
                        :count="count"
                        :inputBlur="inputBlur"
                        :countInputChange="countInputChange"
                        :smallForm="true"
                        :changeCount="changeCount"
                        :defaultValues="item"
                        :actionId="goods.id"
                        :liveUpdate="true"
                        :updateInjectQuantity="updateInjectQuantity"
                        :setOrderFormCalculated="setOrderFormCalculated"
                        class="mt-2" />
                </template>
            </div>
            <template v-else>
                {{ item.quantity }}
            </template>
        </div>
        <div 
            v-if="widgetData.nds_column" 
            class="count mt-1">
            НДС: {{ item.amount_nds }}
        </div>
        <div class="price_end mt-1 font-semibold">
            Сумма: {{ quantityItems }}
        </div>
    </a-card>
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
        setOrderLoader: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        deleteItem: {
            type: Function,
            default: () => {}
        },
        showPrintForm: {
            type: Boolean,
            default: false
        },
        crmDirectOrder: {
            type: Boolean,
            default: false
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },

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
            priceEdit: false,
            injectQuantity: 0,
            warehouseList: [],
            warehouseSelected: null
        }
    },
    created() {
        this.$nextTick(() => {
            this.updateQuantityItems()
        })

        if(this.warehouse?.name)
            this.warehouseSelected = this.warehouse.name
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.warehouse_select')
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

            if(this.goods.price?.length && this.injectQuantity)
                value = value * this.injectQuantity

            this.quantityItems = priceFormatter(value)
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
        countFormatter(value) {
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
            this.count = value
            this.setOrderFormCalculated(false)
        },
        plus() {
            this.setOrderFormCalculated(false)
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
                time = setTimeout(async () => {
                    try {
                        if(this.edit || this.crmDirectOrder) {
                            this.$store.commit('orders/ORDER_GOODS_UPDATE_COUNT', {
                                goods: this.item,
                                quantity: this.count,
                            })
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
    grid-template-columns: 50px 1fr 120px 120px 120px 120px;
    &:not(:last-child){
        margin-bottom: 15px;
        border-bottom: 1px solid var(--border2);
    }
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
    }
}
</style>
