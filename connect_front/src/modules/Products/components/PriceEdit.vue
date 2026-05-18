<template>
    <a-spin 
        :spinning="loading" 
        size="small">
        <a-popover 
            :visible="visible"
            content="Необходимо сохранить новую стоимость"
            :getPopupContainer="getPopupContainer"
            destroyTooltipOnHide>
            <div class="flex items-center" :ref="`price_edit_${item.id}`">
                <vue-autonumeric
                    ref="input_number"
                    class="ant-input ant-input-sm price_input"
                    v-model="price"
                    @input="inputChange"
                    :options="decimalConfig"/>
                <template v-if="checkPriceEdit">
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
                </template>
            </div>
        </a-popover>
    </a-spin>
</template>

<script>
import VueAutonumeric from 'vue-autonumeric'
export default {
    components: {
        VueAutonumeric
    },
    props: {
        item: {
            type: Object,
            required: true
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
    data() {
        return {
            price: null,
            oldPrice: null,
            loading: false,
            visible: false,
            decimalConfig: {
                decimalLength: 2,
                decimalPlaces: 2,
                maxValue: "1000000000000000000000",
                minValue: "-1000000000000000000000"
            },
            demicalLenght: 2
        }
    },
    created() {
        this.price = JSON.parse(JSON.stringify(this.item.price_by_catalog))
        this.oldPrice = JSON.parse(JSON.stringify(this.item.price_by_catalog))

        this.$nextTick(() => {
            if(this.$refs['input_number']?.$refs?.['autoNumericElement']) {
                this.$refs['input_number'].$refs['autoNumericElement'].addEventListener('blur', event => {
                    if(this.checkPriceEdit) {
                        this.visible = true
                    }
                })
            }
        })
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`price_edit_${this.item.id}`]
        },
        priceDefault() {
            this.visible = false
            this.price = JSON.parse(JSON.stringify(this.oldPrice))
        },
        async savePrice() {
            this.visible = false
            const oldP = parseFloat(this.oldPrice),
                price_by_catalog = parseFloat(this.price)

            if(oldP !== price_by_catalog) {
                try {
                    this.loading = true
                    const { data } = await this.$http.put(`/catalogs/goods/${this.item.id}/update_price/`, {
                        price_by_catalog
                    })
                    if(data) {
                        this.oldPrice = price_by_catalog
                        this.$message.info('Цена успешно изменена')
                        this.$store.commit('products/CHANGE_PRODUCT_PRICE', {price_by_catalog, id: this.item.id})
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
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
.price_input{
    max-width: 120px;
}
</style>