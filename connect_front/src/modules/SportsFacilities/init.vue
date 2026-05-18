<template>
    <AddDrawer />
</template>

<script>
import store from "./store/index"
export default {
    components: {
        AddDrawer: () => import('./components/AddDrawer.vue')
    },
    beforeCreate() {
        if(!this.$store.hasModule('facilities')) {
            this.$store.registerModule("facilities", store)
        }
    }
}
</script>