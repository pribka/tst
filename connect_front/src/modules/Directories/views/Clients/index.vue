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
                {{ $t('directories.create_contractor') }}
            </a-button>
            <component
                :is="settingsButtonWidget"
                :pageName="initPageName"
                :key="$route.name"
                size="default"
                class="ml-2" />
        </template>

        <component
            :is="viewComponent"
            :pageName="initPageName"
            :pageModel="initPageModel"
            :initPageName="initPageName"
            :initPageModel="initPageModel" />
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
        },
        changeMainViewType: {
            type: Function,
            default: () => {}
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
            return this.$route?.meta?.title || this.$t('directories.clients_label')
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        viewComponent() {
            return this.isMobile
                ? () => import('./ListMobile.vue')
                : () => import('./Table.vue')
        }
    },
    methods: {
        addHandler() {
            eventBus.$emit('helpdesc_add_client')
        },
        openCatalogMenu() {
            eventBus.$emit('directories_open_catalog_drawer')
        }
    }
}
</script>
