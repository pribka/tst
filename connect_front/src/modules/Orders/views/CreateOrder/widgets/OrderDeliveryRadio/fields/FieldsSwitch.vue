<template>
    <component 
        :is="widget"
        :form="form"
        :edit="edit"
        :isOrderDrawer="isOrderDrawer"
        :setOrderFormCalculated="setOrderFormCalculated"
        :field="field" />
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
        edit: {
            type: Boolean,
            default: false
        },
        isOrderDrawer: {
            type: Boolean,
            default: false
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.field.widget}`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`../../NotWidget.vue`)
                })
        }
    }
}
</script>