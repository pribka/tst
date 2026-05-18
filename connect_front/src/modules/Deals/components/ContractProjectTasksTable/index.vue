<template>
    <component
        :is="viewComponent"
        ref="view"
        :projectId="projectId"
        :contractId="contractId"
        :pageName="pageName"
        @open="$emit('open', $event)" />
</template>

<script>
export default {
    name: 'ContractProjectTasksTable',
    props: {
        projectId: {
            type: [String, Number],
            required: true,
        },
        contractId: {
            type: String,
            required: true,
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            return this.isMobile
                ? () => import('./ListView.vue')
                : () => import('./Table.vue')
        },
    },
    methods: {
        loadData() {
            return this.$refs.view?.loadData?.()
        },
    },
}
</script>
