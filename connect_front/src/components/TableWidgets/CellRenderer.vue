<template>
    <div class="h-full">
        <component 
            :is="cellWidget"
            
            :record="params.data"
            :text="params.value"
            :tableType="params.tableType"
            :column="params.colDef"
            
            :state="params.state"
            :changeState="params.changeState"
            :pageModel="params.pageModel"
            :params="params"
            :reloadTableData="params.reloadTableData"
            :colParams="params.colParams"
            :model="params.model"
            :taskType="params.taskType"
            :pageName="params.pageName"
            :id="params.data?.id"

            :takeTask="params.takeTask"
            :reason="params.value"
            :openHandler="params.openHandler"
            :expandedRowKeys="params.expandedRowKeys"
            :main="params.main"
            :extendDrawer="params.extendDrawer"
            :reloadTask="params.reloadTask"
            :showChildren="params.showChildren"

            :startEdit="params.startEdit"
            :deleteSprint="params.deleteSprint"
            :updateStatus="params.updateStatus"

            :expanded="params.expanded"
            :indent="params.indent"
            :childParams="params.childParams"
            :getInvoicePayment="params.getInvoicePayment"
            
            :selectedRows="params.selectedRows"
            :onSelectChange="params.onSelectChange"
            :mode="params.mode"

            :openModalStat="params.openModalStat"
            :openDescModal="params.openDescModal"/>
    </div>
</template>

<script>
export default {
    computed: {
        cellWidget() {
            return () => import(`./Widgets/${this.params.colDef.widget}`)
                .then(module => {
                    return module
                })
                .catch(error => {
                    console.error(error)
                    return import(`./NotWidget.vue`)
                })
        }
    }

}
</script>