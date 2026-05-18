<template>
    <ComplexFilterList v-model="elements" :parentPath="[]" />
</template>

<script>
export default {
    components: { 
        ComplexFilterList: () => import('./ComplexFilterList.vue')
    },
    computed: {
        elements: {
            get() {
                return this.$store.state.reports.activeTemplate.metadata.complexFilters
            },
            set(value) {
                this.$store.commit("reports/UPDATE_COMPLEX_FILTER_LIST", value);
            }
            
        },
    },
    methods: {
        isGroup(to) {
            console.log(to)
            return to?.dataset?.type === 'group' || true;
        }
    }
};
</script>
