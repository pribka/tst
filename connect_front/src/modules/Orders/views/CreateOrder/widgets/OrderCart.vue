<template>
    <div 
        class="form" 
        :class="item.crmCompact && 'crm_order_cart_widget'"
        :key="reload">
        <template v-if="edit || createEmptyOrder || crmDirectOrder">
            <div class="mb-3" :class="!isMobile && 'flex gap-4'">
                <a-button 
                    type="primary" 
                    icon="plus" 
                    :block="isMobile"
                    :class="!isMobile ? 'w-2/6' : 'mb-1'"
                    @click="openProductDrawer()">
                    Добавить товар
                </a-button>
                <template v-if="edit && user.warehouse_select_is_available">
                    <a-button
                        icon="check"
                        :class="!isMobile ? 'w-2/6' : 'mb-1'"
                        :block="isMobile"
                        @click="selectWarehouse('setShippingWarehouse')">
                        Указать склад отгрузки
                    </a-button>
                    <a-button
                        icon="logout"
                        :class="!isMobile && 'w-2/6'"
                        :block="isMobile"
                        :disabled="!checkedTPGoods.length"
                        @click="selectWarehouse('inNewOrder')">
                        В новый заказ
                    </a-button>
                </template>
            </div>
        </template>
        <div v-show="cartList.results?.length">
            <div 
                class="product_list" 
                :class="[!isMobile && 'table_bordered', item.crmCompact && 'crm_order_product_list']">
                
                <template v-if="!isMobile">
                    <div 
                        class="grid header_labels" 
                        :class="item.nds_column ? 'grid-cols-[40px,1fr,120px,120px,100px,120px]' : 'grid-cols-[40px,1fr,120px,120px,120px]'"
                        :style="item.crmCompact ? crmOrderGridStyle(item) : null">
                        <div class="text-center table_header_cell">№</div>
                        <!-- <div class="text-center">Артикул</div> -->
                        <div class="text-left truncate table_header_cell">Наименование</div>
                        <div class="text-center table_header_cell">Цена в руб.</div>
                        <div class="text-center table_header_cell">Количество</div>
                        <div 
                            v-if="item.nds_column" 
                            class="text-center table_header_cell">
                            Сумма НДС в руб.
                        </div>
                        <div class="text-center table_header_cell">Сумма в руб.</div>
                    </div>
                </template>
                <component
                    :is="cardWidget" 
                    v-for="product, index in cartList.results" 
                    :key="product.id"
                    :itemNumber="index+1"
                    :setOrderLoader="setOrderLoader"
                    :reloadAmount="reloadAmount"
                    :deleteItem="deleteItem"
                    :item="product"
                    :edit="edit"
                    :showPrintForm="item.print_form ? item.print_form : false"
                    :markedWarehouse="markedWarehouse"
                    :setOrderFormCalculated="setOrderFormCalculated"
                    :checkBoxOnChange="checkBoxOnChange"
                    :compactOrderForm="item.crmCompact"
                    :crmDirectOrder="crmDirectOrder"
                    :widgetData="item" />
            </div>
            <InfiniteLoading
                ref="infiniteLoading"
                :distance="400"
                :identifier="currentContract"
                @infinite="getOrderList">
                <div 
                    slot="spinner" 
                    class="flex justify-center w-full">
                    <a-spin class="mt-4" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </InfiniteLoading>
        </div>
        <div v-show="edit && newOrdersListIsNotEmpty()">
            <div class="font-bold text-lg mt-7">Новые заказы:</div>
            <div v-for="newOrder in newOrderDisplayList"
                 :key="newOrder.uid">
                <div class="flex items-center justify-between mt-5 mb-1"> 
                    <div class="font-medium">{{ newOrder.displayText }}</div>
                    <a-button icon="close" type="danger" @click="reset(newOrder)">
                        Отменить
                    </a-button>
                </div>
                <div
                    class="product_list" 
                    :class="!isMobile && 'table_bordered'">
                    <template v-if="!isMobile">
                        <div 
                            class="grid header_labels" 
                            :class="newOrder.nds_column ? 'grid-cols-[40px,1fr,120px,120px,100px,120px]' : 'grid-cols-[40px,1fr,120px,120px,120px]'">
                            <div class="text-center table_header_cell">№</div>
                            <div class="text-left truncate table_header_cell">Наименование</div>
                            <div class="text-center table_header_cell">Цена в руб.</div>
                            <div class="text-center table_header_cell">Количество</div>
                            <div 
                                v-if="newOrder.nds_column" 
                                class="text-center table_header_cell">
                                Сумма НДС в руб.
                            </div>
                            <div class="text-center table_header_cell">Сумма в руб.</div>
                        </div>
                    </template>
                    <simpleOrderProductItem 
                        v-for="product, index in newOrder.tpGoods" 
                        :key="product.id"
                        :itemNumber="index+1"
                        :item="product"
                        :widgetData="item" />
                </div>
            </div>
        </div>
        <component
            :is="addProductDrawer" 
            :addProduct="addProduct"
            page_name="catalogs.goodsmodel_list_page_edit"
            :injectGoods="cartList"
            :embdedCheckStock="embdedCheckStock"
            :createEmptyOrder="createEmptyOrder"
            ref="productDrawer" />
        <selectWarehouseDrawer
            page_name="catalogs.list_warehouses_page"
            :markedWarehouseHandler="markedWarehouseHandler"
            :warehouseList="warehouseList"
            ref="selectWarehouseDrawer" />
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus.js'
import InfiniteLoading from "vue-infinite-loading"
import { v4 as uuidv4 } from 'uuid'
import simpleOrderProductItem from '@apps/Orders/components/simpleOrderProductItem.vue'
import selectWarehouseDrawer from '@apps/Orders/views/CreateOrder/widgets/selectWarehouseDrawer.vue'

