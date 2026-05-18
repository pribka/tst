<template>
    <div class="h-full flex flex-col min-h-0">
        <UniversalTable
            ref="callsTable"
            class="flex-1 min-h-0"
            :model="model"
            :pageName="page_name"
            tableType="ticket_calls"
            endpoint="/meetings/calls/"
            :params="queryParams"
            :main="false"
            extendDrawer
            :hash="false" />
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        }
    },
    computed: {
        queryParams() {
            return {
                ticket: this.ticket.id
            }
        }
    },
    methods: {
        updateData() {
            this.$nextTick(() => {
                this.$refs.callsTable?.reloadTableData?.()
            })
        }
    }
}
</script>
