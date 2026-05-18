<template>
    <a-form-model-item 
        :ref="field.key" 
        :label="field.name"
        class="form_item"
        :prop="field.key"
        :rules="field.rules">
        <a-input
            :size="field.size"
            v-model="form[field.key]"
            :placeholder="field.placeholder" />
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
    },
    beforeDestroy() {
        this.form[this.field.key] = null
    }
}
</script>