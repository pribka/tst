<template>
    <div ref="wrapRef" class="flex-grow flex flex-col">
        <UniversalTable 
            :model="model"
            class="min-h-0"
            :pageName="page_name"
            tableType="helpdesk_tickets"
            :main="false"
            :hash="false"
            extendDrawer
            :params="{
                customer_card: client.id
            }"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
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
            default: ""
        },
        model: {
            type: String,
            default: ""
        },
        actions: {
            type: Object,
            required: true
        },
        client: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            endpoint: '/help_desk/tickets/'
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.wrapRef
        }
    }
}
</script>