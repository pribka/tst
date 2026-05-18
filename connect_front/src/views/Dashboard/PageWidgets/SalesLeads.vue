<template>
    <ModuleWrapper
        pageTitle="Лиды"
        :bodyOHidden="viewType !== 'table'"
        :bodyPadding="viewType === 'table'">
        <template v-slot:h_left>
            <PageFilter
                model="help_desk.HelpDeskTicketModel"
                :key="pageName"
                size="large"
                :page_name="pageName" />
        </template>
        <template v-slot:h_right>
            <SettingsButton
                v-if="viewType === 'table'"
                :pageName="pageName"
                size="default" />
        </template>
        <UnconfirmedAppeals
            :initPageName="pageName"
            :initPageModel="pageModel"
            :changeMainViewType="changeMainViewType" />
    </ModuleWrapper>
</template>

<script>
export default {
    name: 'SalesLeadsPage',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        UnconfirmedAppeals: () => import('@apps/HelpDesk/views/UnconfirmedAppeals')
    },
    data() {
        return {
            viewType: 'table',
            pageName: 'help_desk.UnconfirmedAppealsPage',
            pageModel: 'help_desk.HelpDeskTicketModel'
        }
    },
    methods: {
        changeMainViewType(viewType) {
            this.viewType = viewType
        }
    }
}
</script>
