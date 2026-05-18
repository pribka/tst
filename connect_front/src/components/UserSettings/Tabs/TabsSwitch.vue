<template>
    <component :is="pageWidget"/>
</template>

<script>
export default {
    props: {
        activeItem: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        pageWidget() {
            return () => import(`./${this.activeItem.widget}.vue`)
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