<template>
    <a-textarea 
        v-model="form[`x_${widget.property.code}`]"
        size="large" 
        :placeholder="placeholder"
        :autoSize="autoSize"
        class="w-full" />
</template>

<script>
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
        placeholder() {
            return this.widget.widget.placeholder || ''
        },
        autoSize() {
            return this.widget.widget.autoSize || { minRows: 2, maxRows: 3 }
        }
    }
}
</script>