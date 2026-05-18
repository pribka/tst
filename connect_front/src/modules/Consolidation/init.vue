<template>
    <div>
        <component :is="consolidationShowDrawerAsync" v-if="$route.query.consolidation" isProject />

        <ConsolidationFileView />
        <ReportView />
    </div>
</template> 

<script>
export default {
    components: {
        ConsolidationFileView: () => import('./components/ConsolidationFileView.vue'),
        ReportView: () => import('./components/ReportView.vue')
    },
    data() {
        return {
            consolidationShowDrawerAsync: null,
        }
    },
    watch: {
        '$route.query.consolidation': {
            immediate: true,
            handler(v) {
                if (v && !this.consolidationShowDrawerAsync)
                    this.consolidationShowDrawerAsync = () => import(/* webpackChunkName: "consolidation-show-drawer" */ './components/ConsolidationView/index.vue')
            }
        }
    },
}
</script>