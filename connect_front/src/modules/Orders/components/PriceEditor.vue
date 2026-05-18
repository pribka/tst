<template>
    <div 
        :class="inlineForm && 'flex items-center'" 
        class="price_editor_input relative"
        :style="!inlineForm ? 'max-width: 100%;' : 'max-width: 150px;'">
        <vue-autonumeric
            ref="input_number"
            class="ant-input field_width w-full ant-input-sm"
            @input="inputChange"
            v-on:keyup.native.enter="savePrice"
            v-model="price"
            :options="decimalConfig"/>
        <div 
            v-if="checkPriceEdit" 
            class="price_actions absolute">
            <a-button 
                type="link" 
                size="small"
                icon="check"
                class="text_green"
                v-tippy="{ inertia : true }"
                content="Сохранить"
                @click="savePrice()" />
            <a-button 
                type="link" 
                size="small"
                class="text_red"
                icon="close"
                v-tippy="{ inertia : true }"
                content="Сбросить"
                @click="priceDefault()" />
        </div>
    </div>
</template>

<script>
import VueAutonumeric from 'vue-autonumeric'
export default {
    components: {
        VueAutonumeric
    },
    props: {
        goods: {
            type: Object,
            required: true
        },
        changeCount: {
            type: Function,
            default: () => {}
        },
        showEditPrice: {
            type: Function,
            default: () => {}
        },
        updateQuantityItems: {
            type: Function,
            default: () => {}
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        defPrice: {
            type: [String, Number],
            default: '0'
        },
        storeList: {
            type: String,
            default: 'cartList'
        },
        inlineForm: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        checkPriceEdit() {
            if(this.price && this.oldPrice) {
                return parseFloat(this.price) !== parseFloat(this.oldPrice) || false
            }
            return false
        }
    },
    data () {
        return {
            oldPrice: null,
            startPrice: null,
            price: null,
            decimalConfig: {
                decimalLength: 2,
                decimalPlaces: 2,
                maxValue: "1000000000000000000000",
                minValue: "-1000000000000000000000"
            },
            demicalLenght: 2
        }
    },
    created () {
        if(this.goods) {
            if(this.goods.custom_price) {
                this.price = JSON.parse(JSON.stringify(this.goods.custom_price))
                this.oldPrice = JSON.parse(JSON.stringify(this.goods.custom_price))
                this.startPrice = JSON.parse(JSON.stringify(this.goods.custom_price))
            } else {
                this.price = JSON.parse(JSON.stringify(this.goods.goods.price))
                this.oldPrice = JSON.parse(JSON.stringify(this.goods.goods.price))
                this.startPrice = JSON.parse(JSON.stringify(this.goods.goods.price))
            }
        }
    },
    methods: {
        setStartPrice() {
            this.price = JSON.parse(JSON.stringify(this.startPrice))
            this.oldPrice = JSON.parse(JSON.stringify(this.price))
            this.$store.commit('orders/CHANGE_CART_ITEM_PRICE', {
                id: this.goods.id,
                price: this.price,
                type: this.storeList
            })
            this.updateQuantityItems()
        },
        updateStartPrice() {
            if(this.goods.custom_price)
                this.startPrice = JSON.parse(JSON.stringify(this.goods.custom_price))
            else
                this.startPrice = JSON.parse(JSON.stringify(this.goods.goods.price))
        },
        priceDefault() {
            this.price = JSON.parse(JSON.stringify(this.oldPrice))
        },
        async savePrice() {
            const oldP = parseFloat(this.defPrice),
                newP = parseFloat(this.price)

            if(newP >= oldP) {
                this.setOrderFormCalculated(false)
                try {
                    await this.changeCount(null, {custom_price: this.price})
                    this.$store.commit('orders/CHANGE_CART_ITEM_PRICE', {
                        id: this.goods.id,
                        price: this.price,
                        type: this.storeList
                    })
                    this.showEditPrice()
                    this.updateQuantityItems()
                    this.oldPrice = JSON.parse(JSON.stringify(this.price))
                } catch(e) {
                    console.log(e)
                }
            } else {
                this.$message.warning('Указанная цена ниже минимально допустимой цены')
            }
        },
        inputChange(value, e) {
            let selectionStart = 1
            let afterLength = value.toString().split('.')[0]

            if(afterLength) {
                afterLength = Number(afterLength).toLocaleString('ru').toString().length
            }

            if(e) {
                selectionStart = e.target.selectionStart
            }

            let replaceValue = value

            replaceValue = replaceValue.toFixed(this.demicalLenght)

            if(!/^[0-9]*$/.test(replaceValue)) {
                let beforeLength = replaceValue.toString().split('.')[1].length
                // console.log(beforeLength, 'beforeLength')
            }

            this.$nextTick(() => {
                const input = this.$refs.input_number.$refs.autoNumericElement
                input.setSelectionRange(afterLength, afterLength)
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.price_actions{
    top: 0;
    right: 0;
    z-index: 5;
}
</style>