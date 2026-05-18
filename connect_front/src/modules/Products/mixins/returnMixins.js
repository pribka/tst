import Availability from '../components/Availability.vue'
import eventBus from '@/utils/eventBus.js'
export default {
    components: {
        Availability
    },
    computed: {
        warehouseRWidget() {
            if (this.checkReturn)
                return () => import('../components/SelectReturnWarehouse.vue')
            else
                return null
        },
        checkReturn() {
            if (this.$store.state.config.config?.order_setting.purchase_returns)
                return true
            else
                return false
        }
    },
    data() {
        return {
            rLoading: false,
            rVisible: false,
            rWarehouseList: []
        }
    },
    methods: {
        handleReturnCancel() {
            this.rVisible = false
        },
        async addCartRWarehouse(waList) {
            try {
                this.rLoading = true

                await this.$store.dispatch('return/addShoppingCartWarehouse', {
                    waList,
                    id: this.item.id
                })

                this.addCartMessage('Товар добавлен в корзину возврата.', 3, 'open_return_cart', 'Открыть корзину возврата')

                if (this.rVisible)
                    this.rVisible = false

                if (this.detail) {
                    eventBus.$emit('update_return_cart')
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
                this.rLoading = false
            }
        },
        async addReturnCartSwitch() {
            try {
                this.rLoading = true
                const { data } = await this.$http.get(`/catalogs/goods/${this.item.id}/availability/`, {
                    params: {
                        my: true
                    }
                })
                if(data.results?.length) {
                    this.rWarehouseList = data.results.map(item => {
                        return {
                            ...item,
                            qual: Number(item.quantity)
                        }
                    })
                    this.rVisible = true
                } else {
                    this.$message.info('У товара нет складов для возврата')
                }               
            } catch (e) {
                console.log(e)
            } finally {
                this.rLoading = false
            }
        },
        async addReturnCart(warehouse = null) {
            try {
                this.rLoading = true

                let queryData = {
                    goods: this.item.id,
                    quantity: this.count
                }

                if (warehouse) {
                    queryData.warehouse = warehouse
                }

                await this.$store.dispatch('return/addShoppingCart', queryData)
                this.addCartMessage('Товар добавлен в корзину возврата.', 3, 'open_return_cart', 'Открыть корзину возврата')
                // this.count = this.cartMinAdd
                if (this.rVisible)
                    this.rVisible = false

                if (this.detail)
                    eventBus.$emit('update_return_cart')
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
                this.rLoading = false
            }
        }
    }
}