<template>
    <div class="contract_projects_workspace">
        <div class="contract_projects_toolbar">
            <div
                class="contract_projects_toolbar__scroll_wrap"
                @mouseenter="updateProjectsArrows"
                @mouseleave="stopProjectsHoverScroll">
                <a-button
                    v-if="showLeftArrow"
                    class="contract_projects_scroll_arrow contract_projects_scroll_arrow--left"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-left"
                    @mouseenter="startProjectsHoverScroll('left')"
                    @mouseleave="stopProjectsHoverScroll"
                    @click="scrollProjects('left')" />
                <a-button
                    v-if="showRightArrow"
                    class="contract_projects_scroll_arrow contract_projects_scroll_arrow--right"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-right"
                    @mouseenter="startProjectsHoverScroll('right')"
                    @mouseleave="stopProjectsHoverScroll"
                    @click="scrollProjects('right')" />
                <div ref="projectsScroll" class="contract_projects_toolbar__scroll" @scroll="updateProjectsArrows">
                    <div class="contract_projects_toolbar__list">
                        <div
                            v-for="project in normalizedProjects"
                            :key="project.id"
                            class="contract_project_item">
                            <button
                                type="button"
                                class="contract_project_tab"
                                :title="project.name"
                                :class="{ 'is-active': project.id === activeProjectId }"
                                @click="activeProjectId = project.id">
                                <span class="contract_project_tab__name">{{ project.name }}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <a-button
                class="contract_projects_toolbar__edit"
                type="flat_primary"
                icon="fi-rr-edit"
                flaticon
                :disabled="savingProjects"
                @click="openManageProjectsModal">
                {{ $t('deals_contracts.edit_projects') }}
            </a-button>
        </div>

        <template v-if="hasProjects && contractId && activeProjectId">
                <ContractUnlinkedItemsPanel
                    :contractId="contractId"
                    :projectId="activeProjectId"
                    :customerCardId="customerCardId"
                    :initialActiveTab="activeScopeTab"
                    @open-related="openRelatedFromPanel"
                    @assigned="handleUnlinkedAssigned" />
                <a-tabs
                    :activeKey="activeScopeTab"
                    :destroyInactiveTabPane="true"
                    class="contract_projects_workspace__inner_tabs"
                    @change="activeScopeTab = $event">
                    <template #tabBarExtraContent>
                        <div class="contract_projects_workspace__tabs_extra">
                            <a-button
                                class="contract_projects_workspace__tabs_refresh"
                                type="default"
                                icon="fi-rr-refresh"
                                flaticon
                                size="small"
                                :loading="scopeRefreshing"
                                @click="refreshActiveScope">
                                {{ $t('deals_contracts.refresh') }}
                            </a-button>
                        </div>
                    </template>
                    <a-tab-pane key="requests" :tab="$t('deals_contracts.requests_tab')" forceRender>
                        <ContractProjectTicketsTable
                            ref="ticketsTable"
                            :key="`tickets_${contractId}_${activeProjectId}`"
                            :contractId="contractId"
                            :projectId="activeProjectId"
                            :customerCardId="customerCardId"
                            :pageName="ticketsPageName"
                            @open="openTicket" />
                    </a-tab-pane>

                    <a-tab-pane key="tasks" :tab="$t('deals_contracts.tasks_tab')" forceRender>
                        <ContractProjectTasksTable
                            ref="tasksTable"
                            :key="`tasks_${contractId}_${activeProjectId}`"
                            :contractId="contractId"
                            :projectId="activeProjectId"
                            :pageName="tasksPageName"
                            @open="openTask" />
                    </a-tab-pane>
            </a-tabs>
        </template>

        <a-empty
            v-else
            class="contract_projects_workspace__empty"
            :description="$t('deals_contracts.projects_note')" />

        <a-modal
            class="contract_projects_modal_dialog"
            :visible="manageProjectsVisible"
            :width="760"
            :dialog-style="{ top: '20px' }"
            :destroyOnClose="true"
            :title="$t('deals_contracts.projects_label')"
            @cancel="closeManageProjectsModal">
            <div class="contract_projects_modal">
                <div class="contract_projects_modal__toolbar">
                    <div class="contract_projects_modal__filter_wrap">
                        <PageFilter
                            ref="projectsPageFilter"
                            :model="projectsFilterModel"
                            :key="projectsPageName"
                            size="large"
                            :zIndex="999999"
                            autoAdjustOverflow
                            class="contract_projects_modal__filter"
                            transitionName=""
                            placement="bottom"
                            :getPopupContainer="getProjectsPopupContainer"
                            :page_name="projectsPageName" />
                    </div>
                </div>

                <div class="contract_projects_modal__list">
                    <a-empty
                        v-if="!projectsLoading && !availableProjects.length"
                        :description="$t('deals_contracts.projects_not_found')" />

                    <div
                        v-for="project in availableProjects"
                        :key="`project_option_${project.id}`"
                        class="contract_projects_modal__item"
                        :class="{ 'is-selected': selectedProjectIdSet.has(project.id) }"
                        role="button"
                        tabindex="0"
                        @click="toggleProjectSelection(project.id)"
                        @keydown.enter.prevent="toggleProjectSelection(project.id)"
                        @keydown.space.prevent="toggleProjectSelection(project.id)">
                        <a-checkbox
                            class="contract_projects_modal__item_check"
                            :checked="selectedProjectIdSet.has(project.id)"
                            @click.stop
                            @change="toggleProjectSelection(project.id)">
                        </a-checkbox>
                        <div class="contract_projects_modal__item_content">
                            <div class="contract_projects_modal__item_head">
                                <div class="contract_projects_modal__item_title">
                                    <div class="pr-2">
                                        <a-avatar
                                            :size="26"
                                            icon="team"
                                            :src="getProjectLogoPath(project)" />
                                    </div>
                                    <span class="contract_projects_modal__item_name truncate font-medium" :title="project.name">
                                        {{ project.name }}
                                    </span>
                                </div>
                            </div>
                            <div class="contract_projects_modal__item_meta mt-2">
                                <CardDeadStart
                                    :item="project"
                                    :listProject="true" />
                                <Members
                                    v-if="hasProjectMembers(project)"
                                    :item="project"
                                    :visibleCount="1" />
                            </div>
                        </div>
                    </div>

                    <infinite-loading
                        ref="projectsInfinite"
                        :identifier="projectInfiniteId"
                        @infinite="loadProjectsInfinite"
                        :distance="10">
                        <div slot="spinner" class="contract_projects_modal__loading">
                            <a-spin size="small" />
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
            <template #footer>
                <div class="contract_projects_modal__actions">
                    <a-button
                        type="primary"
                        :loading="savingProjects"
                        @click="applyProjects">
                        {{ $t('save') }} ({{ selectedProjectIds.length }})
                    </a-button>
                    <a-button
                        type="ui_ghost"
                        @click="closeManageProjectsModal">
                        {{ $t('cancel') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ContractProjectsWorkspaceTab',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        PageFilter: () => import('@/components/PageFilter'),
        CardDeadStart: () => import('@/modules/Projects/components/CardDeadStart.vue'),
        Members: () => import('@/modules/Projects/components/Members.vue'),
        ContractProjectTicketsTable: () => import('./ContractProjectTicketsTable'),
        ContractProjectTasksTable: () => import('./ContractProjectTasksTable'),
        ContractUnlinkedItemsPanel: () => import('./ContractUnlinkedItemsPanel.vue'),
    },
    props: {
        contract: {
            type: Object,
            default: () => null,
        },
        savingProjects: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            activeProjectId: null,
            activeScopeTab: 'requests',
            showLeftArrow: false,
            showRightArrow: false,
            hoverScrollTimer: null,
            manageProjectsVisible: false,
            projectsDraft: [],
            projectOptions: [],
            projectPage: 1,
            projectHasNext: true,
            projectInfiniteId: 1,
            projectsLoading: false,
            scopeRefreshing: false,
        }
    },
    computed: {
        contractId() {
            return this.contract?.id || null
        },
        normalizedProjects() {
            const source = Array.isArray(this.contract?.projects) ? this.contract.projects : []
            return source
                .map(item => {
                    const id = this.getProjectId(item)
                    if (!id) return null
                    return {
                        id,
                        name: this.getProjectName(item, id),
                    }
                })
                .filter(Boolean)
                .sort((a, b) => a.name.localeCompare(b.name))
        },
        hasProjects() {
            return this.normalizedProjects.length > 0
        },
        customerCardId() {
            return this.contract?.customer_card?.id || null
        },
        ticketsPageName() {
            if (!this.contractId || !this.activeProjectId) return 'deals.contract_project_tickets'
            return `deals.contract_project_tickets_${this.contractId}_${this.activeProjectId}`
        },
        tasksPageName() {
            if (!this.contractId || !this.activeProjectId) return 'deals.contract_project_tasks'
            return `deals.contract_project_tasks_${this.contractId}_${this.activeProjectId}`
        },
        selectedProjectIds() {
            return this.normalizeSelectedProjects(this.projectsDraft)
        },
        selectedProjectIdSet() {
            return new Set(this.selectedProjectIds)
        },
        selectedProjects() {
            return this.selectedProjectIds.map(id => this.getProjectMeta(id))
        },
        availableProjects() {
            const selectedMap = new Map(this.selectedProjects.map(item => [item.id, item]))
            const list = [...selectedMap.values()]
            this.projectOptions.forEach(item => {
                if (!selectedMap.has(item.id)) {
                    list.push(item)
                }
            })
            return list
        },
        projectsFilterModel() {
            return 'workgroups.WorkgroupModel'
        },
        projectsPageName() {
            return 'deals_contract_projects_select.WorkgroupModel'
        },
    },
    watch: {
        normalizedProjects: {
            immediate: true,
            handler(list) {
                const hasActive = list.some(project => project.id === this.activeProjectId)
                if (!hasActive) {
                    this.activeProjectId = list[0]?.id || null
                }
                this.$nextTick(this.updateProjectsArrows)
            },
        },
        contract: {
            deep: true,
            handler() {
                this.projectsDraft = this.getProjectDraftList()
            },
        },
    },
    mounted() {
        this.projectsDraft = this.getProjectDraftList()
        window.addEventListener('resize', this.updateProjectsArrows)
        this.$nextTick(this.updateProjectsArrows)
    },
    beforeDestroy() {
        this.stopProjectsHoverScroll()
        window.removeEventListener('resize', this.updateProjectsArrows)
        eventBus.$off(`update_filter_${this.projectsFilterModel}_${this.projectsPageName}`, this.onProjectsFilterUpdated)
        eventBus.$off(`update_filter_${this.projectsPageName}`, this.onProjectsFilterUpdated)
    },
    methods: {
        getProjectsPopupContainer() {
            return document.querySelector('.contract_projects_modal_dialog') || document.body
        },
        getProjectId(item) {
            if (!item) return null
            if (typeof item === 'string' || typeof item === 'number') {
                return String(item)
            }
            return item.id ? String(item.id) : null
        },
        getProjectName(item, fallbackId) {
            if (!item || typeof item !== 'object') {
                return String(fallbackId)
            }
            return item.string_view || item.name || String(fallbackId)
        },
        getProjectDraftList() {
            const source = Array.isArray(this.contract?.projects) ? this.contract.projects : []
            return source.map(item => this.getProjectId(item)).filter(Boolean)
        },
        normalizeSelectedProjects(list) {
            const source = Array.isArray(list) ? list : []
            const uniqueIds = new Set()
            source.forEach(item => {
                if (item && typeof item === 'object' && item.id) {
                    uniqueIds.add(String(item.id))
                    return
                }
                if (item || item === 0) {
                    uniqueIds.add(String(item))
                }
            })
            return Array.from(uniqueIds)
        },
        emitSaveProjects(projectIds) {
            this.$emit('save-projects', { projects: projectIds })
        },
        openManageProjectsModal() {
            this.projectsDraft = this.getProjectDraftList()
            this.manageProjectsVisible = true
            this.reloadProjectsList()
            eventBus.$off(`update_filter_${this.projectsFilterModel}_${this.projectsPageName}`, this.onProjectsFilterUpdated)
            eventBus.$off(`update_filter_${this.projectsPageName}`, this.onProjectsFilterUpdated)
            eventBus.$on(`update_filter_${this.projectsFilterModel}_${this.projectsPageName}`, this.onProjectsFilterUpdated)
            eventBus.$on(`update_filter_${this.projectsPageName}`, this.onProjectsFilterUpdated)
        },
        closeManageProjectsModal() {
            this.manageProjectsVisible = false
            eventBus.$off(`update_filter_${this.projectsFilterModel}_${this.projectsPageName}`, this.onProjectsFilterUpdated)
            eventBus.$off(`update_filter_${this.projectsPageName}`, this.onProjectsFilterUpdated)
        },
        onProjectsFilterUpdated() {
            this.reloadProjectsList()
            this.$nextTick(() => this.$refs.projectsInfinite?.stateChanger?.reset())
        },
        reloadProjectsList() {
            this.projectOptions = []
            this.projectPage = 1
            this.projectHasNext = true
            this.projectInfiniteId += 1
        },
        normalizeProjectOption(item) {
            const id = this.getProjectId(item)
            if (!id) return null
            return {
                ...item,
                id,
                name: this.getProjectName(item, id),
                workgroup_logo: item?.workgroup_logo || null,
            }
        },
        mergeProjectOptions(list) {
            const map = new Map()
            list.forEach(item => {
                const normalized = this.normalizeProjectOption(item)
                if (!normalized) return
                map.set(normalized.id, normalized)
            })
            return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name))
        },
        getProjectMeta(id) {
            const normalizedId = String(id)
            const fromOptions = this.projectOptions.find(item => item.id === normalizedId)
            if (fromOptions) return fromOptions

            const source = Array.isArray(this.contract?.projects) ? this.contract.projects : []
            const fromContract = source.find(item => this.getProjectId(item) === normalizedId)
            if (fromContract) {
                return {
                    id: normalizedId,
                    ...fromContract,
                    name: this.getProjectName(fromContract, normalizedId),
                    workgroup_logo: fromContract?.workgroup_logo || null,
                }
            }
            return { id: normalizedId, name: normalizedId, workgroup_logo: null }
        },
        toggleProjectSelection(projectId) {
            const id = String(projectId)
            const selected = this.selectedProjectIds
            if (this.selectedProjectIdSet.has(id)) {
                this.projectsDraft = selected.filter(item => item !== id)
                return
            }
            this.projectsDraft = [...selected, id]
        },
        async loadProjectsInfinite($state) {
            if (this.projectsLoading) {
                return
            }
            if (!this.projectHasNext) {
                $state.complete()
                return
            }
            try {
                this.projectsLoading = true
                const params = {
                    page_size: 15,
                    page: this.projectPage,
                    is_project: 1,
                    page_name: this.projectsPageName,
                    filters: { is_finished: false },
                }
                const { data } = await this.$http.get('/work_groups/workgroups/', { params })
                const incoming = Array.isArray(data?.results) ? data.results : []
                this.projectOptions = this.mergeProjectOptions([...this.projectOptions, ...incoming])
                this.projectPage += 1
                this.projectHasNext = Boolean(data?.next)
                if (this.projectHasNext) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.projectsLoading = false
            }
        },
        applyProjects() {
            const projects = this.normalizeSelectedProjects(this.projectsDraft)
            this.emitSaveProjects(projects)
            this.closeManageProjectsModal()
        },
        getProjectLogoPath(project) {
            return project?.workgroup_logo?.path || null
        },
        hasProjectMembers(project) {
            return Array.isArray(project?.workgroup_members) && Boolean(project?.founder?.id)
        },
        updateProjectsArrows() {
            const el = this.$refs.projectsScroll
            if (!el) {
                this.showLeftArrow = false
                this.showRightArrow = false
                return
            }
            const maxScrollLeft = Math.max(0, el.scrollWidth - el.clientWidth)
            this.showLeftArrow = el.scrollLeft > 6
            this.showRightArrow = el.scrollLeft < maxScrollLeft - 6
        },
        scrollProjects(direction) {
            const el = this.$refs.projectsScroll
            if (!el) return
            const delta = direction === 'left' ? -240 : 240
            el.scrollBy({ left: delta, behavior: 'smooth' })
        },
        startProjectsHoverScroll(direction) {
            this.stopProjectsHoverScroll()
            const step = direction === 'left' ? -14 : 14
            this.hoverScrollTimer = setInterval(() => {
                const el = this.$refs.projectsScroll
                if (!el) return
                el.scrollLeft += step
                this.updateProjectsArrows()
            }, 22)
        },
        stopProjectsHoverScroll() {
            if (this.hoverScrollTimer) {
                clearInterval(this.hoverScrollTimer)
                this.hoverScrollTimer = null
            }
        },
        openTicket(id) {
            if (!id) return
            this.$emit('open-related', { type: 'ticket', id })
        },
        openTask(id) {
            if (!id) return
            this.$emit('open-related', { type: 'task', id })
        },
        openRelatedFromPanel(payload) {
            if (!payload?.id || !payload?.type) return
            this.$emit('open-related', payload)
        },
        async handleUnlinkedAssigned() {
            await Promise.all([
                this.$refs.ticketsTable?.loadData?.(),
                this.$refs.tasksTable?.loadData?.(),
            ])
        },
        async refreshActiveScope() {
            if (this.scopeRefreshing) return
            this.scopeRefreshing = true
            try {
                if (this.activeScopeTab === 'tasks') {
                    await this.$refs.tasksTable?.loadData?.()
                    return
                }
                await this.$refs.ticketsTable?.loadData?.()
            } finally {
                this.scopeRefreshing = false
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_projects_workspace {
    margin-top: 6px;
}

.contract_projects_toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    margin-bottom: 12px;
}

.contract_projects_toolbar__scroll_wrap {
    position: relative;
    flex: 1;
    min-width: 0;
    margin-right: 18px;
}

.contract_projects_toolbar__scroll {
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;
}

.contract_projects_toolbar__scroll::-webkit-scrollbar {
    display: none;
}

.contract_projects_toolbar__list {
    width: max-content;
    min-width: 100%;
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 2px 0;
}

.contract_project_item {
    position: relative;
}

.contract_project_tab {
    border: 1px solid #d9d9d9;
    background: #fff;
    color: rgba(0, 0, 0, 0.85);
    border-radius: 999px;
    min-height: 32px;
    padding: 0 14px;
    display: inline-flex;
    align-items: center;
    font-weight: 500;
    user-select: none;
    transition: border-color .2s ease, background-color .2s ease, color .2s ease;
}

.contract_project_tab.is-active {
    border-color: var(--blue);
    background: var(--primaryHover);
    color: var(--blue);
}

.contract_project_tab:not(.is-active):hover {
    border-color: var(--blue);
    color: var(--blue);
}

.contract_project_tab__name {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    letter-spacing: 0.01em;
}

.contract_projects_scroll_arrow {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
}

.contract_projects_scroll_arrow--left {
    left: -10px;
}

.contract_projects_scroll_arrow--right {
    right: -10px;
}

.contract_projects_toolbar__edit {
    height: 36px;
    padding: 0 12px;
    flex-shrink: 0;
}

.contract_projects_workspace__inner_tabs {
    margin-top: 6px;

    &::v-deep > .ant-tabs-bar {
        display: block !important;
    }

    &::v-deep > .ant-tabs-bar .ant-tabs-extra-content {
        display: flex;
        align-items: center;
    }

    &::v-deep .ant-tabs-content-holder {
        min-height: 460px;
    }
}

.contract_projects_workspace__tabs_extra {
    display: flex;
    align-items: center;
    height: 100%;
}

.contract_projects_workspace__tabs_refresh {
    border-color: transparent !important;
    background: transparent !important;
    box-shadow: none !important;
    transform: translateY(-1px);
}

.contract_projects_workspace__tabs_refresh:hover,
.contract_projects_workspace__tabs_refresh:focus {
    border-color: transparent !important;
    background: transparent !important;
}

.contract_projects_workspace__empty {
    margin-top: 14px;
}

.contract_projects_modal {
    display: grid;
    gap: 12px;
}

.contract_projects_modal__toolbar {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    gap: 10px;
}

.contract_projects_modal__list {
    display: grid;
    gap: 10px;
    width: 100%;
    min-width: 0;
    padding-right: 2px;
}

.contract_projects_modal__item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
    padding: 12px;
    cursor: pointer;
    background: #f7f9fc;
    border: 1px solid transparent;
    border-radius: var(--borderRadius);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.contract_projects_modal__item:hover {
    background: #f7f9fc;
}

.contract_projects_modal__item.is-selected {
    border-color: #2f5ff5;
    background: #f7f9fc;
    box-shadow: 0 6px 16px rgba(47, 95, 245, 0.12);
}

.contract_projects_modal__item_check {
    flex-shrink: 0;
    margin-top: 2px;
}

.contract_projects_modal__item_content {
    min-width: 0;
    flex: 1;
}

.contract_projects_modal__item_head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 0;
}

