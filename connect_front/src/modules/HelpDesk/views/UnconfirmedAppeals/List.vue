
<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable 
            ref="ticketTable"
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            :params="{ display: 'leads' }"
            tableType="helpdesk_tickets"
            :colParams="{
                getPopupContainer: getPopupContainer,
                useSpam: true
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
            endpoint: '/help_desk/tickets/'
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.wrapRef
        },
        listReload() {
            this.$nextTick(() => {
                this.$refs.ticketTable.reloadTableData()
            })
        }
    }
}
</script>