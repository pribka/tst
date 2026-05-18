<template>
    <a-textarea
        v-model="form[field.key]"
        class="w-full"
        :placeholder="fieldPlaceholder"
        :disabled="fieldDisabled"
        :auto-size="fieldAutoSize"/>
</template>

<script>
import fieldMixins from './fieldMixins.js'
export default {
    mixins: [
        fieldMixins
    ],
    computed: {
        fieldAutoSize() {
            return this.field.autoSize ? this.field.autoSize : 0
        },
        fieldAllowClear() {
            return this.field.allowClear ? this.field.allowClear : 0
        }
    }
}
</script>