import { priceFormatter } from '@/utils'
import Availability from '../components/Availability.vue'
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
export default {
    components: {
        Availability
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            windowWidth: state => state.windowWidth,
            cartList: state => state.orders.orderList
        }),
        disabledCart() {
            if(this.remnantControl) {
                if (this.item.available_count)
                    return false
                else
                    return true
            } else
                return false
        },
        warehouseWidget() {
            if (this.checkStock || this.checkStockModal)
                return () => import('../components/SelectWarehouse.vue')
            else
                return null
        },
        checkStock() {
            
            if(this.config?.order_setting?.repeat_add_product) {
                return true
            }
                
            if(this.embded) {
                if(!this.embdedCheckStock)
                    return true

                if(this.cartList.results?.length) {
                    const find = this.cartList.results.find(f => f.goods.id === this.item.id)
                    if(find)
                        return false
                    return true
                }
                
                return false
            } else {
                if (this.config?.order_setting?.check_stock)
                    return true
                else {
                    if(this.item.in_cart)
                        return false
                    else
                        return true
                }
            }
        },
        checkStockModal() {
            if (this.config?.order_setting?.check_stock_modal)
                return true
            else
                return false
        },
        price() {
            return priceFormatter(this.item.price)
        },
        price_by_catalog() {
            return priceFormatter(this.item.price_by_catalog)
        },
        remnantControl() {
            if(this.config?.order_setting?.remnant_control)
                return true
            else
                return false
        },
        cartMinAdd() {
            if(this.config?.order_setting?.min_product_count === 0)
                return this.config.order_setting.min_product_count
            else
                return 1
        },
        cartDecimalCount() {
            return this.config?.order_setting?.cartDecimalCount
        }
    },
    data() {
        return {
            loading: false,
            visible: false,
            count: null,
            warehouseList: [],
            detail: false
        }
    },
    created() {
        this.count = this.cartMinAdd
    },
    methods: {
        addCartMessage(message = 'Товар добавлен в корзину.', durations = 3, openHandler = 'open_cart', openText = 'Открыть корзину') {

            if(window?.ReactNativeWebView) {
                window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'productAddCart'
                }))
            }

            this.$message.info(this.$createElement(
                'span',
                {},
                [
                    message,
                    this.$createElement(
                        'span',
                        {
                            class: 'link cursor-pointer blue_color',
                            on: {
                                click: () => {
                                    if(window?.ReactNativeWebView) {
                                        window.ReactNativeWebView.postMessage(JSON.stringify({
                                            type: 'openCart'
                                        }))
                                    }
                                    eventBus.$emit(openHandler, 2000)
                                }
                            },
                        },
                        ` ${openText}`
                    )
                ]
            ),
            durations)
        },
        changeInputCount(val) {
            if(!this.cartDecimalCount)
                this.count = Math.round(val)
            if (!val)
                this.count = this.cartMinAdd
        },
        openCart() {
            this.$store.commit('orders/SET_CART_VISIBLE', true)
        },
        async addCartWarehouse(waList, formData = null) {
            try {
                this.loading = true

                if(this.createEmptyOrder) {
                    await this.$store.dispatch('orders/addShoppingCartWarehouse', {
                        waList,
                        formData,
                        id: this.item.id
                    })
                    
                    this.addCartMessage()
                    this.count = this.cartMinAdd
    
                    if (this.visible)
                        this.visible = false
    
                    if (this.detail) {
                        eventBus.$emit('update_cart')
                    }
                } else {
                    if(this.embded) {
                        await this.addProduct({
                            waList,
                            formData,
                            id: this.item.id,
                            draft: true
                        })
                        this.$message.info('Товар добавлен в заказ')
                        if (this.visible)
                            this.visible = false
                    } else {
                        const data = await this.$store.dispatch('orders/addShoppingCartWarehouse', {
                            waList,
                            formData,
                            id: this.item.id
                        })
        
                        this.addCartMessage()
                        this.count = this.cartMinAdd
        
                        if (this.visible)
                            this.visible = false
        
                        if (this.detail) {
                            eventBus.$emit('update_cart')
                        }
                    }
                }
            } catch (error) {
                if (error?.non_field_errors?.length) {
                    error.non_field_errors.forEach(item => {
                        if (item.includes('Too much quantity'))
                            this.$message.error('Количество выбранного товара превышает количество на выбранном складе')
                        else
                            this.$message.error(item)
                    })
                }
                console.log(error)
            } finally {
                this.loading = false
            }
        },
        countFormatter(value) {
            if (this.remnantControl && this.item.available_count) {
                if (value < this.cartMinAdd)
                    return this.cartMinAdd
                else {
                    if (value >= this.item.available_count)
                        return this.item.available_count
                    else
                        return value
                }
            } else
                return value
        },
        changeCount(value) {
            if(!this.cartDecimalCount)
                value = Math.round(value)
            this.count = value
        },
        plus() {
            if(this.remnantControl) {
                if (this.item.available_count > this.count) {
                    this.count += 1
                }
            } else
                this.count += 1
        },
        minus() {
            if (this.count > this.cartMinAdd)
                this.count -= 1
        },
        handleCancel() {
            this.visible = false
        },
        async addCartSwitch() {
            if (this.embdedCheckStock && this.checkStock || this.embdedCheckStock && this.checkStockModal || this.createEmptyOrder && this.checkStock) {
                try {
                    this.loading = true
                    const { data } = await this.$http.get(`/catalogs/goods/${this.item.id}/availability/`)
                    if (data?.results?.length) {
                        this.visible = true
                        this.warehouseList = data.results.map(item => {
                            return {
                                ...item,
                                qual: Number(item.quantity)
                            }
                        })
                    } else {
                        // this.addCart()
                    }
                } catch (e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else {
                this.addCart()
            }
        },
        async addCart(warehouse = null) {
            try {
                this.loading = true

                let queryData = {
                    goods: this.item.id,
                    quantity: this.count
                }

                if (warehouse)
                    queryData.warehouse = warehouse

                if(this.embded) {
                    await this.addProduct({
                        goods: this.item
                    })
                } else {
                    await this.$store.dispatch('orders/addShoppingCart', queryData)
                    this.addCartMessage()
                    this.count = this.cartMinAdd
                    // if (this.visible)
                    //     this.visible = false

                    if (this.detail)
                        eventBus.$emit('update_cart')
                }
            } catch (error) {
                if (error?.non_field_errors?.length) {
                    error.non_field_errors.forEach(item => {
                        if (item.includes('Too much quantity'))
                            this.$message.error('Количество выбранного товара превышает количество на выбранном складе')
                        else if (item.includes('No remnants'))
                            this.$message.error('Нет в наличии')
                        else
                            this.$message.error(item)
                    })
                }
                console.log(error)
            } finally {
                this.loading = false
            }
        }
    }
}