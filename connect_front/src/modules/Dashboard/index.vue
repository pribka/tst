<template>
    <component :is="dashboardLayout" />
</template>

<script>
import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        })
    },
    data() {
        return {
            dashboardLayout: null
        }
    },
    created() {
        this.dashboardLayout = this.isMobile
            ? () => import('./components/List.vue')
            : () => import('./components/Desktop.vue')
    }
}
</script>