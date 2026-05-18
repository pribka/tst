<template>
    <keep-alive>
        <component 
            :is="component"
            showPageTitle
            :pageName="pageName" >
            <template #pageFilter>
                <PageFilter
                    :model="model"
                    :key="pageName"
                    size="large"
                    :page_name="pageName"/>
            </template>
            <template #addButton>
                <a-button
                    type="primary"
                    flaticon
                    icon="fi-rr-plus"
                    size="large"
                    @click="openCreateDrawer">
                    {{ $t('reports.add_report') }}
                </a-button>
                <SettingsButton
                    :pageName="pageName"
                    class="ml-2" />
            </template>
        </component>
    </keep-alive>
</template>

<script>
import PageFilter from '@/components/PageFilter'
import SettingsButton from '@/components/TableWidgets/SettingsButton'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        PageFilter,
        SettingsButton
    },
    data() {
        return {
            pageName: 'accounting_reports',
            model: 'accounting_reports.AccountingReportBaseModel',

        }
    },  
    computed: {
        component() {
            return () => import('./components/Desktop.vue')
        }
    },
    methods: {
        openCreateDrawer() {
            eventBus.$emit('open_create_accounting_order_drawer')
        }
    }
}
</script>