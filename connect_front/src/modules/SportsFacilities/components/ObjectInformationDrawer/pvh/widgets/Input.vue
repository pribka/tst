<template>
    <a-input 
        v-model="form[`x_${widget.property.code}`]"
        size="large" 
        :placeholder="placeholder"
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
        }
    }
}
</script>