<template>
    <component 
        :is="widgetComponent" 
        :widget="widget" />
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        widgetComponent() {
            return () => import(`./Widgets/${this.widget.widget.widget_component}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./Widgets/NotWidget.vue`)
                })
        }
    }
}
</script>