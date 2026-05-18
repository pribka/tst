<template>
    <a-modal
        :title=title
        :class="!isMobile || 'warehouse_list_mobile'"
        :visible="visible"
        :footer="null"
        :zIndex="zIndex"
        :destroyOnClose="true"
        @cancel="handleCancel"
        :afterClose="afterClose">
        <a-spin :spinning="loadingWarehouseForm">
            <div class="warehouse_list">
                <div
                    v-for="item in warehouseList"
                    :key="item.warehouse.id"
                    class="item select-none w-full">
                    <div class="w-full">
                        <div class="info">
                            <div class="name"
                                 v-show="!(item.warehouse.default_warehouse && warehouseList.length === 1)">
                                {{ item.warehouse.name }}
                            </div>
                            <div
                                v-show="item.warehouse.address && !item.warehouse.default_warehouse"
                                class="address">
                                {{ item.warehouse.address }}
                            </div>
                        </div>
                        <div>
                            <div
                                v-if="checkStockModal && item.in_cart"
                                class="mr-6 in_cart flex items-center">
                                <i class="fi fi-rr-shopping-cart-check mr-2"></i>
                                В корзине
                            </div>
                            <template v-else>
                                <div class="mb-1">Количество</div>
                                <div :class="isMobile ? 'flex-col-reverse w-full' : 'flex items-center'">
                                    <div
                                        v-if="Object.keys(selectedWarehouse).length"
                                        class="counter_input flex items-center"
                                        :class="isMobile ? 'counter_input_mobile' : 'mr-6'">
                                        <div
                                            class="btn minus"
                                            @click="minus(item.warehouse.id)">
                                            <a-icon type="minus" />
                                        </div>
                                        <a-input-number
                                            v-if="remnantControl"
                                            v-model="selectedWarehouse[item.warehouse.id]"
                                            style="width: 100%;"
                                            :min="0"
                                            :max="item.qual"
                                            :precision=3
                                            :parser="countParser"
                                            :formatter="value => countFormatter(value, item.qual)"
                                            :default-value="0"
                                            @change="changeInputCount($event, item.warehouse.id)" />
                                        <a-input-number
                                            v-else
                                            v-model="selectedWarehouse[item.warehouse.id]"
                                            style="width: 100%;"
                                            :min="0"
                                            :precision=3
                                            :parser="countParser"
                                            :formatter="value => countFormatter(value, item.qual)"
                                            :default-value="0"
                                            @change="changeInputCount($event, item.warehouse.id)" />
                                        <div
                                            class="btn plus"
                                            @click="plus(item.warehouse.id, item.qual)">
                                            <a-icon type="plus" />
                                        </div>
                                    </div>
                                    <div
                                        v-if="Object.keys(selectedWarehouse).length && cartMinAdd <= 0"
                                        class="mr-6"
                                        :class="isMobile && 'mt-2'">
                                        <a-checkbox
                                            :checked="!!selectedWarehouse[item.warehouse.id]"
                                            @change="onChange($event, item)">
                                            Выбрать
                                        </a-checkbox>
                                    </div>
                                </div>
                            </template>
                            <div
                                v-if="remnantControl"
                                class="quantity"
                                :class="!isMobile || 'mb-2'">
                                доступно: {{ item.quantity }}
                            </div>
                        </div>
                        <template v-if="warehouseFormInfo && Object.keys(warehouseFormInfo).length">
                            <WarehouseForm
                                :ref="`form_${item.warehouse.id}`"
                                :uniqKey="item.warehouse.id"
                                :warehouseId="item.warehouse.id"
                                :goods="product"
                                :count="selectedWarehouse[item.warehouse.id]"
                                :countInputChange="changeInputCount"
                                class="mt-3" />
                        </template>
                    <!--<div
                        v-if="checkQuantity(item)"
                        class="quantity_info">
                        В корзину будет добавлено {{ productCount(item.qual) }}
                    </div>-->
                    </div>
                </div>
            </div>
            <div class="flex mt-4 justify-end modal_footer">
                <a-button
                    v-if="embded"
                    icon="plus"
                    type="primary"
                    :block="isMobile"
                    size="large"
                    class="px-8"
                    :disabled="btnDisabled"
                    :loading="loading"
                    @click="addWarehouseCart()">
                    Добавить
                </a-button>
                <a-button
                    v-else
                    icon="shopping-cart"
                    type="primary"
                    :block="isMobile"
                    size="large"
                    class="px-8"
                    :disabled="btnDisabled"
                    :loading="loading"
                    @click="addWarehouseCart()">
                    В корзину
                </a-button>
            </div>
        </a-spin>
    </a-modal>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { mapState } from 'vuex'