.contract_projects_modal__item_title {
    display: flex;
    align-items: center;
    min-width: 0;
    flex: 1;
}

.contract_projects_modal__item_name {
    display: block;
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.contract_projects_modal__item_meta {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    width: 100%;
    min-width: 0;

    &::v-deep {
        .wrg_dates {
            min-width: 0;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .flex.items-center,
        .member {
            flex-shrink: 0;
        }
    }
}

.contract_projects_modal__loading {
    display: flex;
    justify-content: center;
    padding: 10px;
}

.contract_projects_modal__actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    width: 100%;
}

.contract_projects_modal_dialog {
    &::v-deep {
        .ant-modal {
            max-width: calc(100vw - 40px);
        }

        .ant-modal-body {
            max-width: 100%;
            overflow: visible;
        }

        .contract_projects_modal__filter {
            width: 100%;
        }

        .contract_projects_modal__filter .filter_input {
            border-radius: 8px;
            background: #f7f9fc;
            border-color: #f7f9fc !important;
            box-shadow: initial !important;
            color: var(--text);

            .ant-input {
                background: #f7f9fc;
            }
        }

        .contract_projects_modal__filter_wrap {
            width: 100%;

            .filter_pop_wrapper {
                max-width: 100%;
                min-width: 100%;
            }
        }

        .ant-modal-footer {
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
    }
}

@media (max-width: 991px) {
    .contract_projects_toolbar {
        flex-direction: column;
        align-items: stretch;
    }

    .contract_projects_toolbar__edit {
        width: 100%;
        justify-content: center;
    }

    .contract_projects_modal__actions {
        flex-direction: column;

        .ant-btn {
            width: 100%;
        }
    }
}
</style>
