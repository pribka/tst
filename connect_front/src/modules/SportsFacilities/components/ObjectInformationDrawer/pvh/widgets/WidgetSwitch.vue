<template>
    <a-form-model-item 
        :ref="`x_${widget.property.code}`" 
        :label="widget.name" 
        :rules="rules"
        :prop="`x_${widget.property.code}`">
        <component 
            :is="widgetType" 
            :form="form"
            :setSelectsList="setSelectsList"
            :widget="widget" />
    </a-form-model-item>
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
        },
        setSelectsList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        rules() {
            return this.widget.widget?.rules || null
        },
        widgetType() {
            if(this.widget.widget?.type) {
                return () => import(`./${this.widget.widget.type}.vue`)
                    .then(module => {
                        return module
                    })
                    .catch(error => {
                        console.error(error)
                        return import(`./NotWidget.vue`)
                    })
            }
            return import(`./NotWidget.vue`)
        }
    }
}
</script>