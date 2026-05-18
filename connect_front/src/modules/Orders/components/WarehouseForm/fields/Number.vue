<template>
    <vue-autonumeric
        ref="input_number"
        class="ant-input field_width w-full"
        :class="inputSize === 'small' && 'ant-input-sm'"
        @input="inputChange"
        v-model="form[field.key]"
        :options="decimalConfig"/>
</template>

<script>
import VueAutonumeric from 'vue-autonumeric'
import eventBus from '@/utils/eventBus.js'
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
        field: {
            type: Object,
            required: true
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
        }
    },
    data () {
        return {
            decimalConfig: {
                decimalLength: 6,
                decimalPlaces: 6,
                maxValue: "1000000000000000000000",
                minValue: "-1000000000000000000000"
            },
            demicalLenght: 6,
            start: false,
            oldValue: null
        }
    },
    created () {
        this.oldValue = this.form[this.field.key]
        if(this.defaultValues?.[this.field.key]) {
            this.form[this.field.key] = this.defaultValues[this.field.key] || null
            this.oldValue = this.defaultValues[this.field.key] || null
            this.changeAmountQuantity()
            setTimeout(() => {
                this.start = true
            }, 200)
        }
    },
    methods: {
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

            if(this.liveUpdate && this.start) {
                this.changeAmountQuantity()
                clearTimeout(time)

                setTimeout(() => {
                    this.changeCount(null, {[this.field.key]: this.form[this.field.key] || 1})
                }, 800)
            }
        }
    },
    mounted() {
        if(this.field.depends_on?.length) {
            this.field.depends_on.forEach(item => {
                eventBus.$on(`change_field_${item}_${this.uniqKey}`, baseValue => {
                    if(baseValue) {
                        this.form[this.field.key] = this.oldValue
                    } else {
                        this.form[this.field.key] = ''
                    }
                })
            })
        }
    },
    beforeDestroy() {
        if(this.field.depends_on?.length) {
            this.field.depends_on.forEach(item => {
                eventBus.$off(`change_field_${item}_${this.uniqKey}`)
            })
        }
    }
}
</script>