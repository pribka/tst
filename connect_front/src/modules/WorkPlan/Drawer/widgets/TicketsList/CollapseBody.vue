<template>
    <div class="ticket_collapse_body">
        <a-tabs v-model="tab" class="collapse_tabs" :showBar="showResultTab">
            <a-tab-pane v-if="showResultTab" key="result" :tab="$t('workplan.ticket_result_tab')">
                <CompletedBanner :ticket="detailTicket" />
            </a-tab-pane>
            <a-tab-pane key="accounting" :tab="$t('workplan.ticket_accounting_tab')">
                <Accounting
                    :ticket="detailTicket"
                    :actions="actions" />
            </a-tab-pane>
        </a-tabs>
    </div>
</template>

<script>
export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
        detail: {
            type: Object,
            default: () => null
        },
        showResultTab: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Accounting: () => import('@/modules/HelpDesk/components/Tickets/TicketDrawer/tabs/Accounting/index.vue'),
        CompletedBanner: () => import('@/modules/HelpDesk/components/Tickets/TicketDrawer/components/ChatList/CompletedBanner.vue')
    },
    computed: {
        detailTicket() {
            return this.detail || this.ticket
        },
        actions() {
            return this.detailTicket?.actions || this.ticket?.actions || null
        }
    },
    data() {
        return {
            tab: 'accounting'
        }
    },
    watch: {
        showResultTab: {
            immediate: true,
            handler(value) {
                this.tab = value ? 'result' : 'accounting'
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.ticket_collapse_body{
    min-height: 120px;
}
.collapse_tabs{
    &.ant-tabs.ant-tabs-top{
        &::v-deep{
            .ant-tabs-bar.ant-tabs-top-bar{
                display: block;
            }
        }
    }
}
</style>
