<template>
    <component 
        :is="columnWidget" 
        :column="column"
        :row="row"
        :task="task"
        :code="code"
        :allColumns="allColumns"
        :item="item"
        :actionsAsBlock="actionsAsBlock"
        :actionsButtonType="actionsButtonType" />
</template>

<script>
import widgetMixins from './widgetMixins.js'
export default {
    mixins: [
        widgetMixins
    ],
    computed: {
        columnWidget() {
            return () => import(`./${this.column.scopedSlots.customRender}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>