import warehouse from '@apps/Orders/mixins/warehouse'
import WarehouseForm from '@apps/Orders/components/WarehouseForm'
export default {
    components: {
        WarehouseForm
    },
    props: {
        product: {
            type: Object,
            required: true
        },
        visible: {
            type: Boolean,
            default: false
        },
        handleCancel: {
            type: Function,
            default: () => {}
        },
        count: {
            type: Number,
            default: 1
        },
        warehouseList: {
            type: Array,
            default: () => []
        },
        addCartWarehouse: {
            type: Function,
            default: () => {}
        },
        loading: {
            type: Boolean,
            default: false
        },
        changeCount: {
            type: Function,
            default: () => {}
        },
        zIndex: {
            type: Number,
            default: 1000
        },
        embded: {
            type: Boolean,
            default: false
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        }
    },
    mixins: [
        warehouse
    ],
    computed: {
        ...mapState({
            config: state => state.config.config,
            cart: state => state.orders?.cartList?.results,
            warehouseFormInfo: state => state.orders.warehouseFormInfo
        }),
        title() {
            return (this.warehouseList.length === 1 && this.warehouseList[0].warehouse.default_warehouse) ? '' : 'Склад'
        },
        cartMinAdd() {
            if(this.config?.order_setting?.min_product_count === 0)
                return this.config.order_setting.min_product_count
            else
                return 1
        },
        remnantControl() {
            if(this.config?.order_setting?.remnant_control)
                return true
            else
                return false
        },
        checkStockModal() {
            if (this.config?.order_setting?.check_stock_modal)
                return true
            else
                return false
        },
        btnDisabled() {
            if(this.selectedWarehouse && Object.values(this.selectedWarehouse)?.length) {
                const values = Object.values(this.selectedWarehouse).reduce(function(accumulator, currentValue) {
                    return accumulator + currentValue
                })
                if(values)
                    return false
                else
                    return true
            } else
                return false
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        cartDecimalCount() {
            return this.config?.order_setting?.cartDecimalCount
        },
    },
    data() {
        return {
            selectWarehouse: null,
            selectedWarehouse: {},
            loadingForm: false
        }
    },
    watch: {
        visible(val) {
            if(val && this.warehouseList?.length) {
                this.getWarehouseFormInfo()
                let newCount = Number(JSON.parse(JSON.stringify(this.count)))

                this.warehouseList.forEach((item, index) => {
                    let cnt = newCount
                    if(cnt > item.qual)
                        cnt = item.qual

                    if(this.cartMinAdd > 0)
                        this.$set(this.selectedWarehouse, item.warehouse.id, cnt)
                    else
                        this.$set(this.selectedWarehouse, item.warehouse.id, 0)

                    if(this.warehouseList?.length === 1)
                        this.$set(this.selectedWarehouse, item.warehouse.id, 1)


                    newCount = newCount - item.qual
                    if(newCount < 0)
                        newCount = 0

                    if(index === 0) {
                        this.$set(this.selectedWarehouse, item.warehouse.id, Number(JSON.parse(JSON.stringify(this.count))))
                    } else {
                        this.$set(this.selectedWarehouse, item.warehouse.id, 0)
                    }
                })
            }
        }
    },
    methods: {
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
        onChange(event, val) {
            if(this.checkStockModal) {
                if(!val.in_cart)
                    this.$set(this.selectedWarehouse, val.warehouse.id, Number(!this.selectedWarehouse[val.warehouse.id]))
            } else {
                if(this.cartMinAdd <= 0)
                    this.$set(this.selectedWarehouse, val.warehouse.id, Number(!this.selectedWarehouse[val.warehouse.id]))
                // console.log(this.selectedWarehouse[val.warehouse.id])
            }
        },
        changeInputCount(val, id) {
            if(!this.cartDecimalCount)
                this.$set(this.selectedWarehouse, id, Math.round(Number(val)))
            // if(!val)
            //     this.$set(this.selectedWarehouse, id, false)
        },
        countFormatter(value, qual) {
            if(this.remnantControl && qual) {
                if(value < 0)
                    return 0
                else {
                    if(value >= qual)
                        return qual
                    else
                        return value
                }
            } else
                return value
        },
        afterClose() {
            this.$set(this, 'selectedWarehouse', {})
        },
        minus(id) {
            if(this.selectedWarehouse[id] !== 0)
                this.selectedWarehouse[id] -= 1
        },
        plus(id, qual) {
            if(this.remnantControl) {
                if(this.selectedWarehouse[id] < qual)
                    this.$set(this.selectedWarehouse, id, this.selectedWarehouse[id] + 1)
            } else
                this.$set(this.selectedWarehouse, id, this.selectedWarehouse[id] + 1)
        },
        async addWarehouseCart() {
            let valid = false
            let formData = {}

            if(this.warehouseFormInfo && Object.keys(this.warehouseFormInfo)?.length) {
                for (const key in this.selectedWarehouse) {
                    if(this.selectedWarehouse[key]) {
                        formData[key] = this.$refs[`form_${key}`]?.[0]?.form || null
                        valid = await this.$refs[`form_${key}`]?.[0]?.validations() || false
                    } else
                        this.$refs[`form_${key}`]?.[0]?.resetForm()
                }
            } else
                valid = true

            if(valid) {
                if(!Object.keys(formData)?.length)
                    formData = null

                this.addCartWarehouse(this.selectedWarehouse, formData)
            }
        },
        productCount(qual) {
            return qual + ' ' + declOfNum(qual, ['товар', 'товара', 'товаров'])
        },
        checkQuantity(item) {
            if(this.count > item.qual)
                return true
            else
                return false
        }
    }
}
</script>

<style lang="scss">
// .warehouse_select_list {
//     .ant-modal-body {
//         max-height: max-content;
//     }
//     .list {
//         max-height: 63vh;
//         overflow-y: auto;
//     }
// }
.warehouse_list{
    .ant-input-number-handler-wrap{
        display: none;
    }
    .ant-input-number{
        border-radius: 0px;
        border-left: 0px;
        border-right: 0px;
        font-size: 14px;
        max-width: 80px;
        &:hover{
            border-color: var(--border2);
        }
    }
    input{
        text-align: center;
    }
}
.warehouse_list_mobile {
    .ant-modal-header, .ant-modal-body{
        padding: 15px;
    }
}
</style>

<style lang="scss" scoped>
.modal_footer{
    position: sticky;
    padding: 5px 0;
    background: #ffffff;
    bottom: 0;
}
.warehouse_list{
    .item{
        border-radius: var(--borderRadius);
        background: #eff2f5;
        padding: 10px;
        display: flex;
        justify-content: space-between;
        .in_cart{
            color: #00b800;
        }
        .counter_input{
            .btn{
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0 6px;
                transition: all 0.3s linear;
                -moz-user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
                user-select: none;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                border: 1px solid #e1e7ec;
                cursor: pointer;
                background: #fff;
                &:hover{
                    color: var(--blue);
                    background: #eff2f5;
                }
                &.plus{
                    border-left: 0px;
                    border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
                }
                &.minus{
                    border-radius: var(--borderRadius) 0 0 var(--borderRadius);
                    border-right: 0px;
                }

            }
        }
        .counter_input_mobile{
            .ant-input-number{
                max-width: 100%;
            }
        }
        .radio_btn{
            padding-left: 10px;
        }
        .info{
            margin-bottom: 10px;
        }
        .name{
            font-weight: 600;
            font-size: 17px;
            word-break: break-word;
            color: #000;
        }
        .address{
            margin-top: 3px;
            font-weight: 300;
            font-size: 13px;
            word-break: break-word;
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .quantity{
            color: #000;
        }
        .quantity_info{
            margin-top: 5px;
            color: var(--errorRed);
            font-size: 13px;
            font-weight: 300;
        }
    }
}
</style>