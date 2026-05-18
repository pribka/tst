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
import UniversalTable from '@/components/TableWidgets/UniversalTable'
export default {
    components: {
        UniversalTable,
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
            default: 'sports_facilities'
        },
        params: {
            type: Object,
            default: () => {}
        },
    },
    computed: {
        endpoint() {
            return '/sports_facilities/'
        }
    },
    methods: {
        onRowClicked(event) {
            this.$router.push({ name: 'full_sports_facilities_gallery', params: { id: event.data.id } })
        }
    },
}
</script>