export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        form: {
            type: Object,
            required: true
        },
        reload: {
            type: Boolean,
            default: false
        },
        reloadAmount: {
            type: Function,
            default: () => {}
        },
        setOrderLoader: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        },
        sourceCustomerContractId: {
            type: String,
            default: ''
        }
    },
    components: {
        InfiniteLoading,
        simpleOrderProductItem,
        selectWarehouseDrawer
    },
    computed: {
        ...mapState({
            cartList: state => state.orders.orderList,
            currentContract: state => state.orders.currentContract,
            newOrdersList: state => state.orders.create_orders,
            user: state => state.user.user,
            newOrderDisplayList: state => state.orders.newOrderDisplayList
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        cardWidget() {
            if(this.isMobile)
                return () => import('../../../components/OrderProductItemMobile.vue')
            return () => import('../../../components/OrderProductItem.vue')
        },
        addProductDrawer() {
            if(this.edit || this.createEmptyOrder || this.crmDirectOrder)
                return () => import('@apps/Products/ProductDrawer.vue')
            return null
        },
        crmDirectOrder() {
            return Boolean(this.sourceCustomerContractId)
        },
        embdedCheckStock() {
            if(this.createEmptyOrder && !this.cartList.results?.length) {
                return false
            }
            return true
        }
    },
    data() {
        return {
            loading: false,
            checkedTPGoods: [],
            warehouseLoader: false,
            warehouseList: [],
            newOrderCartList: [],
            eventSource: '',
            markedWarehouse: {} 
        }
    },
    methods: {
        selectWarehouse(source) {
            this.eventSource = source
            this.$nextTick(() => {
                if(this.$refs['selectWarehouseDrawer']) {
                    this.$refs['selectWarehouseDrawer'].toggleDrawer()
                }
            })
        },
        setWarehouse(id) {
            let warehouse = this.warehouseList.find(f => f.id === id)
            this.$store.commit('orders/SET_WAREHOUSE', warehouse)
        },
        markedWarehouseHandler(id) {
            if(this.eventSource === 'setShippingWarehouse') {
                this.setWarehouse(id)
                this.markedWarehouse = this.warehouseList.find(f => f.id === id)
                this.$store.commit('orders/SET_DELIVERY_WAREHOUSES', [this.markedWarehouse,])
            }
            if(this.eventSource === 'inNewOrder') {
                this.addToCreateOrders(id)
            }
            this.eventSource = ''
        },
        reset(order) {
            this.$store.commit('orders/RESET_NEW_ORDER', {
                tpGoods: order.tpGoods,
                uid: order.uid
            })
            this.$store.commit('orders/REMOVE_ITEM_FROM_ORDER_DISPLAY_LIST', this.newOrderDisplayList.findIndex(f => f === order))
            eventBus.$emit('edit_update_price')
        },
        newOrdersListIsNotEmpty() {
            return Object.keys(this.newOrderDisplayList).length !== 0
        },
        async addToCreateOrders(id) {
            for (let i=0; i < this.cartList.results.length; i++) {
                let item = this.cartList.results[i]
                if(this.checkedTPGoods.indexOf(item.id) !== -1) {
                    this.newOrderCartList.push(item)
                    this.$store.commit('orders/DELETE_ORDER_GOODS', item)
                    i--
                }
            }
            this.$store.commit('orders/SET_NEW_ORDER_WAREHOUSE', id)
            this.$store.commit('orders/SET_NEW_ORDER_TPGOODG', this.newOrderCartList)
            let uid = uuidv4()
            uid = uid.replace(/-/g, '')
            await this.$store.dispatch('orders/addToCreateOrders', uid)
            const newWarehoyseName = this.warehouseList.find(f => f.id === id).name
            this.$store.commit('orders/PUSH_TO_NEW_ORDER_DISPLAY_LIST', {
                displayText: `Склад "${newWarehoyseName}", ${this.newOrderCartList.length} товарн. поз.`,
                tpGoods: this.newOrderCartList,
                uid: uid
            })
            this.checkedTPGoods = []
            this.newOrderCartList = []
            eventBus.$emit('edit_update_price')
            
            this.setOrderFormCalculated(false)
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
        },
        getPopupContainer() {
            return document.querySelector('.form')
        },
        checkBoxOnChange(val) {
            if(val.target.checked) {
                if(this.checkedTPGoods.indexOf(val.target.value) === -1) {
                    let index = this.cartList.results.findIndex(f => f.id === val.target.value)
                    this.checkedTPGoods.push(val.target.value)
                }
            } else {
                if(this.checkedTPGoods.indexOf(val.target.value) !== -1) {
                    let index = this.cartList.results.findIndex(f => f.id === val.target.value)
                    this.checkedTPGoods.splice(this.checkedTPGoods.indexOf(val.target.value), 1)
                }
            }
        },
        async addProduct({waList, formData, id, draft}) {
            if(this.crmDirectOrder) {
                await this.$store.dispatch('orders/addCrmOrderLine', {
                    waList,
                    formData,
                    id
                })
                eventBus.$emit('edit_update_price')
                this.setOrderFormCalculated(false)
                return
            }
            await this.$store.dispatch('orders/addShoppingCartWarehouse', {
                waList,
                formData,
                id,
                draft
            })
            eventBus.$emit('edit_update_price')
        },
        async deleteItem(item) {
            this.$store.commit('orders/DELETE_ORDER_GOODS', item)
            if(this.createEmptyOrder) {
                try {
                    await this.$store.dispatch(`orders/deleteProductCart`, {
                        goods: item,
                        count: +item.quantity
                    })
                } catch(e) {
                    console.log(e)
                    this.$message.error('Ошибка удаления товара')
                }
            }
            eventBus.$emit('edit_update_price')
            if(this.checkedTPGoods.indexOf(item.id) !== -1) {
                this.checkedTPGoods.splice(this.checkedTPGoods.indexOf(item.id), 1)
            }
        },
        openProductDrawer() {
            this.$nextTick(() => {
                if(this.$refs['productDrawer']) {
                    this.$refs['productDrawer'].toggleDrawer()
                }
            })
        },
        async getOrderList($state = null) {
            if(this.cartList.next && !this.loading) {
                try {
                    this.loading = true
                    const data = await this.$store.dispatch('orders/getOrderList')

                    if(data?.next) {
                        if($state)
                            $state.loaded()
                    } else {
                        if($state)
                            $state.complete()
                    }
                } catch(e) {
                    console.log(e)
                    this.loading = false
                    if($state)
                        $state.complete()
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        },
        crmOrderGridStyle(item) {
            if(item?.nds_column) {
                return {
                    gridTemplateColumns: '40px minmax(300px, 1fr) 130px 190px 110px 130px'
                }
            }
            return {
                gridTemplateColumns: '40px minmax(300px, 1fr) 130px 190px 130px'
            }
        },
        resetProductList() {
            this.$store.commit('orders/CLEAR_ORDER_CREATE_PAGE')
            this.reloadAmount()
            this.getOrderList()
        }
    },
    mounted() {
        eventBus.$on('update_order_cart', () => {
            this.resetProductList()
        })
        this.getWarehouseList()
    },
    beforeDestroy() {
        eventBus.$off('update_order_cart')
    }
}
</script>

<style lang="scss" scoped>
.header_labels{
    font-weight: 300;
    color: #000;
    position: sticky;
    top: 0px;
    z-index: 10;
}

.table_header_cell {
    background-color: #fff;
    padding: 2px 5px;
    border-bottom: 1px solid var(--border2);
    &:not(:last-child) {
        border-right: 1px solid var(--border2);
    }
}
.product_list{
    &.table_bordered{
        border: 1px solid var(--border2);
    }
}
</style>
