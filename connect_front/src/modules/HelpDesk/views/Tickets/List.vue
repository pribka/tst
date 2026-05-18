<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable 
            ref="ticketTable"
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            tableType="helpdesk_tickets"
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
    sockets: {
        ticket_update({ data }) {
            if (data) {
                this.updateItem(data)
            }
        }
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
        listReload() {
            this.$nextTick(() => {
                this.$refs.ticketTable?.reloadTableData?.()
            })
        },
        updateItem(data) {
            const table = this.$refs.ticketTable
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(data)
            }
        },
        getPopupContainer() {
            return this.$refs.wrapRef
        }
    }
}
</script>
