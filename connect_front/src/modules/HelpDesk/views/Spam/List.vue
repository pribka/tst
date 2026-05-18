
<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable 
            ref="ticketTable"
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            :params="{ filters: { spam: true } }"
            tableType="helpdesk_spam"
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
            endpoint: '/help_desk/contact_persons/'
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