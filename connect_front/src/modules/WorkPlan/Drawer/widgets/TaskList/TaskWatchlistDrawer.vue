<template>
    <div>
        <DrawerWrapper v-model="visible" :titleTruncate="isMobile" :width="1460">
            <template #title>
                <div class="w-full flex items-center task_watchlist_drawer_header" :title="drawerTitle">
                    <i v-if="!isMobile" class="fi fi-rr-calendar-check task_watchlist_drawer_header__icon" />
                    <div class="title task_watchlist_drawer_header__title">
                        {{ drawerTitle }}
                    </div>
                </div>
            </template>
            <template #body>
                <div ref="bodyRef" class="task_watchlist_drawer_body">
                <div class="mb-3 flex items-center gap-2">
                    <a-input
                        v-model="search"
                        :placeholder="$t('workplan.search')"
                        size="large"
                        class="tab_search"
                        @change="changeSearch()">
                        <template #suffix>
                            <transition name="fade-scale" mode="out-in">
                                <a-button
                                    v-if="search.length"
                                    type="ui_ghost"
                                    size="small"
                                    flaticon
                                    shape="circle"
                                    icon="fi-rr-cross-small"
                                    @click="clearSearch()" />
                                <i v-else class="fi fi-rr-search mr-1" />
                            </transition>
                        </template>
                    </a-input>
                </div>

                <div class="mb-3 flex" :class="isMobile && 'mob_scroll'">
                    <div :class="isMobile && 'task_watchlist_drawer_role_wrap'">
                        <Segmented
                            v-model="role"
                            deselectable
                            :options="roleList">
                            <template #default="{ option }">
                                <div class="task_watchlist_drawer_role">
                                    <span class="task_watchlist_drawer_role__title">{{ option.title }}</span>
                                    <span class="task_watchlist_drawer_role__badges">
                                        <a-badge
                                            :count="option.overdue"
                                            :overflow-count="9999"
                                            :number-style="roleBadgeStyle('overdue')"
                                            class="task_watchlist_drawer_role__badge overdue" />
                                        <a-badge
                                            :count="option.stalled"
                                            :overflow-count="9999"
                                            :number-style="roleBadgeStyle('stalled')"
                                            class="task_watchlist_drawer_role__badge stalled" />
                                    </span>
                                </div>
                            </template>
                        </Segmented>
                    </div>
                </div>

                <div class="task_watchlist_drawer_sections">
                    <div v-if="overdueSection.results.length || overdueSection.loading" class="task_block_item">
                        <h2 class="task_block_title overdue" @click="toggleSection('overdue')">
                            <span class="task_block_title__main">
                                <span>{{ $t('workplan.task_watchlist_overdue_title') }}</span>
                                <a-badge
                                    v-if="selectedCounts.overdue"
                                    :count="selectedCounts.overdue"
                                    :overflow-count="9999"
                                    :number-style="{ backgroundColor: '#fdd5d5', color: '#FF5C5C' }"
                                    class="ml-2" />
                            </span>
                            <i class="fi fi-rr-angle-small-up task_block_title__arrow" :class="{ collapsed: !sectionOpen.overdue }" />
                        </h2>
                        <template v-if="sectionOpen.overdue && overdueSection.page === 1 && overdueSection.loading">
                            <CardLoading v-for="i in 3" :key="`overdue_loading_${i}`" />
                        </template>
                        <template v-if="sectionOpen.overdue">
                            <transition-group name="watchlist-card-slide" tag="div">
                            <TaskWatchlistCard
                                v-for="task in overdueSection.results"
                                :key="`overdue_${task.id}`"
                                :storeKey="storeKey"
                                :popupContainer="popupContainer"
                                :task="task"
                                group="overdue"
                                @reload="handleTaskReload(task.id)" />
                            </transition-group>
                        <a-button
                            v-if="overdueSection.results.length && overdueSection.next"
                            :loading="overdueSection.loading"
                            type="ui"
                            ghost
                            class="task_watchlist_drawer__load_more"
                            block
                            @click="nextLoading('overdue')">
                            {{ $t('workplan.load_more') }}
                        </a-button>
                        </template>
                    </div>

                    <div v-if="stalledSection.results.length || stalledSection.loading" class="task_block_item">
                        <h2 class="task_block_title stalled" @click="toggleSection('stalled')">
                            <span class="task_block_title__main">
                                <span>{{ $t('workplan.task_watchlist_stalled_title') }}</span>
                                <a-badge
                                    v-if="selectedCounts.stalled"
                                    :count="selectedCounts.stalled"
                                    :overflow-count="9999"
                                    :number-style="{ backgroundColor: '#fef8eb', color: '#FF9A01' }"
                                    class="ml-2" />
                            </span>
                            <i class="fi fi-rr-angle-small-up task_block_title__arrow" :class="{ collapsed: !sectionOpen.stalled }" />
                        </h2>
                        <template v-if="sectionOpen.stalled && stalledSection.page === 1 && stalledSection.loading">
                            <CardLoading v-for="i in 3" :key="`stalled_loading_${i}`" />
                        </template>
                        <template v-if="sectionOpen.stalled">
                            <transition-group name="watchlist-card-slide" tag="div">
                            <TaskWatchlistCard
                                v-for="task in stalledSection.results"
                                :key="`stalled_${task.id}`"
                                :storeKey="storeKey"
                                :popupContainer="popupContainer"
                                :task="task"
                                group="stalled"
                                @reload="handleTaskReload(task.id)" />
                            </transition-group>
                        <a-button
                            v-if="stalledSection.results.length && stalledSection.next"
                            :loading="stalledSection.loading"
                            type="ui"
                            ghost
                            class="task_watchlist_drawer__load_more"
                            block
                            @click="nextLoading('stalled')">
                            {{ $t('workplan.load_more') }}
                        </a-button>
                        </template>
                    </div>
                </div>

                <a-empty
                    v-if="!isAnyLoading && !overdueSection.results.length && !stalledSection.results.length"
                    :description="$t('workplan.no_tasks')" />
                </div>
            </template>
            <template v-if="isMobile" #footer>
                <a-button type="ui_ghost" size="large" block @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </template>
        </DrawerWrapper>
        <a-modal
            :visible="closeConfirmVisible"
            :footer="null"
            :closable="false"
            :maskClosable="false"
            :width="520"
            centered>
            <div class="task_watchlist_confirm">
                <div class="task_watchlist_confirm__title">
                    <i class="fi fi-rr-exclamation mr-2" />
                    {{ $t('workplan.task_watchlist_close_title') }}
                </div>
                <div class="task_watchlist_confirm__text">
                    {{ closeConfirmText }}
                </div>
                <div class="task_watchlist_confirm__actions">
                    <a-button type="primary" size="large" block @click="closeConfirmVisible = false">
                        {{ $t('workplan.task_watchlist_close_continue') }}
                    </a-button>
                    <a-button type="ui_ghost" size="large" block @click="forceCloseDrawer()">
                        {{ $t('workplan.task_watchlist_close_exit') }}
                    </a-button>
                </div>
            </div>
        </a-modal>
    </div>
