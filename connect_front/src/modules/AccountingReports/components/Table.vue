<template>
    <div class="h-full flex">
        <UniversalTable
            :model="model"
            :pageName="pageName"
            :tableType="tableType"
            :endpoint="endpoint" />
    </div>
</template>

<script>
import UniversalTable from '@/components/TableWidgets/UniversalTable.vue'

export default {
    components: {
        UniversalTable
    },
    props: {
        model: {
            type: String,
            default: 'accounting_reports.AccountingReportBaseModel'
        },
        pageName: {
            type: String,
            default: 'accounting_reports'
        }
    },
    data() {
        return {
            tableType: 'accounting_reports'
        }
    },

    computed: {
        endpoint() {
            return `/accounting_reports/`
        }
    },
}
</script>