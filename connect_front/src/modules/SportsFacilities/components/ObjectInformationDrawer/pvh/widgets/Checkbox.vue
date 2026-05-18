<template>
    <a-checkbox v-model="form[`x_${widget.property.code}`]">
        {{ checkTitle }}
    </a-checkbox>
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
        checkTitle() {
            return this.widget.widget.title || this.widget.name
        }
    }
}
</script>