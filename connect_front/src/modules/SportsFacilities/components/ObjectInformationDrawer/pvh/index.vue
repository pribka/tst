<template>
    <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
        <WidgetSwitch 
            v-for="widget in pvhWidgets" 
            :key="widget.id"
            :form="form"
            :setSelectsList="setSelectsList"
            :widget="widget" />
    </div>
</template>

<script>
import WidgetSwitch from './widgets/WidgetSwitch.vue'
export default {
    components: {
        WidgetSwitch
    },
    props: {
        pvhWidgets: {
            type: Array,
            default: () => []
        },
        form: {
            type: Object,
            default: () => {}
        },
        setSelectsList: {
            type: Function,
            default: () => {}
        }
    }
}
</script>