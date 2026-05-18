<template>
    <div class="flex flex-grow flex-col">
        <UniversalTable 
            :model="model"
            :pageName="page_name"
            :tableType="tableType"
            :showChildren="true"
            :extendDrawer="false"
            :params="params"
            :endpoint="endpoint"
            :onRowClicked="onRowClicked" />
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
            default: 'invest_projects'
        },
        params: {
            type: Object,
            default: () => {}
        },
    },
    computed: {
        endpoint() {
            return '/invest_projects_info/'
        }
    },
    methods: {
        onRowClicked(event) {
            this.$router.push({ name: 'full_invest_project_info', params: { id: event.data.id } })
        }
    },
}
</script>