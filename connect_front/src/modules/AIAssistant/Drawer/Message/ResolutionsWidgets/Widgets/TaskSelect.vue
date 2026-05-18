<template>
    <div class="wdg_input">
        <template v-if="isEdit">
            <div
                class="popover_input ant-input flex items-center relative ant-input-lg truncate"
                @click="openDrawer">
                <a-tooltip
                    v-if="value"
                    destroyTooltipOnHide
                    :title="taskTitle"
                    class="mr-2 truncate">
                    <a-tag
                        color="blue"
                        class="tag_block truncate"
                        @click.stop="openDrawer">
                        {{ taskTitle }}
                    </a-tag>
                </a-tooltip>
                <a-button
                    type="link"
                    class="px-0 select_trigger"
                    @click.stop="openDrawer">
                    {{ value ? '' : $t('task.select') }}
                </a-button>
                <a-button
                    v-if="value"
                    type="link"
                    icon="close-circle"
                    class="px-0 text-current remove_parent"
                    @click.stop="clearValue" />
            </div>

            <a-modal
                :title="$t('task.select_task')"
                :width="isMobile ? '100%' : 560"
                :dialog-style="{ top: '20px' }"
                :visible="drawerVisible"
                destroyOnClose
                class="ai-task-select-modal"
                @afterVisibleChange="afterVisibleChange"
                @cancel="closeDrawer">
                <div class="drawer_select_filter pb-2">
                    <PageFilter
                        :model="pageModel"
                        :key="pageName"
                        size="large"
                        :zIndex="999999"
                        ref="pageFilter"
                        initInputFocus
                        autoAdjustOverflow
                        class="modal_filter"
                        transitionName=""
                        placement="bottom"
                        :getPopupContainer="getPopupContainer"
                        :page_name="pageName" />
                </div>

                <div class="drawer_select_list">
                    <div class="max-w-full">
                        <div
                        v-for="task in taskList"
                            :key="task.id"
                            class="flex items-center">
                            <WorkplanItem
                                :item="task"
                                :selectingSubtask="checkActive(task)"
                                class="w-full task_card"
                                :selectFunction="selectTask"
                                :isScrolling="false"
                                :myTaskEnabled="false"
                                :useActions="false"
                                :showStatus="true" />
                        </div>
                    </div>

                    <div v-if="!loading && !taskList.length" class="field_empty py-4">
                        Нет задач
                    </div>

                    <infinite-loading
                        ref="taskInfinite"
                        :identifier="identifier"
                        :distance="10"
                        @infinite="getTaskList">
                        <div slot="spinner">
                            <a-spin class="w-full" />
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>

                <template #footer>
                    <a-button block type="ui_ghost" @click="closeDrawer">
                        {{ $t('task.close') }}
                    </a-button>
                </template>
            </a-modal>
        </template>

        <div v-else>
            <div v-if="value" class="truncate">
                {{ taskTitle }}
            </div>
            <div v-else class="field_empty">
                {{ $t('ai_assistant.not_specified') }}
            </div>
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

