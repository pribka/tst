<template>
    <TableName
        :record="record"
        :text="text"
        v-model="expandedRowKeys"
        :main="main"
        :extendDrawer="extendDrawer"
        :reloadTask="reloadTask"
        :showChildren="showChildren"
        :pageName="pageName"
        :childParams="childParams"
        :expanded="expanded"
        :indent="indent" />
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
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
        openTask: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        },
        childParams: {
            type: Object,
            default: () => null
        }
    },
    components: {
        TableName: () => import('@apps/vue2TaskComponent/components/TaskList/TableName')
    }
}
</script>