<template>
    <ModuleWrapper :pageTitle="pageTitle" :headerBg="!isMobile">
        <template v-if="!isMobile" #h_left>
            <PageFilter
                model="customer_contracts.CustomerContractModel"
                :key="pageName"
                size="large"
                :page_name="pageName"
                :getPopupContainer="getHeaderPopupContainer" />
        </template>

        <template v-if="!isMobile" #h_right>
            <div class="contracts_page__header_right">
                <a-button
                    v-if="canAddContract"
                    type="primary"
                    icon="fi-rr-plus"
                    flaticon
                    @click="openAddContract">
                    {{ $t('deals_contracts.add') }}
                </a-button>
                <component
                    :is="settingsButtonWidget"
                    :pageName="pageName"
                    size="default" />
            </div>
        </template>

        <div class="contracts_page">
            <component
                v-if="isMobile"
                :is="viewComponent"
                ref="contractsView"
                :pageName="pageName"
                :pageModel="pageModel" />

            <MobileFloatActions
                v-if="isMobile"
                :pageModel="pageModel"
                :pageName="pageName"
                :showAdd="canAddContract"
                :showMenu="false"
                @create="openAddContract"
                @open-menu="noop" />

            <div v-if="!isMobile" ref="tableWrapRef" class="contracts_page__table">
                <UniversalTable
                    ref="contractsTable"
                    class="contracts_page__table_widget"
                    tableType="contracts"
                    :model="pageModel"
                    :pageName="pageName"
                    endpoint="/customer_contracts/"
                    :colParams="{ getPopupContainer }"
                    :onRowClicked="handleRowClick" />
            </div>
        </div>
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'

export default {
    name: 'DealsModule',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        MobileFloatActions: () => import('../Directories/components/MobileFloatActions.vue'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
    },
    computed: {
        ...mapState({
            routeActions: state => state.navigation.routeActions,
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || this.$t('deals_contracts.page_title')
        },
        pageModel() {
            return 'customer_contracts.CustomerContractModel'
        },
        pageName() {
            return 'page_list_contracts_v3_customer_contracts.CustomerContractModel'
        },
        canAddContract() {
            return Boolean(this.routeActions?.deals?.pageActions?.add)
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        viewComponent() {
            return this.isMobile
                ? () => import('./components/ListMobile.vue')
                : null
        },
    },
    methods: {
        async fetchRouteActions() {
            try {
                await this.$store.dispatch('navigation/getRouteActions', {
                    name: 'deals',
                })
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        getHeaderPopupContainer() {
            return this.$refs.headerRef || document.body
        },
        getPopupContainer() {
            return this.$refs.tableWrapRef || document.body
        },
        noop() {},
        openAddContract() {
            eventBus.$emit('DEALS_ADD_CONTRACT')
        },
        handleRowClick(event) {
            const contractId = event?.data?.id
            if (!contractId) return
            this.openContract(contractId)
        },
        async openContract(id) {
            if (String(this.$route.query.contract || '') === String(id)) return
            await this.$router.push({ query: { ...this.$route.query, contract: id } })
        },
    },
    created() {
        this.fetchRouteActions()
    },
}
</script>

<style lang="scss" scoped>
.contracts_page {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    position: relative;
}

.contracts_page__header_right {
    display: flex;
    align-items: center;
    gap: 8px;
}

.contracts_page__table {
    flex: 1;
    min-height: 0;
    display: flex;
}

.contracts_page__table_widget {
    flex: 1;
}
</style>
