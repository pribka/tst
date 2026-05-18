<template>
    <AddObjective />
</template>

<script>
import okr from "./store/index.js"
export default {
    components: {
        AddObjective: () => import('@apps/OKR/components/AddObjective.vue')
    },
    created() {
        if (!this.$store.hasModule('okr')) {
            this.$store.registerModule('okr', okr)
            this.$store.commit('ADD_CONNECTED_MODULES', 'okr')
        }
    }
}
</script>