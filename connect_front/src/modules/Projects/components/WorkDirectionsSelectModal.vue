<template>
    <a-modal
        :visible="visible"
        :width="isMobile ? '100%' : '90%'"
        :footer="null"
        destroyOnClose
        :wrapClassName="modalWrapClass"
        :bodyStyle="modalBodyStyle"
        @afterVisibleChange="afterVisibleChange"
        @cancel="close">
        <template #title>
            {{ $t('project.work_directions') }}
        </template>

        <div class="work_direction_modal">
            <ListView
                v-if="!isMobile && visible"
                ref="listViewRef"
                addButtonText="Создать"
                :add="openCreateDirection"
                tableType="work_directions"
                :model="model"
                :pageName="pageName"
                :endpoint="endpoint"
                :params="tableParams"
                multiple
                :selectedItems="currentSelected"
                @select="selectDirections" />

            <div v-else class="work_direction_modal__mobile">
                <div class="work_direction_modal__mobile-scroll">
                    <div
                        v-if="listEmpty"
                        class="pt-7">
                        <a-empty :description="$t('project.no_data')" />
                    </div>

                    <div
                        v-for="item in list"
                        :key="item.id"
                        class="direction_card"
                        @click="toggleMobileSelection(item)">
                        <div class="direction_card__main">
                            <a-checkbox
                                :checked="isSelected(item)"
                                @click.stop
                                @change="toggleMobileSelection(item)" />
                            <div class="direction_card__content">
                                <div class="direction_card__title">
                                    {{ item.name || '-' }}
                                </div>
                                <div v-if="item.contractor" class="direction_card__organization">
                                    <a-avatar
                                        :size="22"
                                        :src="item.contractor.logo"
                                        icon="fi-rr-users-alt"
                                        flaticon />
                                    <span class="direction_card__organization-name">
                                        {{ item.contractor.name || item.contractor.full_name || '-' }}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="direction_card__actions" @click.stop>
                            <DirectionsRowActions :record="item" />
                        </div>
                    </div>

                    <infinite-loading
                        ref="catalog_infinity"
                        :identifier="pageName + '_' + mobileListKey"
                        :distance="250"
                        @infinite="getMobileList">
                        <div
                            slot="spinner"
                            class="flex items-center justify-center inf_spinner mt-3">
                            <a-spin />
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>

                <div class="work_direction_modal__footer">
                    <a-button
                        block
                        type="flat_primary"
                        @click="selectDirections">
                        {{ $t('project.select') }}
                    </a-button>
                </div>

                <div class="float_add mobile">
                    <div class="filter_slot">
                        <PageFilter
                            :model="model"
                            :title="$t('filters')"
                            filterButtonSize="large"
                            :zIndex="6000"
                            size="large"
                            :page_name="pageName" />
                    </div>
                    <a-button
                        flaticon
                        shape="circle"
                        size="large"
                        type="primary"
                        icon="fi-rr-plus-small"
                        @click="openCreateDirection" />
                </div>
            </div>
        </div>

        <WorkDirectionFormModal
            ref="createModalRef"
            model="catalogs.WorkDirectionModel"
            contractorSelect
            :contractor="organization"
            :afterCreate="selectCreatedDirection" />
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    components: {
        ListView: () => import('@/components/ListView/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        WorkDirectionFormModal: () => import('@/modules/Directories/components/WorkDirectionFormModal.vue'),
        DirectionsRowActions: () => import('@/components/TableWidgets/Widgets/DirectionsRowActions.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        organization: {
            type: String,
            default: ''
        },
        selectedItems: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            visible: false,
            model: 'catalogs.WorkDirectionModel',
            pageName: 'project_work_directions_select',
            endpoint: '/catalogs/work_directions/',
            currentSelected: [],
            list: [],
            loading: false,
            next: true,
            page: 0,
            pageSize: 15,
            listEmpty: false,
            mobileListKey: 0
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        tableParams() {
            const params = {
                filters: JSON.stringify({
                    is_archive: false
                })
            }
            if (this.organization) {
                params.contractor = this.organization
            }
            return params
        },
        modalWrapClass() {
            return this.isMobile
                ? 'project-work-directions-modal project-work-directions-modal--mobile'
                : 'project-work-directions-modal'
        },
        modalBodyStyle() {
            if (this.isMobile) {
                return {
                    height: 'calc(100vh - 55px)',
                    padding: '12px'
                }
            }
            return {}
        }
    },
    watch: {
        organization(newValue, oldValue) {
            if (newValue === oldValue) return
            this.currentSelected = []
            if (this.visible) {
                if (this.isMobile) {
                    this.reloadMobileList()
                } else {
                    this.$refs.listViewRef?.$refs?.tableRef?.reloadTableData?.()
                }
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, this.handleExternalUpdate)
        eventBus.$on(`update_filter_${this.pageName}`, this.handleExternalUpdate)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`, this.handleExternalUpdate)
        eventBus.$off(`update_filter_${this.pageName}`, this.handleExternalUpdate)
    },
    methods: {
        open() {
            this.visible = true
        },
        close() {
            this.visible = false
        },
        syncSelectedItems() {
            this.currentSelected = Array.isArray(this.selectedItems)
                ? this.selectedItems.map(item => ({ ...item }))
                : []
        },
        afterVisibleChange(vis) {
            if (!vis) return
            this.syncSelectedItems()
            if (this.isMobile) {
                this.reloadMobileList()
            }
        },
        selectDirections(items) {
            if (Array.isArray(items)) {
                this.currentSelected = items
            }
            this.$emit('select', this.currentSelected)
            this.close()
        },
        openCreateDirection() {
            this.$refs.createModalRef?.open()
        },
        selectCreatedDirection(direction, meta = {}) {
            if (!direction?.id) return
            const index = this.currentSelected.findIndex(item => item.id === direction.id)
            if (index === -1) {
                if (!meta.edit) {
                    this.currentSelected.unshift(direction)
                }
            } else {
                this.currentSelected.splice(index, 1, direction)
            }
            if (this.isMobile) {
                const listIndex = this.list.findIndex(item => item.id === direction.id)
                if (listIndex === -1) {
                    this.list.unshift(direction)
                } else {
                    this.list.splice(listIndex, 1, direction)
                }
            } else if (this.$refs.listViewRef?.$refs?.tableRef) {
                this.$refs.listViewRef.$refs.tableRef.selectedRows = [...this.currentSelected]
                this.$nextTick(() => {
                    this.$refs.listViewRef.$refs.tableRef.gridApi?.refreshCells?.({ force: true })
                    this.$refs.listViewRef.$refs.tableRef.reloadTableData?.()
                })
            }
        },
        isSelected(item) {
            return this.currentSelected.findIndex(selected => selected.id === item.id) !== -1
        },
        toggleMobileSelection(item) {
            const index = this.currentSelected.findIndex(selected => selected.id === item.id)
            if (index === -1) {
                this.currentSelected.push(item)
            } else {
                this.currentSelected.splice(index, 1)
            }
        },
        reloadMobileList() {
            this.page = 0
            this.next = true
            this.list = []
            this.listEmpty = false
            this.mobileListKey += 1
            this.$nextTick(() => {
                this.$refs.catalog_infinity?.stateChanger?.reset()
            })
        },
        async getMobileList($state) {
            if (!this.organization || !this.next || this.loading) {
                $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1
                const { data } = await this.$http.get(this.endpoint, {
                    params: {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName,
                        contractor: this.organization,
                        filters: JSON.stringify({
                            is_archive: false
                        })
                    }
                })

                const results = data?.results || []
                if (results.length) {
                    this.list = this.list.concat(results)
                }

                this.next = Boolean(data?.next)

                if (this.page === 1 && !results.length) {
                    this.listEmpty = true
                }

                if (this.next) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.$message.error(this.$t('project.error'))
                $state.complete()
            } finally {
                this.loading = false
            }
        },
        handleExternalUpdate() {
            if (!this.visible) return
            if (this.isMobile) {
                this.reloadMobileList()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.work_direction_modal{
    height: 100%;
    &__mobile{
        height: 99%;
        min-height: 99%;
        display: flex;
        flex-direction: column;
        position: relative;
    }
    &__mobile-scroll{
        flex: 1 1 auto;
        min-height: 99%;
        overflow-y: auto;
        overflow-x: hidden;
        padding-top: 12px;
        padding-bottom: 92px;
    }
    &__footer{
        margin-top: 12px;
        padding-top: 8px;
        background: #fff;
        display: flex;
        position: sticky;
        bottom: 0;
        z-index: 3;
    }
}

.direction_card{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    padding: 12px;
    border-bottom: 1px solid var(--border2);
    background: #fff;
    &__main{
        display: flex;
        align-items: flex-start;
        min-width: 0;
        flex: 1 1 auto;
    }
    &__content{
        min-width: 0;
        margin-left: 10px;
    }
    &__title{
        font-size: 14px;
        font-weight: 600;
        line-height: 1.35;
    }
    &__organization{
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--gray);
        font-size: 12px;
    }
    &__organization-name{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    &__actions{
        flex-shrink: 0;
    }
}

</style>

<style lang="scss">
.project-work-directions-modal{
    .ant-modal-body{
        padding-top: 12px;
    }
    &.project-work-directions-modal--mobile{
        .ant-modal{
            width: 100vw !important;
            max-width: 100vw;
            top: 0;
            padding-bottom: 0;
            margin: 0;
        }
        .ant-modal-content{
            min-height: 100vh;
            border-radius: 0;
            display: flex;
            flex-direction: column;
        }
        .ant-modal-body{
            height: calc(100vh - 55px);
            padding: 12px;
            overflow: hidden;
        }
        .ant-modal-close{
            top: 8px;
            right: 8px;
        }
        .float_add.mobile{
            bottom: calc(88px + env(safe-area-inset-bottom)) !important;
        }
    }
}
</style>
