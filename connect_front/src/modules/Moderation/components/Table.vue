<template>
    <UniversalTable
        :model="pageModel"
        :pageName="pageName"
        :tableType="tableType"
        :endpoint="endpoint"
        :openHandler="openHandler" />
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    data() {
        return {
            pageModel: 'catalogs.ContractorProfileRequestModel',
            pageName: 'catalogs.ContractorProfileRequestModel',
            tableType: 'moderation',
            endpoint: '/catalogs/profile_requests/'
        }
    },
    methods: {
        openHandler(record) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query?.organization_drawer) {
                query.organization_drawer = 'detail'
                query.organization_id = record.organization.id
                this.$router.replace({query})
            }
        }
    }
}
</script>