<template>
    <ModuleWrapper
        pageTitle="Клиенты"
        :bodyOHidden="false">
        <template v-slot:h_left>
            <PageFilter
                model="help_desk.CustomerCardModel"
                :key="pageName"
                size="large"
                :page_name="pageName"
                :popoverMaxWidth="600" />
        </template>
        <template v-slot:h_right>
            <a-button
                type="primary"
                flaticon
                icon="fi-rr-plus-small"
                class="mr-2"
                @click="addClient">
                Клиент
            </a-button>
            <SettingsButton
                :pageName="pageName"
                size="default" />
        </template>
        <Clients
            :initPageName="pageName"
            :initPageModel="pageModel" />
        <ClientForm />
        <component
            :is="clientDrawerAsync"
            v-if="$route.query.client" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'SalesClientsPage',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        Clients: () => import('@apps/HelpDesk/views/Clients'),
        ClientForm: () => import('@apps/HelpDesk/components/ClientForm.vue')
    },
    data() {
        return {
            pageName: 'list_help_desk.CustomerCardModel',
            pageModel: 'help_desk.CustomerCardModel',
            clientDrawerAsync: null
        }
    },
    watch: {
        '$route.query.client': {
            immediate: true,
            handler(value) {
                if (value && !this.clientDrawerAsync) {
                    this.clientDrawerAsync = () => import('@apps/HelpDesk/components/ClientDrawer')
                }
            }
        }
    },
    methods: {
        addClient() {
            eventBus.$emit('helpdesc_add_client')
        }
    }
}
</script>
