<template>
    <component 
        :is="calendarComponent" 
        :uKey="uKey" 
        :related_object="related_object" 
        :addEventCheck="addEventCheck" />
</template>

<script>
export default {
    props: {
        uKey: {
            type: [String, Number],
            default: 'default'
        },
        related_object: {
            type: [String, Number],
            default: null
        },
        addEventCheck: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            calendarComponent: null
        }
    },
    created() {
        this.calendarComponent = this.isMobile
            ? () => import('./Mobile.vue')
            : () => import('./Desktop.vue')
    }
}
</script>