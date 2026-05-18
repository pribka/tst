<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable
            :model="pageModel"
            ref="tableWidget"
            class="flex-grow"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
            :pageName="page_name"
            tableType="workflow_requests"
            endpoint="/processes/workflow_requests/" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    props: {
        page_name: {
            type: String,
            required: true
        },
        pageModel: {
            type: String,
            required: true
        }
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
    },
    sockets: {
        workflow_request_update({data}){
            if(data)
                this.syncItem(data)
        }
    },
    mounted() {
        eventBus.$on('request_approvals_comments_seen', this.markNewCommentsSeen)
    },
    beforeDestroy() {
        eventBus.$off('request_approvals_comments_seen', this.markNewCommentsSeen)
    },
    methods: {
        markNewCommentsSeen(data) {
            if(!data?.id) return
            this.updateItem({
                id: data.id,
                has_new_comments: false
            })
        },
        syncItem(data) {
            const table = this.$refs.tableWidget
            if (!table) return

            const rowIndex = typeof table.findRowIndex === 'function'
                ? table.findRowIndex(data)
                : -1

            if (rowIndex === -1 && typeof table.prependRow === 'function')
                table.prependRow(data)
            else
                this.updateItem(data)
        },
        updateItem(data) {
            const table = this.$refs.tableWidget
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
