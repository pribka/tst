<template>
    <a-input-number 
        v-model="form[`x_${widget.property.code}`]"
        size="large" 
        class="w-full" 
        :step="step"
        :parser="decParser"
        :min="min"
        :max="max"
        :placeholder="placeholder"
        decimalSeparator="." /> 
</template>

<script>
import { decParser } from '../../../../utils.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        step() {
            return this.widget.widget.step || 0.1
        },
        min() {
            return this.widget.widget.min || 1
        },
        max() {
            return this.widget.widget.max || 1000000
        },
        placeholder() {
            return this.widget.widget.placeholder || ''
        }
    },
    methods: {
        decParser
    }
}
</script>