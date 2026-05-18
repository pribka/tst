import cart from './cart.js'
import returnMixins from './returnMixins.js'
import eventBus from '@/utils/eventBus.js'
import 'lazysizes'
export default {
    mixins: [cart, returnMixins],
    props: {
        item: {
            type: Object,
            required: true
        },
        embded: {
            type: Boolean,
            default: false  
        },
        injectGoods: {
            type: Object,
            default: () => null
        },
        addProduct: {
            type: Function,
            default: () => {}
        },
        embdedCheckStock: {
            type: Boolean,
            default: true
        },
        addText: {
            type: String,
            default: "Добавить"
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        priceWidget() {
            if(this.priceEdit)
                return () => import('../components/PriceEdit.vue')
            return null
        },
        user() {
            return this.$store.state.user.user
        },
        priceEdit() {
            return this.user?.can_edit_goods_price || false
        },
        wModalZIndex() {
            return (this.embded || this.createEmptyOrder) ? 2000 : 1000
        }
    },
    methods: {
        async deleteCart() {
            try {
                this.loading = true
                await this.$store.dispatch('orders/deleteProductCart', this.item)
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}