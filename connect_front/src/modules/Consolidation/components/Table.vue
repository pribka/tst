<template>
    <div class="flex flex-grow flex-col">
        <UniversalTable 
            :model="model"
            :pageName="page_name"
            :tableType="tableType"
            :openHandler="openConsolidation"
            :showChildren="true"
            :extendDrawer="false"
            :params="params"
            :endpoint="endpoint" />
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        page_name: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        },
        tableType: {
            type: String,
            default: 'consolidation'
        },
        params: {
            type: Object,
            default: () => {}
        },
    },
    computed: {
        endpoint() {
            return `/consolidation/`
        }
    },
    methods: {
        openConsolidation(id) {
            const query = Object.assign({}, this.$route.query)
            if(query.consolidation && query.consolidation !== id || !query.consolidation) {
                query.consolidation = id
                this.$router.push({query})
            }
        },
    },
}
</script>