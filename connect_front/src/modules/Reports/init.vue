<template>
    <component :is="GenerateReportModal" v-if="visible" />
</template>

<script>
import store from "./store/index"
export default {
    name: "ProductivityReportsInit",
    computed: {
        visible() {
            return this.$store.state.reports.reportModalVisibleCheck
        },
        GenerateReportModal() {
            if(this.visible)
                return () => import('./components/GenerateReportModal.vue')
            return null
        }
    },
    created() {
        if(!this.$store.hasModule('reports')) {
            this.$store.registerModule("reports", store)
            this.$store.commit('ADD_CONNECTED_MODULES', 'reports')
        }
    }
}
</script>