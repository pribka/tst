<template>
    <a-modal
        title="Склад"
        :class="!isMobile || 'warehouse_list_mobile'"
        :visible="visible"
        :footer="null"
        :zIndex="zIndex"
        :destroyOnClose="true"
        @cancel="handleCancel"
        :afterClose="afterClose">
        <div class="warehouse_list">
            <div
                v-for="item in warehouseList"
                :key="item.warehouse.id"
                class="item select-none w-full"
                @click="onChange($event, item)">
                <div :class="!isMobile || 'w-full'">
                    <div class="info">
                        <div class="name">
                            {{ item.warehouse.name }}
                        </div>
                        <div
                            v-if="item.warehouse.address"
                            class="address">
                            {{ item.warehouse.address }}
                        </div>
                    </div>
                    <div class="flex"
                         :class="isMobile ? 'flex-col-reverse w-full' : 'items-center' ">

                        <div
                            v-if="checkStockModal && item.in_cart"
                            class="mr-6 in_cart flex items-center">
                            <i class="fi fi-rr-shopping-cart-check mr-2"></i>
                            В корзине
                        </div>
                        <template v-else>
                            <div
                                v-if="Object.keys(selectedWarehouse).length && cartMinAdd > 0"
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
                                    :formatter="value => countFormatter(value, item.qual)"
                                    :max="item.qual"
                                    :default-value="0"
                                    @change="changeInputCount($event, item.warehouse.id)" />
                                <a-input-number
                                    v-else
                                    v-model="selectedWarehouse[item.warehouse.id]"
                                    style="width: 100%;"
                                    :min="0"
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
                                class="mr-6">
                                <a-checkbox
                                    :checked="selectedWarehouse[item.warehouse.id]"
                                    @change="onChange($event, item)">
                                    Выбрать
                                </a-checkbox>
                            </div>
                        </template>
                        <div class="quantity"
                             :class="!isMobile || 'mb-2'">
                            всего: {{ item.quantity }}
                        </div>
                    </div>
                    <!--<div
                        v-if="checkQuantity(item)"
                        class="quantity_info">
                        В корзину будет добавлено {{ productCount(item.qual) }}
                    </div>-->
                </div>
            </div>
            <div class="flex mt-4 justify-end">
                <a-button
                    icon="shopping-cart"
                    type="primary"
                    :block="isMobile"
                    size="large"
                    class="px-8"
                    :disabled="btnDisabled"
                    :loading="loading"
                    @click="addWarehouseCart()">
                    В корзину возврата
                </a-button>
            </div>
        </div>
    </a-modal>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { mapState } from 'vuex'
export default {
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
        zIndex: {
            type: Number,
            default: 1000
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        cartMinAdd() {
            if(this.config?.order_setting?.min_product_count === 0)
                return this.config.order_setting.min_product_count
            else
                return 1
        },
        remnantControl() {
            if(this.config?.order_setting?.remnant_returns_control)
                return true
            else
                return false
        },
        checkStockModal() {
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
        }
    },
    data() {
        return {
            selectWarehouse: null,
            selectedWarehouse: {}
        }
    },
    watch: {
        visible(val) {
            if(val && this.warehouseList?.length) {
                let newCount = Number(JSON.parse(JSON.stringify(this.count)))
                this.warehouseList.forEach(item => {
                    let cnt = newCount
                    if(cnt > item.qual)
                        cnt = item.qual

                    if(this.cartMinAdd > 0)
                        this.$set(this.selectedWarehouse, item.warehouse.id, cnt)
                    else
                        this.$set(this.selectedWarehouse, item.warehouse.id, false)

                    newCount = newCount - item.qual
                    if(newCount < 0)
                        newCount = 0

                    /*console.log(item, 'item')
                    if(index === 0) {
                        this.$set(this.selectedWarehouse, item.warehouse.id, Number(JSON.parse(JSON.stringify(this.count))))
                    } else {
                        this.$set(this.selectedWarehouse, item.warehouse.id, 0)
                    }*/
                })
            }
        }
    },
    methods: {
        onChange(event, val) {
            if(this.checkStockModal) {
                if(!val.in_cart)
                    this.$set(this.selectedWarehouse, val.warehouse.id, !this.selectedWarehouse[val.warehouse.id])
            } else {
                if(this.cartMinAdd <= 0)
                    this.$set(this.selectedWarehouse, val.warehouse.id, !this.selectedWarehouse[val.warehouse.id])
            }
        },
        changeInputCount(val, id) {
            if(!val)
                this.$set(this.selectedWarehouse, id, 0)
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
        addWarehouseCart() {
            this.addCartWarehouse(this.selectedWarehouse)
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