</template>

<script>
import axios from '@/config/axios'
import { errorHandler } from '@/utils/index.js'

const createSection = () => ({
    loading: false,
    page: 1,
    next: true,
    results: []
})

let searchTimer

export default {
    props: {
        value: {
            type: Boolean,
            default: false
        },
        storeKey: {
            type: String,
            required: true
        },
        taskWatchlistCount: {
            type: Object,
            default: () => ({
                overdue: 0,
                stalled: 0,
                roles: {}
            })
        }
    },
    components: {
        DrawerWrapper: () => import('../../DrawerWrapper.vue'),
        CardLoading: () => import('./CardLoading.vue'),
        TaskWatchlistCard: () => import('./TaskWatchlistCard.vue'),
        Segmented: () => import('@/modules/UIModules/Segmented')
    },
    computed: {
        visible: {
            get() {
                return this.value
            },
            set(value) {
                if(value) {
                    this.$emit('input', value)
                    return
                }

                if(this.skipCloseConfirm || !this.hasPendingTasks) {
                    this.$emit('input', value)
                    return
                }

                this.closeConfirmVisible = true
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        roleList() {
            const roles = this.taskWatchlistCountLocal.roles || {}

            return [
                {
                    key: 'is_executor',
                    title: this.$t('workplan.role_do'),
                    overdue: Number(roles.is_executor?.overdue) || 0,
                    stalled: Number(roles.is_executor?.stalled) || 0
                },
                {
                    key: 'is_owner',
                    title: this.$t('workplan.role_delegate'),
                    overdue: Number(roles.is_owner?.overdue) || 0,
                    stalled: Number(roles.is_owner?.stalled) || 0
                },
                {
                    key: 'is_project_moderator',
                    title: this.$t('workplan.task_watchlist_role_project_moderator'),
                    overdue: Number(roles.is_project_moderator?.overdue) || 0,
                    stalled: Number(roles.is_project_moderator?.stalled) || 0
                }
            ]
        },
        selectedCounts() {
            const roleCounts = this.taskWatchlistCountLocal.roles?.[this.role]

            if(roleCounts) {
                return {
                    overdue: Number(roleCounts.overdue) || 0,
                    stalled: Number(roleCounts.stalled) || 0
                }
            }

            return {
                overdue: Number(this.taskWatchlistCountLocal.overdue) || 0,
                stalled: Number(this.taskWatchlistCountLocal.stalled) || 0
            }
        },
        isAnyLoading() {
            return this.overdueSection.loading || this.stalledSection.loading
        },
        pendingOverdueCount() {
            return Number(this.taskWatchlistCountLocal.overdue) || 0
        },
        pendingStalledCount() {
            return Number(this.taskWatchlistCountLocal.stalled) || 0
        },
        hasPendingTasks() {
            return this.pendingOverdueCount > 0 || this.pendingStalledCount > 0
        },
        closeConfirmText() {
            return this.$t('workplan.task_watchlist_close_text', {
                overdue: this.pendingOverdueCount,
                overdueTasks: this.taskLabel(this.pendingOverdueCount),
                stalled: this.pendingStalledCount,
                stalledTasks: this.taskLabel(this.pendingStalledCount)
            })
        },
        formattedPeriod() {
            const startDate = this.taskWatchlistCount?.start_date
            const endDate = this.taskWatchlistCount?.end_date

            if(!startDate || !endDate)
                return ''

            const locale = this.$i18n?.locale || 'ru'
            const start = this.$moment(startDate).locale(locale)
            const end = this.$moment(endDate).locale(locale)

            if(!start.isValid() || !end.isValid())
                return ''

            const startDay = start.format('DD')
            const startDayMonth = start.format('DD MMMM')
            const endDayMonth = end.format('DD MMMM')
            const startMonth = start.format('MMMM')
            const endMonth = end.format('MMMM')

            if(startMonth === endMonth)
                return `${startDay}-${endDayMonth}`

            return `${startDayMonth} - ${endDayMonth}`
        },
        drawerTitle() {
            if(!this.formattedPeriod)
                return this.$t('workplan.task_watchlist_title')

            return this.$t('workplan.task_watchlist_title_period', { period: this.formattedPeriod })
        }
    },
    watch: {
        visible(value) {
            if(value)
                this.initDrawer()
        },
        taskWatchlistCount: {
            handler(value) {
                this.syncTaskWatchlistCount(value)
            },
            immediate: true,
            deep: true
        },
        role() {
            this.reloadAll()
        }
    },
    data() {
        return {
            search: '',
            role: 'is_executor',
            closeConfirmVisible: false,
            skipCloseConfirm: false,
            sectionOpen: {
                overdue: true,
                stalled: true
            },
            taskWatchlistCountLocal: {
                overdue: 0,
                stalled: 0,
                roles: {}
            },
            overdueSection: createSection(),
            stalledSection: createSection()
        }
    },
    methods: {
        popupContainer() {
            return this.$refs.bodyRef || document.body
        },
        async initDrawer() {
            this.reloadAll()
        },
        syncTaskWatchlistCount(value) {
            this.taskWatchlistCountLocal = {
                overdue: Number(value?.overdue) || 0,
                stalled: Number(value?.stalled) || 0,
                roles: value?.roles || {}
            }
        },
        clearSearch() {
            this.search = ''
            clearTimeout(searchTimer)
            this.reloadAll()
        },
        forceCloseDrawer() {
            this.skipCloseConfirm = true
            this.closeConfirmVisible = false
            this.$emit('input', false)
            this.$nextTick(() => {
                this.skipCloseConfirm = false
            })
        },
        changeSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.reloadAll()
            }, 700)
        },
        toggleSection(section) {
            this.$set(this.sectionOpen, section, !this.sectionOpen[section])
        },
        resetSection(group) {
            this[`${group}Section`] = createSection()
        },
        async nextLoading(group) {
            this[`${group}Section`].page += 1
            await this.getTaskWatchlist(group)
        },
        handleTaskReload(taskId) {
            const hasOverdueTask = this.overdueSection.results.some(task => task.id === taskId)
            const hasStalledTask = this.stalledSection.results.some(task => task.id === taskId)

            this.overdueSection.results = this.overdueSection.results.filter(task => task.id !== taskId)
            this.stalledSection.results = this.stalledSection.results.filter(task => task.id !== taskId)

            if(!hasOverdueTask && !hasStalledTask)
                return

            this.$emit('reload-count')
            this.silentReloadAll()
        },
        silentReloadAll() {
            this.getTaskWatchlist('overdue', { silent: true })
            this.getTaskWatchlist('stalled', { silent: true })
        },
        reloadAll() {
            this.resetSection('overdue')
            this.resetSection('stalled')

            this.getTaskWatchlist('overdue')
            this.getTaskWatchlist('stalled')
        },
        roleBadgeStyle(type) {
            return {
                backgroundColor: type === 'overdue' ? '#fdd5d5' : '#fef8eb',
                color: type === 'overdue' ? '#FF5C5C' : '#FF9A01'
            }
        },
        taskLabel(count) {
            const mod10 = count % 10
            const mod100 = count % 100

            if(mod10 === 1 && mod100 !== 11)
                return this.$t('workplan.task_watchlist_task_one')
            if(mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14))
                return this.$t('workplan.task_watchlist_task_few')

            return this.$t('workplan.task_watchlist_task_many')
        },
        async getTaskWatchlist(group, { silent = false } = {}) {
            const section = this[`${group}Section`]

            try {
                if(!silent)
                    section.loading = true

                const loadedPages = Math.max(Number(section.page) || 1, 1)
                const params = {
                    group,
                    page: silent ? 1 : section.page,
                    page_size: silent ? loadedPages * 8 : 8
                }

                if(this.role !== null && this.role !== undefined && this.role !== '')
                    params.role = this.role
                if(this.search)
                    params.search = this.search

                const { data } = await axios.get('/tasks/task/task_watchlist/', { params })
                const results = Array.isArray(data?.results) ? data.results : []

                section.results = section.page === 1 || silent
                    ? results
                    : section.results.concat(results)
                section.next = !!data?.next
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                if(!silent)
                    section.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.task_watchlist_drawer_body {
    min-height: 240px;

    &::v-deep {
        .tab_search .ant-input{
            border: 0;
        }
        .tab_search.ant-input-affix-wrapper {
            border: 0;
            box-shadow: none;
        }

        .tab_search.ant-input-affix-wrapper:hover,
        .tab_search.ant-input-affix-wrapper:focus,
        .tab_search.ant-input-affix-wrapper-focused {
            border: 0;
            box-shadow: none;
        }
    }
}

.task_watchlist_drawer_header {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;

    &__icon {
        color: currentColor;
        font-size: 22px;
        line-height: 1;
    }

    &__title {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
}

.task_watchlist_drawer__load_more {
    margin-top: 12px;
}

.task_watchlist_drawer_role {
    display: flex;
    align-items: center;
    gap: 8px;

    &__title {
        font-size: 14px;
        font-weight: 400;
        white-space: nowrap;
        line-height: 1.2;
    }

    &__badges {
        display: inline-flex;
        align-items: center;
        &::v-deep{
            .task_watchlist_drawer_role__badge{
                margin-left: 5px;
            }
        }
    }

    &__badge {
        display: inline-flex;
        align-items: center;
    }
}

.task_block_item {
    &:not(:last-child) {
        margin-bottom: 15px;
    }
}

.task_watchlist_drawer_sections {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 20px;
}

.task_watchlist_confirm {
    &__title {
        font-size: 20px;
        font-weight: 700;
        line-height: 1.3;
        color: #d97706;
        margin-bottom: 18px;
        display: flex;
        align-items: center;

        i {
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
    }

    &__text {
        font-size: 16px;
        line-height: 1.65;
        color: #667085;
        margin-bottom: 24px;
    }

    &__actions {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
}

@media (min-width: 1280px) {
    .task_watchlist_drawer_sections {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        align-items: start;
    }
}

@media (min-width: 768px) {
    .task_watchlist_confirm {
        &__actions {
            flex-direction: row;

            .ant-btn {
                margin-top: 0 !important;
            }
        }
    }
}

@media (max-width: 767px) {
    .task_watchlist_drawer_sections {
        gap: 0;
    }

    .task_watchlist_confirm {
        &__title {
            font-size: 16px;
        }
    }
}

.task_block_title {
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;

    &__main {
        display: inline-flex;
        align-items: center;
    }

    &__arrow {
        color: #98a2b3;
        font-size: 18px;
        transition: transform .2s ease;

        &.collapsed {
            transform: rotate(180deg);
        }
    }

    &.overdue {
        color: #ff3b30;
    }

    &.stalled {
        color: #f08b00;
    }
}

.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity .15s ease, transform .15s ease
}

.fade-scale-enter,
.fade-scale-leave-to {
    opacity: 0;
    transform: scale(.55)
}

.watchlist-card-slide-enter-active,
.watchlist-card-slide-leave-active {
    transition: opacity .25s ease, transform .25s ease;
}

.watchlist-card-slide-leave-to {
    opacity: 0;
    transform: translateX(-32px);
}

.mob_scroll {
    display: -webkit-box;
    margin-bottom: 0;
    overflow-x: scroll;
    width: 100%;
    margin-left: -15px;
    margin-right: -15px;
    -ms-overflow-style: none;
}

.mob_scroll::-webkit-scrollbar {
    display: none;
}

.task_watchlist_drawer_role_wrap {
    padding-left: 15px;
    padding-right: 15px;
}

@media (max-width: 767px) {
    .mob_scroll {
        margin-bottom: 6px !important;
    }
}
</style>
