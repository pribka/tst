<template>
    <div>
        <PageFilter 
            model="tasks.TaskModel"
            :key="widget.page_name"
            ref="filter"
            size="large"
            :page_name="pageName" />
        <a-divider class="mt-1" />
        <UniversalTableSetting 
            tableType="tasks"
            ref="tableSetting"
            model="tasks.TaskModel"
            :pageName="pageName"
            :updateData="updateData" />
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
        PageFilter: () => import('@/components/PageFilter/PageWidget.vue'),
        UniversalTableSetting: () => import('@/components/TableWidgets/UniversalTableSetting.vue')
    },
    computed: {
        pageName() {
            return (this.widget.page_name || this.widget.id) || this.widget.widget.id
        }
    },
    methods: {
        updateData() {

        },
        saveConfig() {
            this.$nextTick(() => {
                this.$refs.filter.setFilter()
                this.$refs.tableSetting.setColumns()
                this.closeSettingDrawer()
            })
        },
        resetConfig() {
            this.$nextTick(() => {
                this.$refs.filter.removeFilters()
                this.$refs.tableSetting.dropColumns()
                this.closeSettingDrawer()
            })
        }
    }
}
</script>