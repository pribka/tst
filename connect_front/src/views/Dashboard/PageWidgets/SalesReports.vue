<template>
    <Reports />
</template>

<script>
import reportsStore from '@apps/Reports/store'

export default {
    name: 'SalesReportsPage',
    components: {
        Reports: () => import('@apps/Reports')
    },
    created() {
        if (!this.$store.hasModule('reports')) {
            this.$store.registerModule('reports', reportsStore)
            this.$store.commit('ADD_CONNECTED_MODULES', 'reports')
        }
    }
}
</script>
