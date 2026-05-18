<template>
    <a-form-model-item
        prop="quantityInMeasureUnits"
        class="w-full form_field"
        :class="smallForm && 'form_field_small'"
        :label="label">
        <vue-autonumeric
            v-if="!disabled"
            ref="input_number"
            class="ant-input field_width w-full"
            :class="inputSize === 'small' && 'ant-input-sm'"
            @input="inputChange"
            v-model="quantityInMeasureUnits"
            :options="decimalConfig"/>
        <div v-else ref="input_number" class="flex justify-center">
            {{ defaultValues.quantity }}
        </div>
    </a-form-model-item>
</template>

<script>
import VueAutonumeric from 'vue-autonumeric'
let time;
export default {
    components: {
        VueAutonumeric
    },
    props: {
        form: {
            type: Object,
            required: true
        },
        smallForm: {
            type: Boolean,
            default: false
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        defaultValues: {
            type: Object,
            default: () => null
        },
        changeCount: {
            type: Function,
            default: () => {}
        },
        count: {
            type: [String, Number],
            required: true
        },
        liveUpdate: {
            type: Boolean,
            default: false
        },
        uniqKey: {
            type: [String, Number],
            default: 'warehouse'
        },
        changeAmountQuantity: {
            type: Function,
            default: () => {}
        },
        countInputChange: {
            type: Function,
            default: () => {}
        },
        inputBlur: {
            type: Function,
            default: () => {}
        },
        measureUnitName: {
            type: String,
            default: ''
        },
        warehouseId: {
            type: String,
            default: ''
        },
        disabled: {
            type: Boolean,
            default: true
        },
    },
    data () {
        return {
            decimalConfig: {
                decimalLength: 3,
                decimalPlaces: 3,
                maxValue: "1000000000000000000000",
                minValue: "-1000000000000000000000"
            },
            demicalLenght: 3,
            start: false,
            oldValue: null,
            newCount: 0
        }
    },
    computed: {
        quantityInMeasureUnits: {
            get() {
                return this.form.coefficient * this.count
            },
            set(value) {
                this.newCount = value / this.form.coefficient
            }
        },
        label() {
            if(this.measureUnitName)
                return `Кол-во в ${this.measureUnitName}`
            return 'Кол-во в выбранных ед. изм.'
        }
    },
    created () {
        if(!this.disabled) {
            this.$nextTick(() => {
                this.$refs['input_number'].$refs['autoNumericElement'].addEventListener('blur', event => {
                    this.afterSetValue()
                })
            })
        }
    },
    methods: {
        inputChange(value, e) {
            // let selectionStart = 1
            // let afterLength = value.toString().split('.')[0]

            // if(afterLength) {
            //     afterLength = Number(afterLength).toLocaleString('ru').toString().length
            // }

            // if(e) {
            //     selectionStart = e.target.selectionStart
            // }

            // let replaceValue = value

            // replaceValue = replaceValue.toFixed(this.demicalLenght)

            // if(!/^[0-9]*$/.test(replaceValue)) {
            //     let beforeLength = replaceValue.toString().split('.')[1].length
            //     // console.log(beforeLength, 'beforeLength')
            // }

            // this.$nextTick(() => {
            //     const input = this.$refs.input_number.$refs.autoNumericElement
            //     input.setSelectionRange(afterLength, afterLength)
            // })

            // if(this.liveUpdate && this.start) {
            //     this.changeAmountQuantity()
            //     clearTimeout(time)

            //     setTimeout(() => {
            //         this.changeCount(null, {[quantityInMeasureUnits]: this.form[quantityInMeasureUnits] || 1})
            //     }, 800)
            // }
        },
        afterSetValue() {
            this.countInputChange(this.newCount, this.warehouseId)
            this.inputBlur()
        }
    },
}
</script>