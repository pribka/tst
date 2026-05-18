<template>
    <div 
        v-if="!pageOrder" 
        class="action_btn cart_btn">
        <a-badge 
            @click="visible = true"
            :count="cartCount" 
            :number-style="{ backgroundColor: '#1d65c0' }"
            style="max-width: 32px;" 
            :offset="[0, 9]">
            <a-button
                type="link"
                class="text_current">
                <i class="fi fi-rr-shopping-cart"></i>
            </a-button>
        </a-badge>
        
        <a-drawer
            title="Корзина"
            placement="right"
            class="cart_drawer"
            :zIndex="zIndex"
            destroyOnClose
            :class="isMobile && 'cart_drawer_mobile'"
            :width="windowWidth > 700 ? 700 : '100%'"
            :visible="visible"
            :afterVisibleChange="afterVisibleChange"
            @close="visible = false">
            <div class="drawer_body">
                <div 
                    v-if="firstLoading" 
                    class="flex justify-center pt-3">
                    <a-spin />
                </div>
                <template v-else>
                    <div v-if="cartEmpty || localEmpty">
                        <div class="cart_empty">
                            <i class="fi fi-rr-shopping-cart"></i>
                            <h4>Ваша корзина пуста</h4>
                            <template v-if="showCatalogButton">
                                <p>
                                    Исправить это просто: выберите в каталоге интересующий товар и нажмите кнопку «В корзину».
                                </p>
                                <div class="mt-6">
                                    <a-button 
                                        type="primary" 
                                        size="large"
                                        @click="openProducts()">
                                        Перейти в каталог
                                    </a-button>
                                </div>
                            </template>
                        </div>
                    </div>
                    <template v-else>
                        <div class="product_list">
                            <component
                                :is="cartWidget" 
                                v-for="(item, index) in cartList.results" 
                                :key="item.id" 
                                :item="item"
                                :itemNumber="index + 1"
                                :setUpdateLoader="setUpdateLoader"
                                :remnantControl="remnantControl"
                                :cartCountUpdate="cartCountUpdate" />
                            <InfiniteLoading 
                                :distance="400"
                                @infinite="getCartList">
                                <div slot="spinner" >
                                    <a-spin class="mt-4" />
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </InfiniteLoading>
                        </div>
                        <div class="cart_footer">
                            <div class="cart_summary">
                                <a-button
                                    style="color: #505050;"
                                    size="small"
                                    icon="delete"
                                    type="link"
                                    :loading="clearLoading"
                                    @click="clearCart()">
                                    очистить
                                </a-button>
                                <div class="cart_summary_item summary flex items-baseline">
                                    <div class="label">
                                        Итого
                                    </div>
                                    <div class="val">
                                        <a-spin :spinning="cartAmountLoader">
                                            {{ cartAmount }} 
                                            <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
                                            <span v-else class="ml-1">руб</span>
                                        </a-spin>
                                    </div>
                                </div>
                            </div>
                            <div 
                                class="actions_btn"
                                :class="isMobile ? 'mt-2' : 'mt-4'">
                                <a-button
                                    v-if="isMobile"
                                    block
                                    size="large"
                                    class="px-8 mr-2"
                                    type="defalut"
                                    @click="visible = false">
                                    {{ $t('close') }}
                                </a-button>
                                <a-button 
                                    size="large"
                                    :block="isMobile"
                                    class="px-8"
                                    :loading="updateLoading"
                                    type="primary"
                                    @click="createOrder()">
                                    Оформить заказ
                                </a-button>
                            </div>
                        </div>
                    </template>
                </template>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import InfiniteLoading from "vue-infinite-loading"
