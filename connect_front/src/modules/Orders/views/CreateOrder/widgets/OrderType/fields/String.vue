<template>
    <a-input 
        v-model="form[field.key]" 
        size="large" />
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
        }
    }
}
</script>