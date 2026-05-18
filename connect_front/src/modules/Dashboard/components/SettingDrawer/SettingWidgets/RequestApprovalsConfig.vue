<template>
    <div>
        <PageFilter 
            model="processes.WorkflowRequestModel"
            :key="widget.page_name"
            ref="filter"
            size="large"
            :page_name="widget.page_name" />
    </div>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        closeSettingDrawer: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        PageFilter: () => import('@/components/PageFilter/PageWidget.vue')
    },
    methods: {
        saveConfig() {
            this.$nextTick(() => {
                this.$refs.filter.setFilter()
                this.closeSettingDrawer()
            })
        },
        resetConfig() {
            this.$nextTick(() => {
                this.$refs.filter.removeFilters()
                this.closeSettingDrawer()
            })
        }
    }
}
</script>