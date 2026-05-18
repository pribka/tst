<template>
    <a-spin class="okr" :spinning="loading">
        <ModuleWrapper 
            :pageTitle="pageTitle" 
            :headerBg="!isMobile" 
            :bodyPadding="true">
            <template v-if="!isMobile" v-slot:h_left>
                <PageFilter
                    :model="model"
                    :key="page_name"
                    size="large"
                    :popoverMaxWidth="400"
                    :page_name="page_name" />
            </template>
            <template v-slot:h_right>
                <div v-if="!isMobile" class="buttons">
                    <a-button
                        v-if="isAddAvailable"
                        icon="plus"
                        class="add-button"
                        @click="createObjective()">
                        {{ $t('okr.addObjective') }}
                    </a-button>
                    <OpenReportModalButton
                        v-if="isAddAvailable"
                        sectionCode="okr" />
                    <HelpButton partCode="okr" type="button" />
                </div>
            </template>
            <Segmented 
                v-model="viewMode" 
                class="view-mode-switch"
                :options="listType"
                localStorageKey="strategic_plan_type"
                useLocalStorageSave
                @change="setViewMode(viewMode)" />
            <component :is="viewComponent" />
        </ModuleWrapper>
        <ObjectiveDetail />
    </a-spin>
</template>
<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'OKR',
    components: {
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        ObjectiveDetail: () => import('./components/ObjectiveDetail'),
        OpenReportModalButton: () => import('@apps/Reports/components/OpenReportModalButton.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    created() {
        this.fetchActions()
            .then(() => {
                this.fetchData()
            })
            .catch(error => {
                errorHandler({error})
            })
    },
    mounted(){
        eventBus.$on('user_profile_updated', () => {
            this.fetchData()
        })
        eventBus.$on('reload_okr_dashboard', () => {
            this.fetchData()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.fetchData()
        })
    },
    beforeDestroy(){
        eventBus.$off('user_profile_updated')
        eventBus.$off('reload_okr_dashboard')
        eventBus.$off(`update_filter_${this.model}`)
    },
    computed: {
        ...mapGetters({
            isAddAvailable: 'okr/isObjectiveCreateAvailable',
            loading: 'okr/anyLoading'
            
        }),
        ...mapState({
            model: state => state.okr.model

        }),
        pageTitle() {
            return this.$t('okr.strategicPlan')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        showInfoButton() {
            // Показать кода будет страница помощи на которую будет вести ссылка
            return false
        },
        currentContractorID() {
            return this.$store.state.user.user.current_contractor.id || null
        },
        page_name() {
            return `${this.currentContractorID}_objectives_and_key_results`
        },
        viewComponent() {
            if (this.viewMode === 'List')
                return () => import('./views/List')
            else if (this.viewMode === 'Kanban')
                return () => import('./views/Kanban')
            return () => import('./views/NotWidget.vue')
        }
    },
    data() {
        const DEFAULT_VIEW_MODE = 'Kanban'
        return {
            viewMode: DEFAULT_VIEW_MODE,
            listType: [
                {
                    key: 'Kanban',
                    title: this.$t('okr.kanban')
                },
                {
                    key: 'List',
                    title: this.$t('okr.list')
                }
            ],
        }
    },
    methods: {
        ...mapActions({
            fetchActions: 'okr/fetchActions',
            fetchDepartments: 'okr/fetchDepartments',
            fetchObjectiveStatuses: 'okr/fetchObjectiveStatuses',
            fetchObjectives: 'okr/fetchObjectives',
            fetchStakeholders: 'okr/fetchStakeholders',
            fetchMetrics: 'okr/fetchMetrics'

        }),
        setViewMode(mode) {
            this.viewMode = mode
        },
        createObjective() {
            eventBus.$emit('add_objective')
        },
        fetchData() {
            Promise.all([
                this.fetchMetrics(),
                this.fetchStakeholders(),
                this.fetchActions(),
                this.fetchDepartments(),
                this.fetchObjectives(),
                this.fetchObjectiveStatuses(),
            ])
                .catch((e) => {
                    console.log(e)
                    this.$message.error('Ошибка получения данных')
                })
        },
    }
}
</script>
<style lang="scss" scoped>
.okr {
    height: 100%;
    .view-mode-switch {
        width: fit-content;
        margin-bottom: 12px;
    }
    .buttons {
        flex: 1;
        display: flex;
        justify-content: flex-end;
        gap: 4px;
        .add-button {
            color: #fff;
            background-color: #4777FF;
            border-color: #4777FF;
        }
        .info-button{
            color: #4777FF;
            background-color: #E8EDFA;
            border-color: #E8EDFA;
        }
    }
    &::v-deep {
        .ant-spin-container {
            height: 100%;
        }
    }
}
</style>