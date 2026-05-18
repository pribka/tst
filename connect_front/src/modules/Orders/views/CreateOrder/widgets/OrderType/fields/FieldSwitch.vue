<template>
    <a-form-model-item 
        :ref="field.key" 
        :label="field.name" 
        :prop="field.key"
        :rules="rules">
        <component 
            :is="fieldWidget" 
            :form="form"
            :visible="visible"
            :checkboxHidden="checkboxHidden"
            :field="field" />
    </a-form-model-item>
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
        visible: {
            type: Boolean,
            default: false
        },
        mainForm: {
            type: Object,
            required: true
        },
        checkboxHidden: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        rules() {
            if(this.field.depends) {
                let required = false
                for(let key in this.field.depends) {
                    if(this.mainForm[key] === this.field.depends[key]) {
                        required = true
                    } else {
                        required = false
                    }
                }
                
                if(required) {
                    return {
                        message: "Обязательно для заполнения",
                        required: true,
                        trigger: "blur"
                    }
                } else
                    return null
            } else
                return this.field.rules
        },
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