export default {
    props: { ...props },
    mixins: [mixins],
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        WorkplanItem: () => import('@apps/vue2TaskComponent/components/Kanban/WorkplanItem.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    data() {
        return {
            value: null,
            drawerVisible: false,
            taskList: [],
            page: 0,
            loading: false,
            scrollStatus: true,
            identifier: Date.now(),
            pageName: 'page_list_work_plan_task.TaskModel',
            pageModel: 'tasks.TaskModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        requestFilters() {
            const defaultFilters = {
                status__task_status_type__is_complete: false
            }

            if (this.widgetKey !== 'parent') {
                return undefined
            }

            return JSON.stringify(defaultFilters)
        },
        resolutionValue() {
            return this.intents?.resolutions?.[this.widgetKey]?.value || null
        },
        taskTitle() {
            if (!this.value) return ''
            return this.value.counter
                ? `#${this.value.counter} ${this.value.name}`
                : this.value.name
        }
    },
    watch: {
        resolutionValue: {
            deep: true,
            handler() {
                this.syncValueFromResolution()
            }
        }
    },
    created() {
        this.syncValueFromResolution()
    },
    methods: {
        afterVisibleChange(vis) {
            if (vis) {
                this.$nextTick(() => {
                    if (this.$refs.pageFilter) {
                        this.$refs.pageFilter.searchFocus()
                    }
                })
            }
        },
        normalizeTask(task) {
            if (!task) return null
            return {
                ...task,
                id: task.id,
                name: task.name || task.repr || '',
                counter: task.counter || null
            }
        },
        checkActive(task) {
            return this.value?.id !== task?.id
        },
        async syncValueFromResolution() {
            const resolutionValue = this.intents?.resolutions?.[this.widgetKey]?.value
            if (!resolutionValue) {
                this.value = null
                return
            }

            if (typeof resolutionValue === 'object') {
                this.value = this.normalizeTask(resolutionValue)
                return
            }

            try {
                const { data } = await this.$http.get('tasks/task/list', {
                    params: {
                        task_type: 'task,stage,milestone',
                        filters: { id: resolutionValue }
                    }
                })
                this.value = this.normalizeTask(data?.results?.[0] || null)
            } catch (error) {
                errorHandler({ error, show: false })
                this.value = null
            }
        },
        openDrawer() {
            if (!this.isEdit) return
            this.drawerVisible = true
            this.reloadList()
        },
        closeDrawer() {
            this.drawerVisible = false
        },
        getPopupContainer() {
            return document.querySelector('.ai-task-select-modal')
        },
        clearValue() {
            this.value = null
            this.storeChangeValue({ value: null, useRepr: true })
            this.updateTimer(null)
        },
        selectTask(task) {
            const normalizedTask = this.normalizeTask(task)
            this.value = normalizedTask
            this.storeChangeValue({ value: normalizedTask, useRepr: true })
            this.updateTimer(normalizedTask.id)
            this.closeDrawer()
        },
        reloadList() {
            this.page = 0
            this.taskList = []
            this.loading = false
            this.scrollStatus = true
            this.identifier = Date.now()
            this.$nextTick(() => {
                if (this.$refs.taskInfinite) {
                    this.$refs.taskInfinite.stateChanger.reset()
                }
            })
        },
        async getTaskList($state = null) {
            if (!this.drawerVisible || this.loading || !this.scrollStatus) {
                if ($state) $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1

                const params = {
                    page_size: 8,
                    page: this.page,
                    page_name: this.pageName,
                    task_type: 'task,stage,milestone',
                    parent: 'all',
                    ordering: 'status,-created_at'
                }

                if (this.requestFilters) {
                    params.filters = this.requestFilters
                }

                const { data } = await this.$http.get('/tasks/task/list/', { params })
                const nextItems = (data?.results || []).map(item => this.normalizeTask(item))
                const existingIds = new Set(this.taskList.map(task => task.id))
                this.taskList = this.taskList.concat(nextItems.filter(task => !existingIds.has(task.id)))

                if (!data?.next) {
                    this.scrollStatus = false
                    if ($state) $state.complete()
                } else if ($state) {
                    $state.loaded()
                }
            } catch (error) {
                errorHandler({ error, show: false })
                this.scrollStatus = false
                if ($state) $state.complete()
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, this.reloadList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`, this.reloadList)
    }
}
</script>

<style lang="scss" scoped>
.wdg_input {
    &::v-deep {
        .ant-input {
            height: initial;
            padding: 0;
            min-height: initial;
            border: 0;
            box-shadow: none;
            background: transparent;
            cursor: pointer;
        }

        .tag_block {
            cursor: pointer;
        }
    }
}

.task_card {
    &::v-deep {
        .kanban-card {
            background: #fff;
            cursor: default;
        }
    }
}

.select_trigger {
    color: #888888;

    &:hover,
    &:focus,
    &:active {
        color: #888888;
    }
}

.modal_filter {
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

.drawer_select_filter {
    &::v-deep {
        .filter_pop_wrapper {
            max-width: 100%;
            min-width: 100%;
        }
    }
}
</style>
