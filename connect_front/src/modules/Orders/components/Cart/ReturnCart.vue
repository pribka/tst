<template>
    <div 
        v-if="!pageOrder" 
        class="action_btn cart_btn">
        <a-badge 
            v-if="dynamicButtonsCheck"
            @click="visible = true"
            :count="cartCount" 
            :number-style="{ backgroundColor: '#52c41a' }"
            style="max-width: 32px;" 
            :offset="[0, 9]">
            <a-button
                type="link"
                class="text_current">
                <i class="fi fi-rr-box"></i>
            </a-button>
        </a-badge>
        
        <a-drawer
            title="Корзина возврата"
            placement="right"
            class="cart_drawer"
            :zIndex="zIndex"
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
                    <div v-if="cartEmpty">
                        <div class="cart_empty">
                            <i class="fi fi-rr-box"></i>
                            <h4>Корзина возврата пуста</h4>
                            <div class="mt-6">
                                <a-button 
                                    type="primary" 
                                    size="large"
                                    @click="openProducts()">
                                    Перейти в каталог
                                </a-button>
                            </div>
                        </div>
                    </div>
                    <template v-else>
                        <div class="product_list">
                            <component
                                :is="cartWidget" 
                                v-for="(item, index) in cartList.results" 
                                :key="item.id" 
                                :item="item"
                                storeName="return"
                                cartTypeText="корзины возврата"
                                :itemNumber="index + 1"
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
                                            {{ cartAmount }}  <span v-if="cartCurrency" class="ml-1">{{ cartCurrency.icon }}</span>
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
                                    type="primary"
                                    @click="createOrder()">
                                    Оформить возврат
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
let timer;
export default {
    components: {
        CartItem: () => import('./CartItem.vue'),
        InfiniteLoading
    },
    computed: {
        ...mapState({
            cartCount: state => state.return.cartCount,
            cartList: state => state.return.cartList,
            cartEmpty: state => state.return.cartEmpty,
            firstLoading: state => state.return.firstLoading,
            cartCurrency: state => state.return.cartCurrency,
            cartAmountLoader: state => state.return.cartAmountLoader,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config
        }),
        dynamicButtons() {
            if(!this.config?.order_setting?.return_static_button && typeof this.config.order_setting.return_static_button === 'boolean') {
                return this.config.order_setting.return_static_button
            } else {
                return true
            }
        },
        dynamicButtonsCheck() {
            if(!this.dynamicButtons) {
                return this.cartCount > 0 ? true : false
            } else
                return true
        },
        remnantControl() {
            if(this.config?.order_setting?.remnant_control)
                return true
            else
                return false
        },
        visible: {
            get() {
                return this.$store.state.return.cartVisible
            },
            set(val) {
                this.$store.commit('return/SET_CART_VISIBLE', val)
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
            zIndex: 1000
        }
    },
    methods: {
        clear() {
            if(this.$refs['createOrder']) {
                this.$refs['createOrder'].clear()
            }
        },
        async createOrder() {
            if(!this.remnantControl || await this.$store.dispatch('return/checkCart')) {
                this.visible = false
                this.$router.push({ name: 'create_return_order' })
                // this.$store.commit('return/SET_CREATE_VISIBLE', true)
            } else {
                this.$message.warning('Некоторых позиций в корзине нет в наличии')
            }
        },
        cartRefresh() {
            this.$store.commit('return/CLEAR_STORE')
            this.$store.commit('return/SET_FIRST_LOADING', true)
            this.getCartList()
        },
        cartCountUpdate() {
            clearTimeout(timer)

            timer = setTimeout(async () => {
                if(!this.cartEmpty) {
                    await this.$store.dispatch('return/getCartSummary')
                    await this.$store.dispatch('return/getCartCount')
                }
            }, 800)
        },
        async clearCart() {
            try {
                this.clearLoading = true
                await this.$store.dispatch('return/clearCart')
                this.$message.info('Корзина возврата полностью очищена')
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка очистки корзины возврата')
            } finally {
                this.clearLoading = false
            }
        },
        openProducts() {
            if(this.$route.name !== 'goods')
                this.$router.push({ name: 'goods' })

            this.visible = false
        },
        async getCartList($state = null) {
            if(this.cartList.next && !this.cartEmpty && !this.loading) {
                try {
                    this.loading = true
                    const data = await this.$store.dispatch('return/getCartList')
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
                this.$message.destroy()
                this.getCartList()
            } else {
                await this.$store.commit('return/CLEAR_STORE')
                this.$store.commit('return/SET_FIRST_LOADING', true)
                this.zIndex = 1000
                this.clear()
            }
        }
    },
    mounted() {
        eventBus.$on('update_return_cart', () => {
            this.cartRefresh()
        })
        eventBus.$on('open_return_cart', (zIndex = null) => {
            if(zIndex)
                this.zIndex = zIndex
            this.visible = true
        })
    },
    beforeDestroy(){
        eventBus.$off('update_return_cart')
        eventBus.$off('open_return_cart')
    }
}
</script>