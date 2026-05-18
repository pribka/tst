<template>
    <a-checkbox v-model="form[field.key]">{{ field.checkboxLabel || 'Нет заголовка' }}</a-checkbox>
</template>

<script>
export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        field: {
            type: Object,
            required: true
        },
        checkboxHidden: {
            type: Boolean,
            default: false
        }
    }
}
</script>