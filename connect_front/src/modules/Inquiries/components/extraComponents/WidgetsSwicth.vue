<template>
    <component 
        ref="widgetSwitch"
        :is="widget"
        :form="form"
        :item="item"
        :categoryDetails="categoryDetails"
        @deleteExtraKeys="deleteExtraKeys" />
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        categoryDetails: {
            type: Object,
            required: true
        },
        deleteExtraKeys: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.item.widget}`)
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