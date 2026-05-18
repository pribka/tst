<template>
    <a-input-number 
        v-model="form[`x_${widget.property.code}`]"
        size="large" 
        :min="min"
        :max="max"
        :placeholder="placeholder"
        class="w-full"
        @keypress="handleKeyPress" />
</template>

<script>
import { handleKeyPress } from '../../../../utils.js'
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
        handleKeyPress
    }
}
</script>