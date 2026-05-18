<template>
    <component 
        :is="widget"
        :form="form"
        :item="item"
        :field="field" />
</template>

<script>
export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.field.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`../NotWidget.vue`)
                })
        }
    }
}
</script>