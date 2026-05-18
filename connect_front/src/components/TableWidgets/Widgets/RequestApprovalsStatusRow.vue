<template>
    <a-tag :color="record.status.color" size="large" block>
        {{ record.status.name || record.status.code }}
    </a-tag>
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
        }
    }
}
</script>