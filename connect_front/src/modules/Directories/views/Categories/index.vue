<template>
    <ModuleWrapper
        :pageTitle="pageTitle"
        :headerBg="!isMobile"
        :bodyPadding="true"
        :bodyOHidden="true">
        <template v-if="!isMobile" #h_left>
            <PageFilter
                :model="initPageModel"
                :key="initPageName"
                size="large"
                :page_name="initPageName" />
        </template>
        <template v-if="!isMobile" #h_right>
            <a-button
                v-if="showCreateButton"
                class="header__button"
                icon="fi-rr-plus-small"
                flaticon
                type="primary"
                @click="addHandler">
                {{ $t('directories.create') }}
            </a-button>
            <component
                :is="settingsButtonWidget"
                :pageName="initPageName"
                :key="$route.name"
                size="default"
                class="ml-2" />
        </template>
        <div v-if="!isMobile" ref="wrapRef" class="h-full flex flex-col">
            <UniversalTable 
                :model="initPageModel"
                class="flex-grow"
                :pageName="initPageName"
                tableType="helpdesk_categories_page"
                :endpoint="endpoint" />
        </div>
        <CategoriesListMobile
            v-else
            :pageModel="initPageModel"
            :pageName="initPageName" />
        <ModalCategoryCreate :model="initPageModel" contractorSelect />
        <MobileFloatActions
            v-if="isMobile"
            :pageModel="initPageModel"
            :pageName="initPageName"
            :showAdd="showCreateButton"
            @create="addHandler"
            @open-menu="openCatalogMenu" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        ModalCategoryCreate: () => import('../../components/ModalCategoryCreate.vue'),
        CategoriesListMobile: () => import('./ListMobile.vue'),
        MobileFloatActions: () => import('../../components/MobileFloatActions.vue')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        }
    },
    data() {
        return {
            endpoint: "/help_desk/ticket_categories/"
        }
    },
    computed: {
        currentRoute() {
            return this.$route.name
        },
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.currentRoute)
        }, 
        showCreateButton() {
            return this.getRouteInfo?.pageActions?.add
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || this.$t('directories.categories_label')
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        }
    },
    methods: {
        addHandler() {
            eventBus.$emit('open_modal_category_add')
        },
        openCatalogMenu() {
            eventBus.$emit('directories_open_catalog_drawer')
        }
    }
}
</script>
