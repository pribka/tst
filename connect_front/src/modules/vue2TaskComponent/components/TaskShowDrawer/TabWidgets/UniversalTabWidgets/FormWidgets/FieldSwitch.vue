<template>
    <a-form-model-item 
        :ref="field.key" 
        :label="field.label" 
        :prop="field.key"
        :rules="field.rules">
        <component 
            :is="fieldWidget" 
            :field="field"
            :formSubmit="formSubmit"
            :form="form"
            :edit="edit"
            :code="code"
            :task="task" />
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
        },
        task: {
            type: Object,
            default: () => null
        },
        formSubmit: {
            type: Function,
            required: true
        },
        code: {
            type: [String, Number],
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        fieldWidget() {
            return () => import(`./${this.field.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>