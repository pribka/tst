<template>
    <component 
        :is="viewComp" 
        :partType="partType" 
        :partCode="partCode" />
</template>

<script>
export default {
    props: {
        partType: {
            type: String,
            default: 'sections'
        },
        partCode: {
            type: String,
            required: true
        },
        type: {
            type: String,
            default: 'text'
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        viewComp() {
            if(this.type === 'button') {
                if(this.isMobile)
                    return () => import('./HelpButtonButtonMobile.vue')
                return () => import('./HelpButtonButton.vue')
            }
            if(this.isMobile)
                return () => null
            return () => import('./HelpButtonText.vue')
        }
    }
}
</script>