<template>
    <div class="contract_project_tickets_table" ref="wrapRef">
        <UniversalTable
            ref="ticketTable"
            :model="model"
            class="min-h-0"
            :pageName="normalizedPageName"
            tableType="helpdesk_tickets"
            :main="false"
            :hash="false"
            extendDrawer
            :params="queryParams"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
            endpoint="/help_desk/tickets/" />
    </div>
</template>

<script>
export default {
    name: 'ContractProjectTicketsTableDesktop',
    sockets: {
        ticket_update({ data }) {
            if (data) {
                this.updateItem(data)
            }
        },
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
    },
    props: {
        projectId: {
            type: [String, Number],
            required: true,
        },
        contractId: {
            type: String,
            required: true,
        },
        customerCardId: {
            type: [String, Number],
            default: null,
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    data() {
        return {
            model: 'help_desk.HelpDeskTicketModel',
        }
    },
    computed: {
        normalizedPageName() {
            return this.pageName || `deals.contract_project_tickets_${this.contractId}_${this.projectId}`
        },
        queryParams() {
            return {
                contract: this.contractId,
                project: this.projectId,
            }
        },
    },
    methods: {
        loadData() {
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
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_project_tickets_table {
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 460px;
    height: 100%;
}
</style>
