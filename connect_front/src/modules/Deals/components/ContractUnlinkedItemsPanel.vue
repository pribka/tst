<template>
    <transition name="contract-unlinked-panel">
        <div v-if="shouldShowPanel" class="contract_unlinked_panel">
            <div class="contract_unlinked_panel__main">
                <div class="contract_unlinked_panel__head">
                    <div class="contract_unlinked_panel__title">
                        {{ unlinkedDetectedTitle }}
                    </div>
                    <a-button
                        type="link"
                        size="small"
                        icon="fi-rr-refresh"
                        flaticon
                        :loading="availabilityLoading"
                        @click="loadAvailability" />
                </div>

                <div class="contract_unlinked_panel__stats">
                    <div
                        v-if="requestsAvailable && requestsCount"
                        class="contract_unlinked_panel__stat">
                        <span class="contract_unlinked_panel__label">{{ $t('deals_contracts.requests_tab') }}</span>
                        <a-badge
                            :count="requestsCount"
                            :number-style="{ backgroundColor: '#fa8c16', color: '#fff' }" />
                    </div>
                    <div
                        v-if="tasksAvailable && tasksCount"
                        class="contract_unlinked_panel__stat">
                        <span class="contract_unlinked_panel__label">{{ $t('deals_contracts.tasks_tab') }}</span>
                        <a-badge
                            :count="tasksCount"
                            :number-style="{ backgroundColor: '#fa8c16', color: '#fff' }" />
                    </div>
                </div>
            </div>

            <a-button
                class="contract_unlinked_panel__open"
                type="primary"
                :disabled="!canOpenModal"
                @click="openModal">
                {{ $t('deals_contracts.unlinked_process') }}
            </a-button>

            <a-modal
                class="contract_unlinked_modal_dialog"
                :visible="modalVisible"
                :title="$t('deals_contracts.unlinked_process')"
                :width="760"
                :dialog-style="{ top: '10px' }"
                :body-style="modalBodyStyle"
                :destroyOnClose="true"
                @cancel="closeModal">
                <div class="contract_unlinked_modal">
                <a-tabs :activeKey="activeTab" @change="onTabChange">
                    <a-tab-pane key="requests" :tab="$t('deals_contracts.requests_tab')">
                        <div class="contract_unlinked_modal__pane">
                        <div class="contract_unlinked_modal__toolbar">
                            <div class="contract_unlinked_modal__filter_wrap">
                            <PageFilter
                                ref="requestsPageFilter"
                                :model="requestsFilterModel"
                                :key="requestsFilterPageName"
                                size="large"
                                :zIndex="999999"
                                autoAdjustOverflow
                                class="contract_unlinked_modal__filter"
                                transitionName=""
                                placement="bottom"
                                :getPopupContainer="getPopupContainer"
                                :page_name="requestsFilterPageName" />
                            </div>
                            <a-checkbox
                                :disabled="!requestsItems.length"
                                :indeterminate="isRequestsPartlySelected"
                                :checked="isRequestsAllSelected"
                                @change="toggleSelectAllRequests">
                                {{ $t('deals_contracts.requests_select_all') }}
                            </a-checkbox>
                        </div>

                        <a-alert
                            v-if="!analyticsKeyId"
                            class="mb-2"
                            type="warning"
                            show-icon
                            :message="$t('deals_contracts.requests_missing_analytics_key')" />

                        <div
                            v-if="!requestsInitialized || requestsItems.length"
                            class="contract_unlinked_modal__list"
                            infinite-wrapper>
                            <ContractUnlinkedRequestCard
                                v-for="ticket in requestsItems"
                                :key="`request_${ticket.id}`"
                                :ticket="ticket"
                                :selected="isRequestSelected(ticket.id)"
                                @toggle="toggleRequestSelected"
                                @open="$emit('open-related', { type: 'ticket', id: $event })"
                                @open-task="$emit('open-related', { type: 'task', id: $event })" />

                            <infinite-loading
                                ref="requestsInfinite"
                                :identifier="requestsInfiniteId"
                                :distance="10"
                                :forceUseInfiniteWrapper="true"
                                @infinite="loadRequestsInfinite">
                                <div slot="spinner" class="contract_unlinked_modal__loading">
                                    <a-spin size="small" />
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                        </div>

                        <a-empty
                            v-else
                            :description="$t('deals_contracts.requests_without_key_empty')" />
                        </div>
                    </a-tab-pane>

                    <a-tab-pane key="tasks" :tab="$t('deals_contracts.tasks_tab')">
                        <div class="contract_unlinked_modal__pane">
                        <div class="contract_unlinked_modal__toolbar">
                            <div class="contract_unlinked_modal__filter_wrap">
                            <PageFilter
                                ref="tasksPageFilter"
                                :model="tasksFilterModel"
                                :key="tasksFilterPageName"
                                size="large"
                                :zIndex="999999"
                                autoAdjustOverflow
                                class="contract_unlinked_modal__filter"
                                transitionName=""
                                placement="bottom"
                                :getPopupContainer="getPopupContainer"
                                :page_name="tasksFilterPageName" />
                            </div>
                            <a-checkbox
                                :disabled="!tasksItems.length"
                                :indeterminate="isTasksPartlySelected"
                                :checked="isTasksAllSelected"
                                @change="toggleSelectAllTasks">
                                {{ $t('deals_contracts.tasks_select_all') }}
                            </a-checkbox>
                        </div>

                        <div
                            v-if="!tasksInitialized || tasksItems.length"
                            class="contract_unlinked_modal__list"
                            infinite-wrapper>
                            <ContractUnlinkedTaskCard
                                v-for="task in tasksItems"
                                :key="`task_${task.id}`"
                                :task="task"
                                :selected="isTaskSelected(task.id)"
                                @toggle="toggleTaskSelected"
                                @open="$emit('open-related', { type: 'task', id: $event })" />

                            <infinite-loading
                                ref="tasksInfinite"
                                :identifier="tasksInfiniteId"
                                :distance="10"
                                :forceUseInfiniteWrapper="true"
                                @infinite="loadTasksInfinite">
                                <div slot="spinner" class="contract_unlinked_modal__loading">
                                    <a-spin size="small" />
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                        </div>

                        <a-empty
                            v-else
                            :description="$t('deals_contracts.tasks_project_empty')" />
                        </div>
                    </a-tab-pane>
                </a-tabs>
                </div>
                <template #footer>
                    <div class="contract_unlinked_modal__actions">
                        <a-button
                            type="primary"
                            :loading="assigning"
                            :disabled="!canAssign"
                            @click="assignSelected">
                            {{ $t('deals_contracts.requests_assign_selected') }} ({{ selectedCount }})
                        </a-button>
                    </div>
                </template>
            </a-modal>
        </div>
    </transition>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ContractUnlinkedItemsPanel',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        PageFilter: () => import('@/components/PageFilter'),
        ContractUnlinkedRequestCard: () => import('./ContractUnlinkedRequestCard.vue'),
        ContractUnlinkedTaskCard: () => import('./ContractUnlinkedTaskCard.vue'),
    },
    props: {
        contractId: {
            type: String,
            default: null,
        },
        projectId: {
            type: [String, Number],
            default: null,
        },
        customerCardId: {
            type: String,
            default: null,
        },
        initialActiveTab: {
            type: String,
            default: 'requests',
            validator: value => ['requests', 'tasks'].includes(value),
        },
    },
    data() {
        return {
            modalVisible: false,
            activeTab: 'requests',
            assigning: false,
            availabilityLoading: false,
            requestsAvailable: false,
            tasksAvailable: false,
            requestsCount: 0,
            tasksCount: 0,
            analyticsKeyId: null,
            requestsItems: [],
            requestsSelected: [],
            requestsPage: 1,
            requestsHasNext: true,
            requestsLoading: false,
            requestsInitialized: false,
            requestsInfiniteId: 1,
            tasksItems: [],
            tasksSelected: [],
            tasksPage: 1,
            tasksHasNext: true,
            tasksLoading: false,
            tasksInitialized: false,
            tasksInfiniteId: 1,
        }
    },
    computed: {
        isMobile() {
            return Boolean(this.$store?.state?.isMobile)
        },
        modalBodyStyle() {
            return {
                height: this.isMobile ? 'calc(100vh - 120px)' : 'calc(100vh - 140px)',
                overflow: 'hidden',
            }
        },
        requestsFilterModel() {
            return 'help_desk.HelpDeskTicketModel'
        },
        requestsFilterPageName() {
            return 'deals_contract_unlinked.HelpDeskForClientTicketModel_page'
        },
        tasksFilterModel() {
            return 'tasks.TaskModel'
        },
        tasksFilterPageName() {
            return 'deals_contract_unlinked.TaskModel_page'
        },
        canOpenModal() {
            return Boolean(this.contractId && this.projectId && this.customerCardId)
        },
        shouldShowPanel() {
            return this.requestsCount > 0 || this.tasksCount > 0
        },
        unlinkedDetectedTitle() {
            if (this.requestsAvailable && this.tasksAvailable) {
                return this.$t('deals_contracts.unlinked_detected')
            }
            if (this.tasksAvailable) {
                return this.$t('deals_contracts.unlinked_tasks_detected')
            }
            return this.$t('deals_contracts.unlinked_requests_detected')
        },
        selectedCount() {
            if (this.activeTab === 'tasks') {
                return this.tasksSelected.length
            }
            return this.requestsSelected.length
        },
        canAssign() {
            if (this.assigning || !this.selectedCount) {
                return false
            }
            if (this.activeTab === 'requests') {
                return Boolean(this.analyticsKeyId)
            }
            return Boolean(this.contractId && this.projectId)
        },
        isRequestsAllSelected() {
            return this.requestsItems.length > 0 && this.requestsSelected.length === this.requestsItems.length
        },
        isRequestsPartlySelected() {
            return this.requestsSelected.length > 0 && this.requestsSelected.length < this.requestsItems.length
        },
        isTasksAllSelected() {
            return this.tasksItems.length > 0 && this.tasksSelected.length === this.tasksItems.length
        },
        isTasksPartlySelected() {
            return this.tasksSelected.length > 0 && this.tasksSelected.length < this.tasksItems.length
        },
    },
    watch: {
        contractId() {
            this.onContextChanged()
        },
        projectId() {
            this.onContextChanged()
        },
        customerCardId() {
            this.onContextChanged()
        },
    },
    mounted() {
        this.loadAvailability()
        eventBus.$on(`update_filter_${this.requestsFilterModel}_${this.requestsFilterPageName}`, this.onRequestsFilterUpdated)
        eventBus.$on(`update_filter_${this.tasksFilterModel}_${this.tasksFilterPageName}`, this.onTasksFilterUpdated)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.requestsFilterModel}_${this.requestsFilterPageName}`, this.onRequestsFilterUpdated)
        eventBus.$off(`update_filter_${this.tasksFilterModel}_${this.tasksFilterPageName}`, this.onTasksFilterUpdated)
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.contract_unlinked_modal_dialog') || document.body
        },
        onContextChanged() {
            this.closeModal()
            this.resetRequestsList()
            this.resetTasksList()
            this.loadAvailability()
        },
        async loadAvailability() {
            if (!this.canOpenModal) {
                this.requestsAvailable = false
                this.tasksAvailable = false
                this.requestsCount = 0
                this.tasksCount = 0
                return
            }
            this.availabilityLoading = true
            try {
                const [requestsResult, tasksResult] = await Promise.all([
                    this.findRequestsAvailability(),
                    this.findTasksAvailability(),
                ])
                this.requestsCount = requestsResult.count
                this.tasksCount = tasksResult.count
                this.requestsAvailable = requestsResult.count > 0
                this.tasksAvailable = tasksResult.count > 0
            } catch (error) {
                this.requestsAvailable = false
                this.tasksAvailable = false
                this.requestsCount = 0
                this.tasksCount = 0
                errorHandler({ error, show: false })
            } finally {
                this.availabilityLoading = false
            }
        },
        async findRequestsAvailability() {
            const { data } = await this.$http.get('/help_desk/tickets/short_list/', {
                params: this.getRequestsParams(1, { countOnly: true }),
            })
            return {
                count: this.getCount(data, this.parseResults(data).length),
            }
        },
        async findTasksAvailability() {
            const { data } = await this.$http.get('/tasks/task/list/', {
                params: this.getTasksParams(1, { countOnly: true }),
            })
            return {
                count: this.getCount(data, this.parseResults(data).length),
            }
        },
        openModal() {
            if (!this.canOpenModal) return
            this.activeTab = this.initialActiveTab
            this.modalVisible = true
            this.loadAnalyticsKey()
            this.resetRequestsList()
            this.resetTasksList()
            this.$nextTick(() => {
                this.resetInfiniteByTab(this.activeTab, false)
            })
        },
        closeModal() {
            this.modalVisible = false
            this.activeTab = 'requests'
            this.requestsSelected = []
            this.tasksSelected = []
        },
        onTabChange(tabKey) {
            this.activeTab = tabKey
            this.$nextTick(() => {
                this.resetInfiniteByTab(tabKey, true)
            })
        },
        resetInfiniteByTab(tabKey, onlyIfNotInitialized = false) {
            if (tabKey === 'tasks') {
                if (onlyIfNotInitialized && this.tasksInitialized) return
                this.$refs.tasksInfinite?.stateChanger?.reset()
                return
            }

            if (onlyIfNotInitialized && this.requestsInitialized) return
            this.$refs.requestsInfinite?.stateChanger?.reset()
        },
        parseResults(data) {
            return Array.isArray(data) ? data : (data?.results || [])
        },
        getCount(data, fallbackLength = 0) {
            if (Array.isArray(data)) return fallbackLength
            return Number.isFinite(data?.count) ? Number(data.count) : fallbackLength
        },
        sortByDate(source, dateResolver) {
            return [...source].sort((a, b) => {
                const bDate = new Date(dateResolver(b) || 0).getTime()
                const aDate = new Date(dateResolver(a) || 0).getTime()
                return bDate - aDate
            })
        },
        mergeById(currentList, incomingList) {
            const map = new Map()
            currentList.forEach(item => {
                if (!item?.id) return
                map.set(String(item.id), item)
            })
            incomingList.forEach(item => {
                if (!item?.id) return
                map.set(String(item.id), item)
            })
            return Array.from(map.values())
        },
        resetRequestsList() {
            this.requestsItems = []
            this.requestsSelected = []
            this.requestsPage = 1
            this.requestsHasNext = true
            this.requestsLoading = false
            this.requestsInitialized = false
            this.requestsInfiniteId += 1
        },
        resetTasksList() {
            this.tasksItems = []
            this.tasksSelected = []
            this.tasksPage = 1
            this.tasksHasNext = true
            this.tasksLoading = false
            this.tasksInitialized = false
            this.tasksInfiniteId += 1
        },
        onRequestsFilterUpdated() {
            this.resetRequestsList()
            this.$nextTick(() => this.$refs.requestsInfinite?.stateChanger?.reset())
        },
        onTasksFilterUpdated() {
            this.resetTasksList()
            this.$nextTick(() => this.$refs.tasksInfinite?.stateChanger?.reset())
        },
        getRequestsParams(page, options = {}) {
            const { countOnly = false } = options
            const params = {
                customer_card: this.customerCardId,
                page,
                page_size: countOnly ? 1 : 30,
                filters: JSON.stringify({
                    customer_card: this.customerCardId,
                    analytics_key: null,
                }),
            }
            if (!countOnly) {
                params.page_name = this.requestsFilterPageName
                params.model = this.requestsFilterModel
            }
            return params
        },
        getTasksParams(page, options = {}) {
            const { countOnly = false } = options
            const params = {
                page,
                page_size: countOnly ? 1 : 30,
                task_type: 'task,stage,milestone',
                filters: JSON.stringify({
                    project: this.projectId,
                    parent: null,
                    contract: null,
                }),
            }
            if (!countOnly) {
                params.page_name = this.tasksFilterPageName
            }
            return params
        },
        async loadAnalyticsKey() {
            this.analyticsKeyId = null
            if (!this.customerCardId || !this.contractId || !this.projectId) {
                return
            }
            try {
                const { data } = await this.$http.get('/customer_contracts/analytics_keys/', {
                    params: {
                        customer_card: this.customerCardId,
                        contract: this.contractId,
                        project: this.projectId,
                    },
                })
                const source = Array.isArray(data?.filteredSelectList) ? data.filteredSelectList : []
                this.analyticsKeyId = source[0]?.id || null
            } catch (error) {
                this.analyticsKeyId = null
                errorHandler({ error, show: false })
            }
        },
        async loadRequestsInfinite($state) {
            if (!this.customerCardId) {
                this.requestsInitialized = true
                this.requestsHasNext = false
                $state.complete()
                return
            }
            if (this.requestsLoading) return
            if (!this.requestsHasNext) {
                this.requestsInitialized = true
                $state.complete()
                return
            }
            this.requestsLoading = true
            try {
                const { data } = await this.$http.get('/help_desk/tickets/short_list/', {
                    params: this.getRequestsParams(this.requestsPage),
                })
                const source = this.parseResults(data)
                this.requestsItems = this.sortByDate(
                    this.mergeById(this.requestsItems, source),
                    item => item?.updated_at || item?.receipt_date || item?.created_at,
                )
                this.requestsPage += 1
                this.requestsHasNext = Boolean(data?.next)
                this.requestsInitialized = true
                this.syncRequestsSelection()
                if (this.requestsHasNext) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.requestsItems = []
                this.requestsSelected = []
                this.requestsHasNext = false
                this.requestsInitialized = true
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.requestsLoading = false
            }
        },
        async loadTasksInfinite($state) {
            if (!this.projectId) {
                this.tasksInitialized = true
                this.tasksHasNext = false
                $state.complete()
                return
            }
            if (this.tasksLoading) return
            if (!this.tasksHasNext) {
                this.tasksInitialized = true
                $state.complete()
                return
            }
            this.tasksLoading = true
            try {
                const { data } = await this.$http.get('/tasks/task/list/', {
                    params: this.getTasksParams(this.tasksPage),
                })
                const source = this.parseResults(data)
                this.tasksItems = this.sortByDate(
                    this.mergeById(this.tasksItems, source),
                    item => item?.dead_line || item?.updated_at || item?.created_at,
                )
                this.tasksPage += 1
                this.tasksHasNext = Boolean(data?.next)
                this.tasksInitialized = true
                this.syncTasksSelection()
                if (this.tasksHasNext) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.tasksItems = []
                this.tasksSelected = []
                this.tasksHasNext = false
                this.tasksInitialized = true
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.tasksLoading = false
            }
        },
        isRequestSelected(id) {
            return this.requestsSelected.includes(String(id))
        },
        toggleRequestSelected(id) {
            const normalized = String(id)
            if (this.isRequestSelected(normalized)) {
                this.requestsSelected = this.requestsSelected.filter(item => item !== normalized)
                return
            }
            this.requestsSelected = [...this.requestsSelected, normalized]
        },
        isTaskSelected(id) {
            return this.tasksSelected.includes(String(id))
        },
        toggleTaskSelected(id) {
            const normalized = String(id)
            if (this.isTaskSelected(normalized)) {
                this.tasksSelected = this.tasksSelected.filter(item => item !== normalized)
                return
            }
            this.tasksSelected = [...this.tasksSelected, normalized]
        },
        toggleSelectAllRequests(event) {
            const checked = Boolean(event?.target?.checked)
            if (!checked) {
                this.requestsSelected = []
                return
            }
            this.requestsSelected = this.requestsItems.map(item => String(item.id))
        },
        toggleSelectAllTasks(event) {
            const checked = Boolean(event?.target?.checked)
            if (!checked) {
                this.tasksSelected = []
                return
            }
            this.tasksSelected = this.tasksItems.map(item => String(item.id))
        },
        syncRequestsSelection() {
            const available = new Set(this.requestsItems.map(item => String(item.id)))
            this.requestsSelected = this.requestsSelected.filter(id => available.has(String(id)))
        },
        syncTasksSelection() {
            const available = new Set(this.tasksItems.map(item => String(item.id)))
            this.tasksSelected = this.tasksSelected.filter(id => available.has(String(id)))
        },
        async assignSelected() {
            if (!this.canAssign) return
            this.assigning = true
            try {
                if (this.activeTab === 'tasks') {
                    await this.$http.post('/tasks/task/assign_contract/', {
                        task_ids: this.tasksSelected,
                        contract: this.contractId,
                        project: this.projectId,
                    })
                    this.tasksSelected = []
                    this.$message.success(this.$t('deals_contracts.tasks_assigned_success'))
                    this.resetTasksList()
                    this.$nextTick(() => this.$refs.tasksInfinite?.stateChanger?.reset())
                } else {
                    await this.$http.post('/help_desk/tickets/assign_analytics_key/', {
                        ticket_ids: this.requestsSelected,
                        analytics_key: this.analyticsKeyId,
                    })
                    this.requestsSelected = []
                    this.$message.success(this.$t('deals_contracts.requests_assigned_success'))
                    this.resetRequestsList()
                    this.$nextTick(() => this.$refs.requestsInfinite?.stateChanger?.reset())
                }
                await this.loadAvailability()
                this.$emit('assigned')
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.assigning = false
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.contract-unlinked-panel-enter-active,
.contract-unlinked-panel-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.contract-unlinked-panel-enter,
.contract-unlinked-panel-leave-to {
    opacity: 0;
    transform: translateY(-12px);
}

.contract_unlinked_panel {
    margin-bottom: 12px;
    border: 1px solid #ffe7ba;
    background: #fffbe6;
    border-radius: 12px;
    padding: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.contract_unlinked_panel__main {
    min-width: 0;
    display: grid;
    gap: 8px;
}

.contract_unlinked_panel__head {
    display: flex;
    align-items: center;
    gap: 8px;
}

.contract_unlinked_panel__title {
    font-size: 13px;
    font-weight: 600;
    color: #594214;
}

.contract_unlinked_panel__stats {
    display: flex;
    align-items: center;
    gap: 14px;
}

.contract_unlinked_panel__stat {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.contract_unlinked_panel__label {
    color: #8c6d1f;
    font-size: 12px;
    font-weight: 500;
}

.contract_unlinked_panel__open {
    flex-shrink: 0;
    min-width: 122px;
    height: 34px;
}

.contract_unlinked_modal {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;

    &::v-deep .ant-tabs {
        height: 100%;
        min-height: 0;
        display: flex;
        flex-direction: column;
    }

    &::v-deep .ant-tabs-content {
        flex: 1;
        min-height: 0;
    }

    &::v-deep .ant-tabs-tabpane {
        height: 100%;
        min-height: 0;
    }
}

.contract_unlinked_modal_dialog {
    &::v-deep {
        .ant-modal {
            max-width: calc(100vw - 16px);
            padding-bottom: 0;
        }

        .ant-modal-content {
            max-height: calc(100vh - 16px);
            display: flex;
            flex-direction: column;
        }

        .ant-modal-body {
            flex: 1;
            min-height: 0;
            overflow: hidden;
        }

        .ant-modal-footer {
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
    }
}

.contract_unlinked_modal__toolbar {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 10px;
}

.contract_unlinked_modal__filter {
    width: 100%;

    &::v-deep {
        .filter_input {
            border-radius: 8px;
            background: #f7f9fc;
            border-color: #f7f9fc !important;
            box-shadow: initial !important;
            color: var(--text);

            .ant-input {
                background: #f7f9fc;
            }
        }
    }
}

.contract_unlinked_modal__filter_wrap {
    width: 100%;

    &::v-deep {
        .filter_pop_wrapper {
            max-width: 100%;
            min-width: 100%;
        }
    }
}

.contract_unlinked_modal__list {
    flex: 1;
    min-height: 0;
    display: grid;
    gap: 8px;
    padding-right: 2px;
    max-height: clamp(260px, calc(100vh - 330px), 620px);
    overflow-y: auto;
    overscroll-behavior: contain;
}

.contract_unlinked_modal__pane {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.contract_unlinked_modal__loading {
    display: flex;
    justify-content: center;
    padding: 10px;
}

.contract_unlinked_modal__actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    width: 100%;
}

.contract_unlinked_modal__selected {
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
}

@media (max-width: 991px) {
    .contract_unlinked_panel {
        flex-direction: column;
        align-items: stretch;
    }

    .contract_unlinked_panel__open {
        width: 100%;
    }

    .contract_unlinked_modal__toolbar {
        flex-direction: column;
        align-items: stretch;
    }

    .contract_unlinked_modal_dialog {
        &::v-deep {
            .ant-modal-footer {
                display: block;
            }
        }
    }

    .contract_unlinked_modal__actions {
        display: block;

        .ant-btn {
            width: 100%;
        }
    }

    .contract_unlinked_modal__list {
        max-height: clamp(220px, calc(100vh - 360px), 520px);
    }
}
</style>
