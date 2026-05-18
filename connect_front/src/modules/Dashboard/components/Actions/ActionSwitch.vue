<template>
    <component 
        :is="actionWidget" 
        :widget="widget" 
        :editNameHandler="editNameHandler" />
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        editNameHandler: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        actionWidget() {
            if(this.isMobile) {
                return () => import('./Mobile.vue')
            } else {
                return () => import('./Desktop.vue')
            }
        }
    }
}
</script>