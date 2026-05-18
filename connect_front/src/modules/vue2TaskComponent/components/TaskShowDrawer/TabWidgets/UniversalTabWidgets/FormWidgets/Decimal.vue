<template>
    <vue-autonumeric
        ref="input_number"
        class="ant-input w-full"
        :class="fieldSize === 'large' && 'ant-input-lg'"
        :disabled="fieldDisabled"
        @input="inputChange"
        v-model="form[field.key]"
        :options="decimalConfig"/>
</template>

<script>
import fieldMixins from './fieldMixins.js'
import VueAutonumeric from 'vue-autonumeric'
export default {
    components: {
        VueAutonumeric
    },
    mixins: [
        fieldMixins
    ],
    computed: {
        demicalLenght() {
            return this.field.demicalLenght ? this.field.demicalLenght : 3
        },
        decimalConfig() {
            return this.field.decimalConfig
        }
    },
    methods: {
        inputChange(value, e) {
            // console.log(e, 'e')

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

            /*if(/^[0-9]*$/.test(replaceValue)) {
                replaceValue = replaceValue.toFixed(this.demicalLenght)
            }*/

            if(!/^[0-9]*$/.test(replaceValue)) {
                let beforeLength = replaceValue.toString().split('.')[1].length
                // console.log(beforeLength, 'beforeLength')
            }

            /*if (replaceValue.indexOf('.') > -1) {
                let splitReplace = replaceValue.split('.')[1]
                let parse = 0
                if(splitReplace.length === 1)
                    parse = '00'
                if(splitReplace.length === 2)
                    parse = 0

                replaceValue = replaceValue + parse
            } else {
                replaceValue = parseFloat(replaceValue).toFixed(this.demicalLenght)
            }*/

            this.$nextTick(() => {
                const input = this.$refs.input_number.$refs.autoNumericElement
                input.setSelectionRange(afterLength, afterLength)
            })
        }
    }
}
</script>