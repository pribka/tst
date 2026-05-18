<template>
    <component 
        :is="cellWidget" 
        
        :column="column"
        :record="record"
        :text="text"
        :model="model"
        :tableType="tableType"
        :taskType="taskType"
        :pageName="pageName"
        :id="record?.id"

        :state="params.state"
        :changeState="params.changeState"

        :takeTask="takeTask"
        :reason="text"
        :openHandler="openHandler"
        :expandedRowKeys="expandedRowKeys"
        :main="main"
        :extendDrawer="extendDrawer"
        :reloadTask="reloadTask"
        :showChildren="showChildren"

        :startEdit="startEdit"
        :deleteSprint="deleteSprint"
        :updateStatus="updateStatus"

        :expanded="expanded"
        :indent="indent"
        :getInvoicePayment="getInvoicePayment"
        
        :openModalStat="openModalStat"
        :openDescModal="openDescModal" />
</template>

<script>
export default {
    props: {
        state: {
            type: Object,
            default: () => {}
        },
        changeState: {
            type: Function,
            default: () => {}
        },

        getInvoicePayment: {
            type: Function,
            default: () => {}
        },
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        model: String,
        pageName: String,
        taskType: { type: String, default: ''},
        tableType: {
            type: String
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String, Boolean, Array],
        },
        expandedRowKeys: {
            type: Array,
        },
        expanded: {
            type: Number,
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        indent: {
            type: Object,
        },
        column: {
            type: Object,
            default: () => null
        },
        openHandler: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },

        startEdit: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        updateStatus: {
            type: Function,
            default: () => {}
        },
        openDescModal: {
            type: Function,
            default: () => {}
        },
        openModalStat: {
            type: Function,
            default: () => {}
        },
        takeTask: {
            type: Function,
            default: () => {}    
        }
    },
    computed: {
        cellWidget() {
            return () => import(`./Widgets/${this.column.widget}`)
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

<!-- 
    :task="task"
        :myTask="myTask"
        :reloadTask="reloadTask"
        :dropActions="dropActions"
        :checkRole="checkRole"
        :getCommentsCount="getCommentsCount"
        :edit="edit"
        :tab="tab"
        :code="code"
        :hideDeliveryMap="hideDeliveryMap"
        :openTask="openTask"
        :isMobile="isMobile"
        :isOperator="isOperator"
        :isAuthor="isAuthor" 
         -->