import { priceFormatter } from '@/utils'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus.js'
import warehouse from '../../mixins/warehouse'
let timer;
export default {
    components: {
        CartItem: () => import('./CartItem.vue'),
        InfiniteLoading
    },
    mixins: [
        warehouse
    ],
    computed: {
        ...mapState({
            cartCount: state => state.orders.cartCount,
            cartList: state => state.orders.cartList,
            cartEmpty: state => state.orders.cartEmpty,
            firstLoading: state => state.orders.firstLoading,
            cartCurrency: state => state.orders.cartCurrency,
            cartAmountLoader: state => state.orders.cartAmountLoader,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config
        }),
        remnantControl() {
            if(this.config?.order_setting?.remnant_control)
                return true
            else
                return false
        },
        showCatalogButton() {
            return this.config?.order_setting?.showCartCatalogButton || false
        },
        catalogLink() {
            return this.config?.order_setting?.cartCatalogButtonLink || 'goods'
        },
        visible: {
            get() {
                return this.$store.state.orders.cartVisible
            },
            set(val) {
                this.$store.commit('orders/SET_CART_VISIBLE', val)
            }
        },
        cartAmount() {
            return priceFormatter(this.cartList.amount)
        },
        pageOrder() {
            if(this.$route.name === 'create_order' || this.$route.name === 'create_return_order')
                return true
            else
                return false
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        cartWidget() {
            if(this.isMobile)
                return () => import('./CartItemMobile.vue')
            return () => import('./CartItem.vue')
        }
    },
    data() {
        return {
            loading: false,
            clearLoading: false,
            zIndex: 1000,
            updateLoading: false,
            localEmpty: false
        }
    },
    methods: {
        clear() {
            if(this.$refs['createOrder']) {
                this.$refs['createOrder'].clear()
            }
        },
        async createOrder() {
            if(!this.remnantControl || await this.$store.dispatch('orders/checkCart')) {
                this.visible = false
                this.$router.push({ name: 'create_order' })
                // this.$store.commit('orders/SET_CREATE_VISIBLE', true)
            } else {
                this.$message.warning('Некоторых позиций в корзине нет в наличии')
            }
        },
        cartRefresh() {
            this.$store.commit('orders/CLEAR_STORE')
            this.$store.commit('orders/SET_FIRST_LOADING', true)
            this.getCartList()
        },
        setUpdateLoader(value) {
            this.updateLoading = value
        },
        cartCountUpdate() {
            this.updateLoading = true
            clearTimeout(timer)

            timer = setTimeout(async () => {
                if(!this.cartEmpty) {
                    try {
                        await this.$store.dispatch('orders/getCartSummary')
                        await this.$store.dispatch('orders/getCartCount')
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.updateLoading = false
                    }
                }
            }, 800)
        },
        async clearCart() {
            try {
                this.clearLoading = true
                await this.$store.dispatch('orders/clearCart')
                this.localEmpty = true
                this.$message.info('Корзина полностью очищена')
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка очистки корзины')
            } finally {
                this.clearLoading = false
            }
        },
        openProducts() {
            if(this.$route.name !== this.catalogLink)
                this.$router.push({ name: this.catalogLink })

            this.visible = false
        },
        async getCartList($state = null) {
            if(this.cartList.next && !this.cartEmpty && !this.loading) {
                try {
                    this.loading = true
                    const data = await this.$store.dispatch('orders/getCartList')
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
        async afterVisibleChange(val) {
            if(val) {
                this.getWarehouseFormInfo()
                this.$message.destroy()
                this.getCartList()
            } else {
                await this.$store.commit('orders/CLEAR_STORE')
                this.$store.commit('orders/SET_FIRST_LOADING', true)
                this.zIndex = 1000
                this.localEmpty = false
                this.clear()
            }
        }
    },
    mounted() {
        eventBus.$on('update_cart', () => {
            this.cartRefresh()
        })
        eventBus.$on('update_cart_count', () => {
            this.$store.commit('orders/CLEAR_STORE')
            this.$store.commit('orders/SET_FIRST_LOADING', true)
            this.cartCountUpdate()
        })
        eventBus.$on('open_cart', (zIndex = null) => {
            if(zIndex)
                this.zIndex = zIndex
            this.visible = true
        })
    },
    beforeDestroy(){
        eventBus.$off('update_cart_count')
        eventBus.$off('update_cart')
        eventBus.$off('open_cart')
    }
}
</script>