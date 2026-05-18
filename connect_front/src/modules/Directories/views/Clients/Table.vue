<template>
    <UniversalTable 
        :model="initPageModel"
        class="flex-grow"
        :pageName="initPageName"
        tableType="clients"
        :endpoint="endpoint" />
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        }
    },
    data() {
        return {
            endpoint: '/help_desk/customer_cards/'
        }
    }
}
</script>