<template>
    <component 
        :is="widget"
        :item="item"
        :size="size"/>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        size: {
            type: String,
            default: 'small'
        }
    },   
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        widget() {
            if(this.isMobile)
                return () => import('./Availability/indexMobile')
            return () => import('./Availability/index')

        }
    }

}
</script>