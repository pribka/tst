<template>
    <div class="flex-grow custom_tabs">
        <template v-if="isMobile">
            <template v-if="isConsolidator !== null">
                <template v-if="isConsolidator">
                    <a-tabs default-active-key="consolidations" class="custom_tabs">
                        <a-tab-pane key="consolidations" :tab="$t('Consolidations')">
                            <List
                                addButton
                                :createConsolidation="createConsolidation"
                                :model="model"
                                :name="page_name"
                                :page_name="page_name" />
                        </a-tab-pane>
                        <a-tab-pane key="templates" :tab="$t('Templates')">
                            <Cards
                                isScheduled
                                :model="model"
                                :name="templates_page_name"
                                :params="params"
                                :page_name="templates_page_name" />
                        </a-tab-pane>
                    </a-tabs>
                </template>
                <template v-else>
                    <List
                        showPageTitle
                        :model="model"
                        name="consolidations_table"
                        :page_name="page_name" />
                </template>
            </template>
            <template v-else>
                <a-skeleton active class="skeleton" />
            </template>
        </template>
        <template v-else>
            <template v-if="isConsolidator !== null">
                <template v-if="isConsolidator">
                    <a-tabs default-active-key="consolidations" class="custom_tabs">
                        <a-tab-pane key="consolidations" :tab="$t('Consolidations')">
                            <ModuleWrapper :pageTitle="pageTitle">
                                <template v-slot:h_left>
                                    <PageFilter
                                        :model="model"
                                        :key="page_name"
                                        class="mr-2"
                                        size="large"
                                        :page_name="page_name" />
                                </template>
                                <template v-slot:h_right>
                                    <a-button
                                        v-if="isConsolidator"
                                        type="primary" 
                                        icon="plus"
                                        class="mr-2"
                                        size="large"
                                        @click="createConsolidation()">
                                        {{$t('New Consolidation')}}
                                    </a-button>
                                    <SettingsButton
                                        :pageName="page_name"
                                        class="ml-2" />
                                </template>
                                <Table 
                                    :model="model"
                                    tableType="consolidation"
                                    :page_name="page_name" />
                            </ModuleWrapper>
                        </a-tab-pane>
                        <a-tab-pane key="templates" :tab="$t('Templates')">
                            <ModuleWrapper :pageTitle="$t('Consolidation Templates')">
                                <template v-slot:h_left>
                                    <PageFilter
                                        :model="model"
                                        :key="templates_page_name"
                                        class="mr-2"
                                        size="large"
                                        :page_name="templates_page_name" />
                                </template>
                                <Cards
                                    :model="model"
                                    name="templates_consolidations_table"
                                    :params="params"
                                    :page_name="templates_page_name"
                                    :isScheduled="true" />
                            </ModuleWrapper>
                        </a-tab-pane>
                    </a-tabs>
                </template>
                <template v-else>
                    <ModuleWrapper :pageTitle="pageTitle">
                        <template v-slot:h_left>
                            <PageFilter
                                :model="model"
                                :key="page_name"
                                class="mr-2"
                                size="large"
                                :page_name="page_name" />
                        </template>
                        <template v-slot:h_right>
                            <a-button
                                v-if="isConsolidator"
                                type="primary" 
                                icon="plus"
                                class="mr-2"
                                size="large"
                                @click="createConsolidation()">
                                {{$t('New Consolidation')}}
                            </a-button>
                            <SettingsButton
                                :pageName="page_name"
                                class="ml-2" />
                        </template>
                        <Table 
                            :model="model"
                            tableType="consolidation"
                            :page_name="page_name" />
                    </ModuleWrapper>
                </template>
            </template>
            <template v-else>
                <a-skeleton active class="skeleton" />
            </template>
        </template>
        <CreateConsolidation
            :pageName="page_name" />
    </div>

</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'ConsolidationIndex',
    components: {
        Cards: () => import('./components/Cards.vue'),
        CreateConsolidation: () => import('./components/CreateConsolidation'),
        List: () => import('./components/List.vue'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        Table: () => import('./components/Table')
    },
    data() {
        return {
            page_name: 'consolidations_table',
            templates_page_name: 'templates_consolidations_table',
            model: 'consolidation.ConsolidationModel',
            isConsolidator: null,
            params: {
                is_scheduled: true
            }
        }
    },
    mounted() {
        this.getIsConsolidator()
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
    },
    methods: {
        createConsolidation() {
            eventBus.$emit('create_consolidation')
        },
        async getIsConsolidator() {
            try {
                const { data } = await this.$http.get(`/consolidation/get_org_administrators`)
                this.isConsolidator = data.length ? true : false
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>

<style scoped lang="scss">
.skeleton {
    padding: 30px;
}
.custom_tabs::v-deep {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    .ant-tabs-content, 
    .ant-tabs-tabpane-active {
        display: flex;
        flex-grow: 1;
    }
    .ant-tabs-nav-container {
        padding: 0 20px;
    }
}
</style>