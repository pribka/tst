<template>
    <ModuleWrapper :pageTitle="pageTitle" :headerBg="!isMobile">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :model="pageModel"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <a-button 
                v-if="user?.is_support"
                class="header__button"
                icon="fi-rr-plus-small" 
                flaticon
                type="primary"
                @click="addOrganization('organization')">
                {{ $t('team.add_organization') }}
            </a-button>
            <HelpButton partCode="organization" type="button" class="ml-2" />
            <component
                :is="settingsButtonWidget"   
                :pageName="page_name"
                size="default"
                class="ml-2" />
        </template>
        <component 
            :is="listComponent"
            :pageModel="pageModel"
            :page_name="page_name" />
        <MobileFloatActions
            v-if="isMobile"
            :pageModel="pageModel"
            :pageName="page_name"
            :showAdd="Boolean(user?.is_support)"
            @create="addOrganization('organization')"
            @open-menu="openCatalogMenu" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        MobileFloatActions: () => import('../components/MobileFloatActions.vue')
    },
    data() {
        return {
            activeTab: 'ours',
            pageModel: 'catalogs.ContractorModel',
            page_name: 'catalogs.ContractorModel_list',
            listComponent: null
        }
    },
    computed: {
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        user() {
            return this.$store.state.user.user
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        addOrganization(organization_type) {
            eventBus.$emit('create_organization', { organization_type })
        },
        openCatalogMenu() {
            eventBus.$emit('directories_open_catalog_drawer')
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./List.vue')
            : () => import('./Table.vue')
    }
}
</script>
