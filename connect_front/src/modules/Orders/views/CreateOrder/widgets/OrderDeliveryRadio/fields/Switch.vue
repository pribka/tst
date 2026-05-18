<template>
    <a-form-model-item
        :ref="field.key" 
        :label="field.name"
        class="form_item"
        :prop="field.key"
        :rules="field.rules || null">
        <a-switch v-model="form[field.key]" />
    </a-form-model-item>
</template>

<script>
export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    }
}
</script>