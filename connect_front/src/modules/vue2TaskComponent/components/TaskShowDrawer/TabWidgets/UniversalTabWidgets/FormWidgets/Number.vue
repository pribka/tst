<template>
    <a-input-number
        v-model="form[field.key]"
        :size="fieldSize" 
        :min="fieldMin"
        :max="fieldMax"
        :disabled="fieldDisabled"
        :step="fieldStep"
        class="w-full"
        @pressEnter="formSubmit" />
</template>

<script>
import fieldMixins from './fieldMixins.js'
export default {
    mixins: [
        fieldMixins
    ],
    computed: {
        fieldMin() {
            return this.field.min ? this.field.min : 0
        },
        fieldMax() {
            return this.field.max ? this.field.max : 100
        },
        fieldStep() {
            return this.field.step ? this.field.step : 1
        }
    }
}
</script>