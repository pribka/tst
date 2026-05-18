<template>
    <ModuleWrapper :page-title="pageTitle" :body-padding="false" :body-o-hidden="true">
        <template #h_left>
            <div class="planner_toolbar__teams planner_toolbar__teams--header">
                <div
                    class="planner_toolbar__teams_scroll_wrap"
                    @mouseenter="onTeamsWrapperEnter"
                    @mouseleave="onTeamsWrapperLeave">
                    <a-button
                        v-if="showTeamsLeftArrow"
                        class="planner_teams_scroll_arrow planner_teams_scroll_arrow--left"
                        shape="circle"
                        size="small"
                        type="flat_primary"
                        flaticon
                        icon="fi-rr-angle-small-left"
                        @mouseenter="startTeamsHoverScroll('left')"
                        @mouseleave="stopTeamsHoverScroll" />
                    <a-button
                        v-if="showTeamsRightArrow"
                        class="planner_teams_scroll_arrow planner_teams_scroll_arrow--right"
                        shape="circle"
                        size="small"
                        type="flat_primary"
                        flaticon
                        icon="fi-rr-angle-small-right"
                        @mouseenter="startTeamsHoverScroll('right')"
                        @mouseleave="stopTeamsHoverScroll" />
                    <div ref="plannerTeamsScroll" class="planner_toolbar__teams_scroll" @scroll="onTeamsScroll">
                    <div class="planner_toolbar__teams_list">
                        <div
                            v-for="team in teams"
                            :key="team.id"
                            :ref="`plannerTeam_${team.id}`"
                            class="planner_team_item">
                            <div class="planner_team_item__tools">
                                <button
                                    type="button"
                                    class="planner_team_item__tool"
                                    title="Редактировать команду"
                                    @click="openEditTeam(team)">
                                    <i class="fi fi-rr-pencil"></i>
                                </button>
                                <button
                                    type="button"
                                    class="planner_team_item__tool is-danger"
                                    title="Удалить команду"
                                    @click="removeTeam(team.id)">
                                    <i class="fi fi-rr-trash"></i>
                                </button>
                            </div>
                            <div class="planner_team_chip" :class="{ 'is-active': isTeamActive(team.id) }">
                                <a-checkbox
                                    class="planner_team_chip__check"
                                    :checked="isTeamActive(team.id)"
                                    @click.stop
                                    @change="toggleTeamCheckbox(team.id, $event.target.checked)" />
                                <button
                                    type="button"
                                    class="planner_team_chip__main"
                                    :title="team.name + ' / ' + ((team.users || []).length)"
                                    @click="selectOnlyTeam(team.id)">
                                    <span class="planner_team_chip__name">{{ team.name }}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>
                <a-tooltip placement="bottom">
                    <template slot="title">
                        <span>Создать команду</span>
                    </template>
                    <a-button
                        class="planner_team_add planner_team_add--header"
                        type="flat_primary"
                        shape="circle"
                        icon="fi-rr-plus"
                        flaticon
                        @click="openCreateTeam" />
                </a-tooltip>
            </div>
        </template>

        <template #h_right>
            <div class="planner_header_controls flex items-center gap-2">
                <DatePicker v-model="selectedDate" size="large" date-format="DD.MM.YYYY" :show-time="false" />
                <div class="planner_toolbar__slot_size planner_toolbar__slot_size--header">
                    <span class="planner_toolbar__label">{{ $t('planner.time_scale') }}</span>
                    <Segmented
                        :value="viewMode"
                        :options="viewModeOptions"
                        @change="handleViewModeChange" />
                </div>
            </div>
        </template>

        <div class="planner_page">
            <a-spin :spinning="isInitialLoading">
                <div class="planner_layout">
                    <aside class="planner_queue">
                        <div class="planner_queue__header">
                            <div>
                                <div class="planner_section_title">{{ $t('planner.queue') }}</div>
                                <div class="planner_queue__hint">{{ $t('planner.queue_hint') }}</div>
                            </div>
                            <div class="planner_queue__count">{{ queueItems.length }}</div>
                        </div>

                        <div class="planner_queue__scroll">
                            <div v-if="queueItems.length" class="planner_queue__list">
                                <div
                                    v-for="item in queueItems"
                                    :key="item.uid"
                                    class="planner_queue_card"
                                    :style="queueCardStyle(item)"
                                    @mousedown.left="beginCardPointerDrag(item, null, $event)"
                                    @click="openItem(item)">
                                    <span class="planner_queue_card__type">{{ getItemTypeLabel(item) }}</span>
                                    <strong class="planner_queue_card__title">{{ item.name }}</strong>
                                    <div class="planner_queue_card__meta">
                                        <span class="planner_queue_card__time">{{ formatItemWindow(item) }}</span>
                                        <div v-if="getCardUsers(item).length" class="planner_queue_card__users">
                                            <a-avatar
                                                v-for="user in getCardUsers(item)"
                                                :key="`${item.uid}-${user.id}`"
                                                :src="user.avatar && user.avatar.path ? user.avatar.path : null"
                                                icon="user"
                                                size="small" />
                                        </div>
                                    </div>
                                    <span v-if="getCardSecondary(item)" class="planner_queue_card__secondary">
                                        {{ getCardSecondary(item) }}
                                    </span>
                                    <button
                                        type="button"
                                        class="planner_card_inline_action"
                                        :title="$t('planner.transfer_card')"
                                        @click.stop="openTransfer(item, item.primaryPerformerId)">
                                        <i class="fi fi-rr-arrows-repeat"></i>
                                    </button>
                                </div>
                            </div>

                            <div v-else class="planner_empty">{{ $t('planner.empty_queue') }}</div>
                        </div>
                    </aside>

                    <section class="planner_board">
                        <button
                            v-show="leftActive"
                            type="button"
                            class="arrow_left arrow"
                            @mouseenter="scrollLeft"
                            @mouseleave="clear">
                            <i class="fi fi-rr-angle-small-left"></i>
                        </button>
                        <button
                            v-show="rightActive"
                            type="button"
                            class="arrow_right arrow"
                            @mouseenter="scrollRight"
                            @mouseleave="clear">
                            <i class="fi fi-rr-angle-small-right"></i>
                        </button>
                        <div
                            ref="plannerBoardScroll"
                            class="planner_board__scroll"
                            v-scroll="handleScroll">
                            <div v-if="!performers.length" class="planner_empty planner_board__empty">
                                {{ $t('planner.no_performers') }}
                            </div>

                            <div v-else-if="requiresSinglePerformer && performers.length !== 1" class="planner_empty planner_board__empty">
                                {{ $t('planner.fortnight_single_user') }}
                            </div>

                        <template v-else-if="isTimedView">
                            <div class="planner_day_board">
                                <div class="planner_day_columns">
                                    <div
                                        v-for="performer in performers"
                                        :key="performer.id"
                                        class="planner_day_column"
                                        :class="{ 'is-collapsed': isPerformerCollapsed(performer.id) }">
                                        <div class="planner_day_column__header">
                                            <div class="planner_day_column__identity">
                                                <span class="planner_day_column__counter">{{ performerScheduledCount[performer.id] || 0 }}</span>
                                                <a-avatar :src="performer.avatar && performer.avatar.path ? performer.avatar.path : null" icon="user" size="small" />
                                                <span class="planner_day_column__name">{{ performer.full_name || performer.name }}</span>
                                            </div>
                                            <a-button
                                                ghost
                                                type="ui"
                                                size="small"
                                                flaticon
                                                class="planner_day_column__toggle"
                                                icon="fi-rr-caret-square-left_1"
                                                @click="togglePerformerCollapse(performer.id)" />
                                        </div>

                                        <div
                                            class="planner_day_column__body"
                                            :class="{ 'is-collapsed': isPerformerCollapsed(performer.id) }"
                                            @scroll.passive="handleTimedColumnScroll(performer, $event)">
                                            <div class="planner_day_column__canvas">
                                                <div
                                                    v-for="day in timedDays[performer.id] || []"
                                                    :key="`${performer.id}-${day.key}`"
                                                    class="planner_day_column__day">
                                                    <div class="planner_day_column__day_head">
                                                        <strong>{{ day.date.format('DD.MM.YYYY') }}</strong>
                                                        <span>{{ day.date.format('dddd') }}</span>
                                                    </div>

                                                    <div
                                                        class="planner_day_column__day_grid"
                                                        :data-performer-id="performer.id"
                                                        :data-day-key="day.key"
                                                        :data-day-date="day.date.toISOString()"
                                                        :style="dayBoardStyle">
                                                        <button
                                                            v-for="slot in slotButtons"
                                                            :key="`${performer.id}-${day.key}-${slot.key}`"
                                                            class="planner_day_column__slot"
                                                            :class="{ 'is-occupied': getDaySlotOccupancy(performer.id, day.key, slot) > 0 }"
                                                            :style="{ top: `${slot.top}px`, height: `${slot.height}px` }"
                                                            @click="openSlotPicker(performer, slot.minute, day.date, timedSlotMinutes)">
                                                            <span class="planner_day_column__slot_time">{{ slot.label }}</span>
                                                        </button>

                                                        <div
                                                            v-if="isTimedDropPreviewVisible(performer.id, day.key)"
                                                            class="planner_drop_preview planner_drop_preview--timed"
                                                            :style="timedDropPreviewStyle"></div>

                                                        <template v-if="!isPerformerCollapsed(performer.id)">
                                                            <div
                                                                v-for="layout in day.layouts"
                                                                :key="`${performer.id}-${day.key}-${layout.item.uid}`"
                                                                class="planner_board_card"
                                                                :style="boardCardStyle(layout)"
                                                                @mousedown.left="beginCardPointerDrag(layout.item, performer.id, $event)"
                                                                @click="openItem(layout.item)">
                                                                <span class="planner_board_card__type">{{ getItemTypeLabel(layout.item) }}</span>
                                                                <strong class="planner_board_card__title">{{ layout.item.name }}</strong>
                                                                <div class="planner_board_card__meta">
                                                                    <span class="planner_board_card__time">{{ formatItemWindow(layout.item) }}</span>
                                                                    <div v-if="getCardUsers(layout.item).length" class="planner_board_card__users">
                                                                        <a-avatar
                                                                            v-for="user in getCardUsers(layout.item)"
                                                                            :key="`${layout.item.uid}-${user.id}`"
                                                                            :src="user.avatar && user.avatar.path ? user.avatar.path : null"
                                                                            icon="user"
                                                                            size="small" />
                                                                    </div>
                                                                </div>
                                                                <span v-if="getCardSecondary(layout.item)" class="planner_board_card__secondary">
                                                                    {{ getCardSecondary(layout.item) }}
                                                                </span>
                                                                <button
                                                                    type="button"
                                                                    class="planner_card_inline_action"
                                                                    :title="$t('planner.transfer_card')"
                                                                    @click.stop="openTransfer(layout.item, performer.id)">
                                                                    <i class="fi fi-rr-arrows-repeat"></i>
                                                                </button>
                                                                <span
                                                                    class="planner_board_card__resize"
                                                                    @mousedown.stop="startResize(layout.item, performer.id, $event)"
                                                                    @click.stop></span>
                                                            </div>
                                                        </template>
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="isTimedColumnLoading(performer.id)" class="planner_day_column__loading">
                                                <a-spin size="small" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>

                        <template v-else>
                            <div class="planner_overview">
                                <div
                                    v-for="performer in overviewPerformers"
                                    :key="performer.id"
                                    class="planner_overview__column"
                                    :class="{ 'is-collapsed': isPerformerCollapsed(performer.id) }">
                                    <div v-if="showOverviewHeaders" class="planner_overview__header">
                                        <div class="planner_day_column__identity">
                                            <span class="planner_day_column__counter">{{ performerScheduledCount[performer.id] || 0 }}</span>
                                            <a-avatar :src="performer.avatar && performer.avatar.path ? performer.avatar.path : null" icon="user" size="small" />
                                            <span class="planner_day_column__name">{{ performer.full_name || performer.name }}</span>
                                        </div>
                                        <a-button
                                            ghost
                                            type="ui"
                                            size="small"
                                            flaticon
                                            class="planner_day_column__toggle"
                                            icon="fi-rr-caret-square-left_1"
                                            @click="togglePerformerCollapse(performer.id)" />
                                    </div>

                                    <div
                                        v-if="!isPerformerCollapsed(performer.id)"
                                        class="planner_overview__days"
                                        :style="overviewGridStyle"
                                        @scroll.passive="handleOverviewDaysScroll(performer, $event)">
                                        <div
                                            v-for="day in overviewDays[performer.id] || []"
                                            :key="`${performer.id}-${day.key}`"
                                            class="planner_overview__day"
                                            :data-performer-id="performer.id"
                                            :data-day-key="day.key"
                                            :data-day-date="day.date.toISOString()">
                                            <button class="planner_overview__head" @click="openSlotPicker(performer, 9 * 60, day.date)">
                                                <span>{{ day.date.format('DD.MM') }}</span>
                                                <small>{{ day.date.format('ddd') }}</small>
                                            </button>

                                            <div v-if="isOverviewDropPreviewVisible(performer.id, day.key)" class="planner_drop_preview planner_drop_preview--overview">
                                                <span class="planner_drop_preview__time">
                                                    {{ formatTransferSlot(dropPreview.start, dropPreview.end) }}
                                                </span>
                                            </div>

                                            <div v-if="day.items.length" class="planner_overview__cards">
                                                <div
                                                    v-for="item in day.items"
                                                    :key="`${day.key}-${item.uid}`"
                                                    class="planner_fortnight__card"
                                                    :style="queueCardStyle(item)"
                                                    @mousedown.left="beginCardPointerDrag(item, performer.id, $event)"
                                                    @click="openItem(item)">
                                                    <span class="planner_queue_card__type">{{ getItemTypeLabel(item) }}</span>
                                                    <strong class="planner_queue_card__title">{{ item.name }}</strong>
                                                    <div class="planner_queue_card__meta">
                                                        <span class="planner_queue_card__time">{{ formatItemWindow(item) }}</span>
                                                        <div v-if="getCardUsers(item).length" class="planner_queue_card__users">
                                                            <a-avatar
                                                                v-for="user in getCardUsers(item)"
                                                                :key="`${item.uid}-${user.id}`"
                                                                :src="user.avatar && user.avatar.path ? user.avatar.path : null"
                                                                icon="user"
                                                                size="small" />
                                                        </div>
                                                    </div>
                                                    <span v-if="getCardSecondary(item)" class="planner_queue_card__secondary">
                                                        {{ getCardSecondary(item) }}
                                                    </span>
                                                    <button
                                                        type="button"
                                                        class="planner_card_inline_action"
                                                        :title="$t('planner.transfer_card')"
                                                        @click.stop="openTransfer(item, performer.id)">
                                                        <i class="fi fi-rr-arrows-repeat"></i>
                                                    </button>
                                                </div>
                                            </div>
                                            <div v-else class="planner_overview__empty">{{ $t('planner.drop_here') }}</div>
                                        </div>
                                        <div v-if="isOverviewColumnLoading(performer.id)" class="planner_overview__loading">
                                            <a-spin size="small" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                    </section>
                </div>
            </a-spin>

            <a-modal :visible="slotPicker.visible" :width="380" :footer="null" :title="$t('planner.slot_picker_title')" @cancel="closeSlotPicker">
                <div class="planner_slot_picker pt-4">
                    <a-button type="primary" block size="large" @click="createFromSlot('task')">{{ $t('planner.create_task') }}</a-button>
                    <a-button block size="large" @click="createFromSlot('request')">{{ $t('planner.create_request') }}</a-button>
                    <a-button block size="large" @click="createFromSlot('event')">{{ $t('planner.create_event') }}</a-button>
                </div>
            </a-modal>

            <a-modal
                :visible="teamEditor.visible"
                :title="teamEditor.id ? 'Редактировать команду' : 'Новая команда'"
                @cancel="closeTeamEditor">
                <div class="planner_team_editor">
                    <a-input
                        ref="teamNameInput"
                        v-model="teamEditor.name"
                        size="large"
                        placeholder="Название команды" />

                    <UserDrawer
                        id="plannerTeamUsersDrawer"
                        v-model="teamEditor.users"
                        multiple
                        buttonIcon="fi-rr-user-add"
                        buttonText="Исполнители"
                        title="Исполнители" />

                </div>
                <template #footer>
                    <div class="flex items-center justify-end gap-2 w-full">
                        <a-button type="primary" @click="saveTeam">Сохранить</a-button>
                        <a-button type="ui_ghost" @click="closeTeamEditor">Отмена</a-button>
                    </div>
                </template>
            </a-modal>

            <a-modal
                :visible="transferState.visible"
                :confirm-loading="transferState.loading"
                :title="$t('planner.transfer_title')"
                :width="1180"
                @cancel="closeTransfer">
                <div class="planner_transfer">
                    <div class="planner_transfer__hint">
                        {{ $t('planner.transfer_hint') }}
                    </div>

                    <div v-if="transferState.start && transferState.end" class="planner_transfer__selected">
                        {{ $t('planner.transfer_selected') }}: {{ transferSelectionLabel }}
                    </div>

                    <div v-if="transferState.slotsLoading" class="planner_transfer__loading">
                        <a-spin size="small" />
                        <span>{{ $t('planner.transfer_slots_loading') }}</span>
                    </div>

                    <div
                        ref="transferSchedule"
                        class="planner_transfer__schedule"
                        @scroll.passive="handleTransferScheduleScroll">
                        <div class="planner_transfer__head" :style="transferScheduleGridStyle">
                            <div
                                v-for="performer in performers"
                                :key="`transfer-head-${performer.id}`"
                                class="planner_transfer__performer">
                                {{ performer.full_name || performer.name }}
                            </div>
                        </div>

                        <div v-for="day in transferState.scheduleDays" :key="day.key" class="planner_transfer_daygroup">
                            <div class="planner_transfer_daygroup__head">
                                <strong>{{ day.date.format('DD.MM.YYYY') }}</strong>
                                <span>{{ day.date.format('dddd') }}</span>
                            </div>

                            <div v-for="slot in day.slots" :key="slot.key" class="planner_transfer_row" :style="transferScheduleGridStyle">
                                <button
                                    v-for="cell in slot.cells"
                                    :key="cell.key"
                                    type="button"
                                    class="planner_transfer_cell"
                                    :class="getTransferCellClass(cell)"
                                    :style="getTransferCellStyle(cell)"
                                    :title="getTransferCellTitle(cell, slot)"
                                    @click="selectTransferSlot(cell)">
                                    <a-checkbox
                                        class="planner_transfer_cell__checkbox"
                                        :checked="isTransferCellSelected(cell)" />
                                    <span class="planner_transfer_cell__body">
                                        <span class="planner_transfer_cell__time">{{ slot.label }}</span>
                                        <span v-if="cell.items.length" class="planner_transfer_cell__busy_names">
                                            {{ getTransferCellBusyLabel(cell) }}
                                        </span>
                                    </span>
                                    <span v-if="cell.items.length" class="planner_transfer_cell__count">{{ cell.items.length }}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <template #footer>
                    <div class="flex items-center justify-end gap-2 w-full">
                        <a-button type="primary" :loading="transferState.loading" @click="submitTransfer">
                            {{ $t('planner.transfer_submit') }}
                        </a-button>
                        <a-button type="ui_ghost" @click="closeTransfer">Закрыть</a-button>
                    </div>
                </template>
            </a-modal>
        </div>
    </ModuleWrapper>
</template>

<script>
import moment from 'moment'
import { vScroll } from '@vueuse/components'
import { useScroll } from '@vueuse/core'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { dateFormat } from '@apps/WorkPlan/utils.js'
import {
    SLOT_MINUTES,
    PIXELS_PER_MINUTE,
    DEFAULT_DAY_START,
    DEFAULT_DAY_END,
    buildDayLayouts,
    buildPlannerItems,
    buildRangeDays,
    clamp,
    formatClockLabel,
    getDefaultDurationMinutes
} from './utils'

const PLANNER_LEGACY_USERS_STORAGE_KEY = 'planner_selected_users'
const PLANNER_TEAMS_STORAGE_KEY = 'planner_user_teams'
const PLANNER_ACTIVE_TEAMS_STORAGE_KEY = 'planner_active_team_ids'
const PLANNER_COLLAPSED_PERFORMERS_STORAGE_KEY = 'planner_collapsed_performer_ids'
const TRANSFER_LOOKAHEAD_DAYS = 14
const TRANSFER_LOOKAHEAD_CHUNK = 7
const TRANSFER_PAGE_SIZE = 1000
const TIMED_DAYS_CHUNK = 3

const createTeamEditorState = () => ({
    visible: false,
    id: null,
    name: '',
    users: []
})

const createTransferState = () => ({
    visible: false,
    loading: false,
    slotsLoading: false,
    item: null,
    entityType: null,
    performer: null,
    start: null,
    end: null,
    durationMinutes: 60,
    replacePerformerId: null,
    selectedCells: [],
    daysVisible: TRANSFER_LOOKAHEAD_DAYS,
    scheduleDays: []
})

export default {
    name: 'PlannerPage',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        DatePicker: () => import('@apps/Datepicker'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    directives: {
        scroll: vScroll
    },
    data() {
        return {
            viewMode: 'hour',
            selectedDate: moment().startOf('day'),
            teams: [],
            activeTeamIds: [],
            collapsedPerformerIds: [],
            plannerBaseItems: [],
            plannerLoading: false,
            plannerLoadToken: 0,
            plannerViewToken: 0,
            timedDaysVisibleByPerformer: {},
            overviewDaysVisibleByPerformer: {},
            timedColumnLoading: {},
            overviewColumnLoading: {},
            columnExtraItemsByPerformer: {},
            dragState: null,
            dropPreview: null,
            pointerDragState: null,
            suppressCardClick: false,
            resizeState: null,
            resizeMoveHandler: null,
            resizeUpHandler: null,
            booting: true,
            teamEditor: createTeamEditorState(),
            slotPicker: { visible: false, performer: null, start: null, end: null },
            transferState: createTransferState(),
            leftActive: true,
            rightActive: true,
            timer: null,
            dragPreviewEl: null,
            dragPreviewOffsetX: 18,
            dragPreviewOffsetY: 18,
            isTeamsListHover: false,
            canScrollTeamsLeft: false,
            canScrollTeamsRight: false,
            teamsHoverScrollTimer: null,
            teamsHoverScrollDir: null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        currentUser() {
            const user = this.$store.state.user?.user || {}
            const fullName = user.full_name || [user.last_name, user.first_name].filter(Boolean).join(' ')

            if (!user.id)
                return null

            return { id: user.id, full_name: fullName || 'User', avatar: user.avatar || null }
        },
        selectedUsers() {
            const selectedTeams = this.teams.filter(team => this.activeTeamIds.includes(String(team.id)))
            const byId = new Map()

            selectedTeams.forEach(team => {
                ;(team.users || []).forEach(user => {
                    if (user?.id)
                        byId.set(String(user.id), user)
                })
            })

            return Array.from(byId.values())
        },
        performers() {
            return this.selectedUsers
        },
        selectedSinglePerformer() {
            return this.performers.length === 1 ? this.performers[0] : null
        },
        isTimedView() {
            return ['half_hour', 'hour', 'two_hours'].includes(this.viewMode)
        },
        requiresSinglePerformer() {
            return this.viewMode === 'fortnight'
        },
        timedSlotMinutes() {
            if (this.viewMode === 'half_hour')
                return 30
            return this.viewMode === 'two_hours' ? 120 : 60
        },
        transferSlotMinutes() {
            if (this.viewMode === 'half_hour')
                return 30
            if (this.viewMode === 'two_hours')
                return 120

            return 60
        },
        overviewLength() {
            if (this.viewMode === 'week')
                return 7
            if (this.viewMode === 'fortnight')
                return 14
            return 1
        },
        visibleRangeLength() {
            if (this.isTimedView)
                return this.performers.reduce((maxValue, performer) => Math.max(maxValue, this.getTimedVisibleLength(performer.id)), 1)

            return this.overviewPerformers.reduce((maxValue, performer) => Math.max(maxValue, this.getOverviewVisibleLength(performer.id)), this.overviewLength)
        },
        rangeStart() {
            return moment(this.selectedDate).startOf('day')
        },
        baseRangeEnd() {
            const baseLength = this.isTimedView ? 1 : this.overviewLength
            return this.rangeStart.clone().add(baseLength - 1, 'days').endOf('day')
        },
        rangeEnd() {
            return this.rangeStart.clone().add(this.visibleRangeLength - 1, 'days').endOf('day')
        },
        activeRangeLabel() {
            if (this.visibleRangeLength > 1)
                return `${this.rangeStart.format('DD.MM.YYYY')} - ${this.rangeEnd.format('DD.MM.YYYY')}`
            return this.rangeStart.format('DD.MM.YYYY')
        },
        hasPlannerData() {
            return this.plannerItems.length > 0
        },
        isInitialLoading() {
            return this.plannerLoading && !this.hasPlannerData
        },
        extraPlannerItems() {
            return Object.values(this.columnExtraItemsByPerformer || {}).reduce((acc, items) => acc.concat(items || []), [])
        },
        plannerItems() {
            return this.mergePlannerItemCollections([this.plannerBaseItems, this.extraPlannerItems])
        },
        queueItems() {
            return this.plannerItems
                .filter(item => !item.isScheduled)
                .filter(item => !item.hasRange || item.overlapsRange || item.allDay)
                .sort((a, b) => a.name.localeCompare(b.name))
        },
        scheduledItems() {
            return this.plannerItems.filter(item => item.isScheduled)
        },
        performerScheduledCount() {
            return this.performers.reduce((acc, performer) => {
                acc[performer.id] = this.scheduledItems.filter(item => this.itemHasPerformer(item, performer.id)).length
                return acc
            }, {})
        },
        timedSlotOccupancy() {
            return this.performers.reduce((acc, performer) => {
                acc[performer.id] = this.timedDays[performer.id]?.reduce((dayMap, day) => {
                    dayMap[day.key] = this.slotButtons.reduce((slotMap, slot) => {
                        const start = moment(day.date).startOf('day').add(slot.minute, 'minutes')
                        const end = start.clone().add(this.timedSlotMinutes, 'minutes')
                        slotMap[slot.key] = this.scheduledItems.filter(item =>
                            this.itemHasPerformer(item, performer.id)
                            && item.startAt
                            && item.endAt
                            && item.startAt.isBefore(end)
                            && item.endAt.isAfter(start)
                        ).length
                        return slotMap
                    }, {})
                    return dayMap
                }, {}) || {}
                return acc
            }, {})
        },
        timedDays() {
            if (!this.isTimedView)
                return {}

            return this.performers.reduce((acc, performer) => {
                acc[performer.id] = Array.from({ length: this.getTimedVisibleLength(performer.id) }).map((_, index) => {
                    const dayStart = this.rangeStart.clone().add(index, 'days').add(DEFAULT_DAY_START, 'minutes')
                    const dayEnd = this.rangeStart.clone().add(index, 'days').add(DEFAULT_DAY_END, 'minutes')

                    return {
                        key: dayStart.format('YYYY-MM-DD'),
                        date: dayStart.clone().startOf('day'),
                        layouts: buildDayLayouts(this.scheduledItems, performer.id, dayStart, dayEnd)
                    }
                })
                return acc
            }, {})
        },
        slotButtons() {
            const buttons = []

            for (let minute = DEFAULT_DAY_START; minute < DEFAULT_DAY_END; minute += this.timedSlotMinutes) {
                buttons.push({
                    key: minute,
                    minute,
                    label: `${formatClockLabel(minute)} - ${formatClockLabel(minute + this.timedSlotMinutes)}`,
                    top: (minute - DEFAULT_DAY_START) * PIXELS_PER_MINUTE,
                    height: this.timedSlotMinutes * PIXELS_PER_MINUTE
                })
            }

            return buttons
        },
        dayBoardStyle() {
            return {
                '--planner-day-height': `${(DEFAULT_DAY_END - DEFAULT_DAY_START) * PIXELS_PER_MINUTE}px`
            }
        },
        timedDropPreviewStyle() {
            if (!this.dropPreview?.start || !this.dropPreview?.end)
                return {}

            const startMinute = this.dropPreview.start.diff(this.dropPreview.start.clone().startOf('day'), 'minutes')
            const endMinute = this.dropPreview.end.diff(this.dropPreview.end.clone().startOf('day'), 'minutes')

            return {
                top: `${startMinute * PIXELS_PER_MINUTE}px`,
                height: `${Math.max((endMinute - startMinute) * PIXELS_PER_MINUTE, 34)}px`
            }
        },
        overviewPerformers() {
            if (this.viewMode === 'fortnight')
                return this.selectedSinglePerformer ? [this.selectedSinglePerformer] : []
            return this.performers
        },
        overviewDays() {
            return this.overviewPerformers.reduce((acc, performer) => {
                acc[performer.id] = buildRangeDays(this.scheduledItems, performer.id, this.selectedDate, this.getOverviewVisibleLength(performer.id))
                return acc
            }, {})
        },
        showOverviewHeaders() {
            return this.viewMode !== 'fortnight' || this.performers.length > 1
        },
        overviewGridStyle() {
            const columns = this.visibleRangeLength > 1 && this.overviewPerformers.length === 1 ? 7 : 1

            return {
                gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`
            }
        },
        transferSelectionLabel() {
            if (!this.transferState.start || !this.transferState.end || !this.transferState.performer)
                return ''

            const performerName = this.transferState.performer.full_name || this.transferState.performer.name || ''
            return `${performerName}: ${this.formatTransferSlot(this.transferState.start, this.transferState.end)}`
        },
        transferScheduleGridStyle() {
            return {
                gridTemplateColumns: `repeat(${this.performers.length}, minmax(104px, 1fr))`
            }
        },
        viewModeOptions() {
            return [
                {
                    key: 'half_hour',
                    title: '30 мин'
                },
                {
                    key: 'hour',
                    title: this.$t('planner.scale_hour')
                },
                {
                    key: 'two_hours',
                    title: this.$t('planner.scale_two_hours')
                }
            ]
        },
        pageTitle() {
            return this.$route?.meta?.title || this.$t('planner.toolbar_title')
        },
        showTeamsLeftArrow() {
            return !this.isMobile && this.isTeamsListHover && this.canScrollTeamsLeft
        },
        showTeamsRightArrow() {
            return !this.isMobile && this.isTeamsListHover && this.canScrollTeamsRight
        }
    },
    watch: {
        selectedDate() {
            if (!this.booting) {
                this.resetPlannerViewState()
                this.reloadPlanner()
            }
        },
        viewMode() {
            if (!this.booting) {
                this.resetPlannerViewState()
                this.reloadPlanner()
            }
        },
        teams() {
            this.$nextTick(() => this.updateTeamsArrows())
        },
        isMobile() {
            this.$nextTick(() => this.updateTeamsArrows())
        },
        performers() {
            this.$nextTick(() => this.updateBoardArrows())
        },
        plannerItems() {
            this.$nextTick(() => this.updateBoardArrows())
        }
    },
    async created() {
        eventBus.$on('TASK_CREATED_task_planner', this.handlePlannerTaskCreated)
        eventBus.$on('add_event_planner', this.handlePlannerEventCreated)
        eventBus.$on('PLANNER_TICKET_CREATED', this.handlePlannerTicketCreated)

        this.teams = this.restoreTeams()
        this.activeTeamIds = this.restoreActiveTeamIds(this.teams)

        this.collapsedPerformerIds = this.restoreCollapsedPerformers()
        this.resetPlannerViewState()
        await this.reloadPlanner()
        this.booting = false
    },
    mounted() {
        window.addEventListener('mousemove', this.handlePointerDragMove)
        window.addEventListener('mouseup', this.handlePointerDragEnd)
        window.addEventListener('resize', this.updateTeamsArrows)
        window.addEventListener('resize', this.updateBoardArrows)
        this.$nextTick(() => {
            if (this.activeTeamIds[0])
                this.scrollTeamIntoView(this.activeTeamIds[0], 'auto')
            this.updateTeamsArrows()
            this.updateBoardArrows()
        })
    },
    beforeDestroy() {
        eventBus.$off('TASK_CREATED_task_planner', this.handlePlannerTaskCreated)
        eventBus.$off('add_event_planner', this.handlePlannerEventCreated)
        eventBus.$off('PLANNER_TICKET_CREATED', this.handlePlannerTicketCreated)
        window.removeEventListener('mousemove', this.handlePointerDragMove)
        window.removeEventListener('mouseup', this.handlePointerDragEnd)
        window.removeEventListener('resize', this.updateTeamsArrows)
        window.removeEventListener('resize', this.updateBoardArrows)
        this.stopTeamsHoverScroll()
        document.body.classList.remove('planner-dragging')
        this.destroyDragPreviewElement()
        this.clear()
        this.detachResizeListeners()
    },
    methods: {
        getTeamsScrollEl() {
            return this.$refs.plannerTeamsScroll
        },
        beginCardPointerDrag(item, performerId = null, event) {
            if (event.button !== 0)
                return

            if (event.target?.closest('.planner_card_inline_action, .planner_board_card__resize'))
                return

            event.preventDefault()

            this.pointerDragState = {
                item,
                performerId,
                sourceEl: event.currentTarget,
                startX: event.clientX,
                startY: event.clientY,
                dragging: false
            }
        },
        handlePointerDragMove(event) {
            if (!this.pointerDragState)
                return

            const deltaX = event.clientX - this.pointerDragState.startX
            const deltaY = event.clientY - this.pointerDragState.startY
            const distance = Math.hypot(deltaX, deltaY)

            if (!this.pointerDragState.dragging) {
                if (distance < 5)
                    return

                this.pointerDragState.dragging = true
                this.dragState = {
                    item: this.pointerDragState.item,
                    performerId: this.pointerDragState.performerId
                }
                this.suppressCardClick = true
                document.body.classList.add('planner-dragging')
                this.destroyDragPreviewElement()
                this.dragPreviewEl = this.createDragPreviewElement(this.pointerDragState.sourceEl)
            }

            this.positionDragPreview(event.clientX, event.clientY)
            this.updateDropPreviewFromPoint(event.clientX, event.clientY)
        },
        async handlePointerDragEnd(event) {
            if (!this.pointerDragState)
                return

            const dragSession = this.pointerDragState
            this.pointerDragState = null

            if (!dragSession.dragging)
                return

            const dropTarget = this.resolveDropTargetFromPoint(event.clientX, event.clientY)

            if (!dropTarget || !this.dragState?.item) {
                this.clearDrag()
                return
            }

            const performer = this.performers.find(user => String(user.id) === String(dropTarget.performerId))
            if (!performer) {
                this.clearDrag()
                return
            }

            const dragPayload = {
                item: this.dragState.item,
                replacePerformerId: this.dragState.performerId
            }

            this.clearDrag()

            if (dropTarget.mode === 'timed') {
                const start = this.resolveDayDropStartFromTarget(dropTarget.dayDate, dropTarget.el, event.clientY)
                const end = start.clone().add(getDefaultDurationMinutes(dragPayload.item), 'minutes')

                await this.applyTransfer({
                    item: dragPayload.item,
                    performer,
                    start,
                    end,
                    replacePerformerId: dragPayload.replacePerformerId
                })
            } else {
                const start = moment(dropTarget.dayDate)
                    .startOf('day')
                    .hour(DEFAULT_DAY_START / 60)
                    .minute(DEFAULT_DAY_START % 60)
                    .second(0)
                    .millisecond(0)
                const end = start.clone().add(getDefaultDurationMinutes(dragPayload.item), 'minutes')

                await this.applyTransfer({
                    item: dragPayload.item,
                    performer,
                    start,
                    end,
                    replacePerformerId: dragPayload.replacePerformerId
                })
            }
        },
        resolveDropTargetFromPoint(clientX, clientY) {
            const elements = typeof document.elementsFromPoint === 'function'
                ? document.elementsFromPoint(clientX, clientY)
                : [document.elementFromPoint(clientX, clientY)].filter(Boolean)

            for (const element of elements) {
                const timed = element?.closest?.('.planner_day_column__day_grid')
                if (timed) {
                    return {
                        mode: 'timed',
                        el: timed,
                        performerId: timed.dataset.performerId,
                        dayKey: timed.dataset.dayKey,
                        dayDate: timed.dataset.dayDate
                    }
                }

                const overview = element?.closest?.('.planner_overview__day')
                if (overview) {
                    return {
                        mode: 'overview',
                        el: overview,
                        performerId: overview.dataset.performerId,
                        dayKey: overview.dataset.dayKey,
                        dayDate: overview.dataset.dayDate
                    }
                }
            }

            return null
        },
        updateDropPreviewFromPoint(clientX, clientY) {
            if (!this.dragState?.item) {
                this.clearDropPreview()
                return
            }

            const target = this.resolveDropTargetFromPoint(clientX, clientY)
            if (!target) {
                this.clearDropPreview()
                return
            }

            if (target.mode === 'timed') {
                const start = this.resolveDayDropStartFromTarget(target.dayDate, target.el, clientY)
                const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

                this.setDropPreview({
                    mode: 'timed',
                    performerId: target.performerId,
                    dayKey: target.dayKey,
                    start,
                    end
                })
                return
            }

            const start = moment(target.dayDate)
                .startOf('day')
                .hour(DEFAULT_DAY_START / 60)
                .minute(DEFAULT_DAY_START % 60)
                .second(0)
                .millisecond(0)
            const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

            this.setDropPreview({
                mode: 'overview',
                performerId: target.performerId,
                dayKey: target.dayKey,
                start,
                end
            })
        },
        onTeamsWrapperEnter() {
            this.isTeamsListHover = true
            this.$nextTick(() => this.updateTeamsArrows())
        },
        onTeamsWrapperLeave() {
            this.isTeamsListHover = false
            this.stopTeamsHoverScroll()
        },
        onTeamsScroll() {
            this.updateTeamsArrows()
        },
        updateTeamsArrows() {
            const el = this.getTeamsScrollEl()

            if (!el || this.isMobile) {
                this.canScrollTeamsLeft = false
                this.canScrollTeamsRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.canScrollTeamsLeft = false
                this.canScrollTeamsRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollTeamsLeft = left > eps
            this.canScrollTeamsRight = left < max - eps
        },
        startTeamsHoverScroll(dir) {
            if (this.isMobile || !this.isTeamsListHover)
                return

            const el = this.getTeamsScrollEl()
            if (!el)
                return

            this.stopTeamsHoverScroll()
            this.teamsHoverScrollDir = dir

            const step = 8
            const tick = 16

            this.teamsHoverScrollTimer = setInterval(() => {
                if (!this.isTeamsListHover) {
                    this.stopTeamsHoverScroll()
                    return
                }

                const max = el.scrollWidth - el.clientWidth
                if (max <= 0) {
                    this.updateTeamsArrows()
                    this.stopTeamsHoverScroll()
                    return
                }

                let next = el.scrollLeft
                if (this.teamsHoverScrollDir === 'left')
                    next -= step
                if (this.teamsHoverScrollDir === 'right')
                    next += step

                if (next < 0)
                    next = 0
                if (next > max)
                    next = max

                el.scrollLeft = next
                this.updateTeamsArrows()

                if (next === 0 || next === max)
                    this.stopTeamsHoverScroll()
            }, tick)
        },
        stopTeamsHoverScroll() {
            if (this.teamsHoverScrollTimer) {
                clearInterval(this.teamsHoverScrollTimer)
                this.teamsHoverScrollTimer = null
            }

            this.teamsHoverScrollDir = null
        },
        scrollTeamIntoView(teamId, behavior = 'smooth') {
            const container = this.getTeamsScrollEl()
            const refEl = this.$refs[`plannerTeam_${teamId}`]
            const el = Array.isArray(refEl) ? refEl[0] : refEl

            if (!container || !el)
                return

            const max = container.scrollWidth - container.clientWidth
            if (max <= 0)
                return

            const targetLeft = Math.min(
                Math.max(el.offsetLeft - ((container.clientWidth - el.offsetWidth) / 2), 0),
                max
            )

            if (typeof container.scrollTo === 'function') {
                container.scrollTo({ left: targetLeft, behavior })
            } else {
                container.scrollLeft = targetLeft
            }

            this.$nextTick(() => this.updateTeamsArrows())
        },
        setDropPreview(payload = null) {
            if (!payload) {
                this.dropPreview = null
                return
            }

            if (
                this.dropPreview
                && this.dropPreview.mode === payload.mode
                && String(this.dropPreview.performerId) === String(payload.performerId)
                && this.dropPreview.dayKey === payload.dayKey
                && this.dropPreview.start?.isSame?.(payload.start)
                && this.dropPreview.end?.isSame?.(payload.end)
            ) {
                return
            }

            this.dropPreview = payload
        },
        clearDropPreview() {
            if (!this.dropPreview)
                return

            this.dropPreview = null
        },
        createTeamId() {
            return `planner-team-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        },
        normalizeUsers(users = []) {
            const byId = new Map()

            ;(users || []).forEach(user => {
                if (user?.id)
                    byId.set(String(user.id), user)
            })

            return Array.from(byId.values())
        },
        buildDefaultTeam(users = [], name = 'Моя команда') {
            return {
                id: this.createTeamId(),
                name,
                users: this.normalizeUsers(users)
            }
        },
        restoreLegacySelectedUsers() {
            try {
                const rawValue = localStorage.getItem(PLANNER_LEGACY_USERS_STORAGE_KEY)
                if (rawValue === null)
                    return null

                const parsed = JSON.parse(rawValue)
                return Array.isArray(parsed) ? parsed : null
            } catch (error) {
                return null
            }
        },
        normalizeTeam(team, fallbackName = 'Команда') {
            const users = this.normalizeUsers(team?.users || [])
            return {
                id: String(team?.id || this.createTeamId()),
                name: (team?.name || fallbackName).trim(),
                users
            }
        },
        restoreTeams() {
            try {
                const rawValue = localStorage.getItem(PLANNER_TEAMS_STORAGE_KEY)
                if (rawValue) {
                    const parsed = JSON.parse(rawValue)
                    if (Array.isArray(parsed) && parsed.length) {
                        return parsed
                            .map((team, index) => this.normalizeTeam(team, `Команда ${index + 1}`))
                            .filter(team => team.name)
                    }
                }
            } catch (error) {
                // fall through to legacy/default bootstrap
            }

            const legacyUsers = this.restoreLegacySelectedUsers()

            if (Array.isArray(legacyUsers) && legacyUsers.length)
                return [this.buildDefaultTeam(legacyUsers)]

            if (this.currentUser)
                return [this.buildDefaultTeam([this.currentUser])]

            return []
        },
        persistTeams() {
            try {
                localStorage.setItem(PLANNER_TEAMS_STORAGE_KEY, JSON.stringify(this.teams || []))
            } catch (error) {
                return null
            }
        },
        restoreActiveTeamIds(teams = this.teams) {
            const validIds = new Set((teams || []).map(team => String(team.id)))

            try {
                const rawValue = localStorage.getItem(PLANNER_ACTIVE_TEAMS_STORAGE_KEY)
                if (rawValue) {
                    const parsed = JSON.parse(rawValue)
                    if (Array.isArray(parsed)) {
                        const restored = parsed
                            .map(id => String(id))
                            .filter(id => validIds.has(id))
                            .slice(0, 2)

                        if (restored.length)
                            return restored
                    }
                }
            } catch (error) {
                // fall through to default team selection
            }

            return teams[0] ? [String(teams[0].id)] : []
        },
        persistActiveTeamIds() {
            try {
                localStorage.setItem(PLANNER_ACTIVE_TEAMS_STORAGE_KEY, JSON.stringify(this.activeTeamIds || []))
            } catch (error) {
                return null
            }
        },
        isTeamActive(teamId) {
            return this.activeTeamIds.includes(String(teamId))
        },
        async selectOnlyTeam(teamId) {
            const value = String(teamId)

            if (this.activeTeamIds.length === 1 && this.activeTeamIds[0] === value) {
                this.$nextTick(() => this.scrollTeamIntoView(value))
                return
            }

            this.activeTeamIds = [value]
            this.$nextTick(() => this.scrollTeamIntoView(value))
            await this.handleTeamsChange()
        },
        async toggleTeamCheckbox(teamId, checked) {
            const value = String(teamId)
            const nextIds = this.activeTeamIds.filter(id => id !== value)

            if (checked)
                nextIds.push(value)

            if (nextIds.length === this.activeTeamIds.length && nextIds.every((id, index) => id === this.activeTeamIds[index]))
                return

            this.activeTeamIds = nextIds
            this.$nextTick(() => this.scrollTeamIntoView(value))
            await this.handleTeamsChange()
        },
        async handleTeamsChange() {
            const currentIds = this.selectedUsers.map(user => String(user.id))
            this.collapsedPerformerIds = this.collapsedPerformerIds.filter(id => currentIds.includes(String(id)))
            this.persistCollapsedPerformers()
            this.persistTeams()
            this.persistActiveTeamIds()
            this.resetPlannerViewState()
            await this.reloadPlanner()
        },
        handleViewModeChange(value) {
            this.viewMode = value
        },
        scrollLeft() {
            this.clear()
            this.timer = setInterval(() => {
                if (!this.$refs.plannerBoardScroll)
                    return
                this.$refs.plannerBoardScroll.scrollLeft -= 5
                this.updateBoardArrows()
            }, 10)
        },
        scrollRight() {
            this.clear()
            this.timer = setInterval(() => {
                if (!this.$refs.plannerBoardScroll)
                    return
                this.$refs.plannerBoardScroll.scrollLeft += 5
                this.updateBoardArrows()
            }, 10)
        },
        clear() {
            clearInterval(this.timer)
            this.timer = null
        },
        handleScroll(event) {
            if (!event?.arrivedState) {
                this.updateBoardArrows()
                return
            }
            this.leftActive = !event.arrivedState.left
            this.rightActive = !event.arrivedState.right
        },
        updateBoardArrows() {
            const el = this.$refs.plannerBoardScroll

            if (!el) {
                this.leftActive = false
                this.rightActive = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.leftActive = false
                this.rightActive = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.leftActive = left > eps
            this.rightActive = left < max - eps
        },
        openCreateTeam() {
            this.teamEditor = createTeamEditorState()
            this.teamEditor.visible = true
            this.$nextTick(() => this.focusTeamNameInput())
        },
        openEditTeam(team) {
            this.teamEditor = {
                visible: true,
                id: String(team.id),
                name: team.name,
                users: this.normalizeUsers(team.users)
            }
            this.$nextTick(() => this.focusTeamNameInput())
        },
        closeTeamEditor() {
            this.teamEditor = createTeamEditorState()
        },
        focusTeamNameInput() {
            const inputRef = this.$refs.teamNameInput
            const input = Array.isArray(inputRef) ? inputRef[0] : inputRef

            if (!input)
                return

            if (typeof input.focus === 'function') {
                input.focus()
                return
            }

            if (input.$refs?.input && typeof input.$refs.input.focus === 'function')
                input.$refs.input.focus()
        },
        createDragPreviewElement(sourceEl) {
            if (!sourceEl || typeof document === 'undefined')
                return null

            const rect = sourceEl.getBoundingClientRect()
            const preview = sourceEl.cloneNode(true)
            const inlineAction = preview.querySelector('.planner_card_inline_action')
            const resizeHandle = preview.querySelector('.planner_board_card__resize')
            const avatars = preview.querySelectorAll('.ant-avatar, img')

            if (inlineAction)
                inlineAction.remove()
            if (resizeHandle)
                resizeHandle.remove()
            avatars.forEach(node => node.remove())

            preview.classList.remove('is-dragging')
            preview.classList.add('planner_drag_preview')
            preview.style.position = 'fixed'
            preview.style.top = '0'
            preview.style.left = '0'
            preview.style.width = `${rect.width}px`
            preview.style.height = `${rect.height}px`
            preview.style.pointerEvents = 'none'
            preview.style.zIndex = '9999'

            document.body.appendChild(preview)
            return preview
        },
        positionDragPreview(clientX = 0, clientY = 0) {
            if (!this.dragPreviewEl)
                return

            this.dragPreviewEl.style.top = `${clientY - this.dragPreviewOffsetY}px`
            this.dragPreviewEl.style.left = `${clientX - this.dragPreviewOffsetX}px`
        },
        destroyDragPreviewElement() {
            if (!this.dragPreviewEl)
                return

            this.dragPreviewEl.remove()
            this.dragPreviewEl = null
        },
        async saveTeam() {
            const name = (this.teamEditor.name || '').trim()
            const users = this.normalizeUsers(this.teamEditor.users)

            if (!name) {
                this.$message.warning('Введите название команды')
                return
            }

            if (!users.length) {
                this.$message.warning('Добавьте людей в команду')
                return
            }

            if (this.teamEditor.id) {
                this.teams = this.teams.map(team => (
                    String(team.id) === String(this.teamEditor.id)
                        ? { ...team, name, users }
                        : team
                ))
            } else {
                const team = {
                    id: this.createTeamId(),
                    name,
                    users
                }

                this.teams = [...this.teams, team]

                if (!this.activeTeamIds.length)
                    this.activeTeamIds = [String(team.id)]
            }

            this.closeTeamEditor()
            await this.handleTeamsChange()
        },
        async toggleTeamSelection(teamId) {
            const value = String(teamId)

            if (this.isTeamActive(value)) {
                this.activeTeamIds = this.activeTeamIds.filter(id => id !== value)
            } else {
                if (this.activeTeamIds.length >= 2) {
                    this.$message.warning('Можно выбрать не больше двух команд')
                    return
                }

                this.activeTeamIds = [...this.activeTeamIds, value]
            }

            await this.handleTeamsChange()
        },
        async removeTeam(teamId) {
            const value = String(teamId)
            const remainingTeams = this.teams.filter(team => String(team.id) !== value)

            this.teams = remainingTeams
            this.activeTeamIds = this.activeTeamIds.filter(id => id !== value)

            if (!this.activeTeamIds.length && remainingTeams.length)
                this.activeTeamIds = [String(remainingTeams[0].id)]

            await this.handleTeamsChange()
        },
        restoreCollapsedPerformers() {
            try {
                const rawValue = localStorage.getItem(PLANNER_COLLAPSED_PERFORMERS_STORAGE_KEY)
                if (!rawValue)
                    return []

                const parsed = JSON.parse(rawValue)
                return Array.isArray(parsed) ? parsed : []
            } catch (error) {
                return []
            }
        },
        persistCollapsedPerformers() {
            try {
                localStorage.setItem(PLANNER_COLLAPSED_PERFORMERS_STORAGE_KEY, JSON.stringify(this.collapsedPerformerIds || []))
            } catch (error) {
                return null
            }
        },
        resetPlannerViewState() {
            this.plannerViewToken += 1
            const timedVisible = {}
            const overviewVisible = {}

            this.performers.forEach(performer => {
                timedVisible[String(performer.id)] = 1
                overviewVisible[String(performer.id)] = this.overviewLength
            })

            this.timedDaysVisibleByPerformer = timedVisible
            this.overviewDaysVisibleByPerformer = overviewVisible
            this.timedColumnLoading = {}
            this.overviewColumnLoading = {}
            this.columnExtraItemsByPerformer = {}
        },
        getTimedVisibleLength(performerId) {
            return this.timedDaysVisibleByPerformer[String(performerId)] || 1
        },
        getOverviewVisibleLength(performerId) {
            return this.overviewDaysVisibleByPerformer[String(performerId)] || this.overviewLength
        },
        isTimedColumnLoading(performerId) {
            return Boolean(this.timedColumnLoading[String(performerId)])
        },
        isOverviewColumnLoading(performerId) {
            return Boolean(this.overviewColumnLoading[String(performerId)])
        },
        setColumnLoading(performerId, value, mode = 'timed') {
            const key = String(performerId)
            const field = mode === 'overview' ? 'overviewColumnLoading' : 'timedColumnLoading'

            this[field] = {
                ...this[field],
                [key]: value
            }
        },
        isPerformerCollapsed(performerId) {
            return this.collapsedPerformerIds.includes(String(performerId))
        },
        togglePerformerCollapse(performerId) {
            const value = String(performerId)

            if (this.isPerformerCollapsed(value))
                this.collapsedPerformerIds = this.collapsedPerformerIds.filter(item => item !== value)
            else
                this.collapsedPerformerIds = [...this.collapsedPerformerIds, value]

            this.persistCollapsedPerformers()
        },
        toEntityIds(value) {
            if (!value)
                return []

            if (Array.isArray(value))
                return value
                    .map(item => (typeof item === 'object' ? item?.id : item))
                    .filter(Boolean)

            if (typeof value === 'object')
                return value.id ? [value.id] : []

            return [value]
        },
        getItemPerformerIds(item) {
            const entityType = this.getEntityType(item)

            if (entityType === 'task') {
                const operatorIds = this.toEntityIds(item?.raw?.operator)
                return operatorIds.length ? operatorIds : (item?.performerIds || [])
            }

            if (entityType === 'request') {
                const specialistIds = this.toEntityIds(item?.raw?.specialist)
                return specialistIds.length ? specialistIds : (item?.performerIds || [])
            }

            if (entityType === 'event') {
                const memberIds = this.toEntityIds(item?.raw?.members)
                return memberIds.length ? memberIds : (item?.performerIds || [])
            }

            return item?.performerIds || []
        },
        itemHasPerformer(item, performerId) {
            return this.getItemPerformerIds(item).some(id => String(id) === String(performerId))
        },
        getEntityType(item) {
            if (item?.uid?.startsWith('task:'))
                return 'task'
            if (item?.uid?.startsWith('request:'))
                return 'request'
            if (item?.uid?.startsWith('event:'))
                return 'event'

            return item?.entityType || null
        },
        getTransferEntityType(item = this.transferState.item) {
            if (item && this.transferState.item && item.uid === this.transferState.item.uid)
                return this.transferState.entityType || this.getEntityType(item)

            return this.getEntityType(item)
        },
        getDaySlotOccupancy(performerId, dayKey, slot) {
            return this.timedSlotOccupancy?.[performerId]?.[dayKey]?.[slot.key] || 0
        },
        mergePlannerItemCollections(collections = []) {
            const byUid = new Map()

            collections.forEach(collection => {
                ;(collection || []).forEach(item => {
                    if (!item?.uid)
                        return

                    const existing = byUid.get(item.uid)

                    if (!existing) {
                        byUid.set(item.uid, {
                            ...item,
                            performerIds: [...(item.performerIds || [])],
                            relatedUsers: [...(item.relatedUsers || [])]
                        })
                        return
                    }

                    const performerIdsMap = new Map()
                    ;[...(existing.performerIds || []), ...(item.performerIds || [])].forEach(id => {
                        performerIdsMap.set(String(id), id)
                    })

                    const relatedUsersMap = new Map()
                    ;[...(existing.relatedUsers || []), ...(item.relatedUsers || [])].forEach(user => {
                        if (user?.id)
                            relatedUsersMap.set(String(user.id), user)
                    })

                    byUid.set(item.uid, {
                        ...existing,
                        performerIds: Array.from(performerIdsMap.values()),
                        relatedUsers: Array.from(relatedUsersMap.values()),
                        hasPerformer: existing.hasPerformer || item.hasPerformer,
                        hasRange: existing.hasRange || item.hasRange,
                        overlapsRange: existing.overlapsRange || item.overlapsRange,
                        isScheduled: existing.isScheduled || item.isScheduled,
                        primaryPerformerId: existing.primaryPerformerId || item.primaryPerformerId
                    })
                })
            })

            return Array.from(byUid.values())
        },
        appendCreatedPlannerItem(entityType, payload) {
            if (!payload)
                return

            const rawPayload = payload?.formData
                ? {
                    ...payload,
                    ...payload.formData,
                    id: payload.id || payload.formData.id
                }
                : payload

            delete rawPayload.formData

            const createdItems = buildPlannerItems({
                tasks: entityType === 'task' ? [rawPayload] : [],
                tickets: entityType === 'request' ? [rawPayload] : [],
                events: entityType === 'event' ? [rawPayload] : [],
                performers: this.performers,
                rangeStart: this.rangeStart,
                rangeEnd: this.rangeEnd
            })

            if (!createdItems.length)
                return

            this.plannerBaseItems = this.mergePlannerItemCollections([this.plannerBaseItems, createdItems])
        },
        handlePlannerTaskCreated(payload) {
            this.appendCreatedPlannerItem('task', payload)
        },
        handlePlannerEventCreated(payload) {
            this.appendCreatedPlannerItem('event', payload)
        },
        handlePlannerTicketCreated(payload) {
            this.appendCreatedPlannerItem('request', payload)
        },
        async fetchPlannerResults(url, params) {
            const { data } = await this.$http.get(url, { params })
            return Array.isArray(data?.results) ? data.results : []
        },
        async fetchPlannerRangeItems({ performerIds = [], performers = this.performers, start, end }) {
            const ids = (performerIds || []).filter(Boolean)

            if (!ids.length)
                return []

            const commonParams = {
                page: 1,
                page_size: TRANSFER_PAGE_SIZE,
                start: dateFormat(start),
                end: dateFormat(end),
                user: ids.join(',')
            }

            const [
                taskActivity,
                taskPinned,
                taskOther,
                eventResults,
                ticketActivity,
                ticketOther
            ] = await Promise.all([
                this.fetchPlannerResults('/tasks/task/my_day/', { ...commonParams, group: 'activity', role: 'is_executor', task_type: 'task' }),
                this.fetchPlannerResults('/tasks/task/my_day/', { ...commonParams, group: 'pinned', role: 'is_executor', task_type: 'task' }),
                this.fetchPlannerResults('/tasks/task/my_day/', { ...commonParams, group: 'other', role: 'is_executor', task_type: 'task' }),
                this.fetchPlannerResults('/calendars/events/my_day/', { ...commonParams }),
                this.fetchPlannerResults('/help_desk/tickets/my_day/', { ...commonParams, group: 'activity', role: 'is_operator' }),
                this.fetchPlannerResults('/help_desk/tickets/my_day/', { ...commonParams, group: 'other', role: 'is_operator' })
            ])

            return buildPlannerItems({
                tasks: [...taskActivity, ...taskPinned, ...taskOther],
                tickets: [...ticketActivity, ...ticketOther],
                events: eventResults,
                performers,
                rangeStart: start,
                rangeEnd: end
            })
        },
        async reloadPlanner() {
            if (!this.performers.length) {
                this.plannerBaseItems = []
                return
            }

            const loadToken = ++this.plannerLoadToken
            const viewToken = this.plannerViewToken
            this.plannerLoading = true

            try {
                const items = await this.fetchPlannerRangeItems({
                    performerIds: this.performers.map(user => user.id),
                    performers: this.performers,
                    start: this.rangeStart.clone(),
                    end: this.baseRangeEnd.clone()
                })

                if (loadToken !== this.plannerLoadToken || viewToken !== this.plannerViewToken)
                    return

                this.plannerBaseItems = items
            } catch (error) {
                errorHandler({ error })
            } finally {
                if (loadToken === this.plannerLoadToken)
                    this.plannerLoading = false
            }
        },
        getItemTypeLabel(item) {
            if (this.getTransferEntityType(item) === 'task')
                return this.$t('planner.type_task')
            if (this.getTransferEntityType(item) === 'request')
                return this.$t('planner.type_request')
            return this.$t('planner.type_event')
        },
        formatItemWindow(item) {
            if (item.allDay)
                return this.$t('planner.all_day')
            if (item.startAt && item.endAt)
                return `${item.startAt.format('DD.MM HH:mm')} - ${item.endAt.format('HH:mm')}`
            if (item.startAt)
                return `${item.startAt.format('DD.MM HH:mm')} ${this.$t('planner.no_time')}`
            return this.$t('planner.no_time')
        },
        formatTransferSlot(start, end) {
            if (!start || !end)
                return ''

            return `${start.format('DD.MM HH:mm')} - ${end.format('HH:mm')}`
        },
        isTimedDropPreviewVisible(performerId, dayKey) {
            return this.dropPreview?.mode === 'timed'
                && String(this.dropPreview.performerId) === String(performerId)
                && this.dropPreview.dayKey === dayKey
        },
        isOverviewDropPreviewVisible(performerId, dayKey) {
            return this.dropPreview?.mode === 'overview'
                && String(this.dropPreview.performerId) === String(performerId)
                && this.dropPreview.dayKey === dayKey
        },
        isTransferCellSelected(cell) {
            return this.transferState.selectedCells.some(selectedCell => selectedCell.key === cell.key)
        },
        sortTransferCells(cells = []) {
            return [...cells].sort((a, b) => a.start.valueOf() - b.start.valueOf())
        },
        normalizeTransferCells(cells = []) {
            if (!cells.length)
                return []

            const sorted = this.sortTransferCells(cells)
            const performerId = String(sorted[0].performerId)
            const isSamePerformer = sorted.every(cell => String(cell.performerId) === performerId)

            if (!isSamePerformer)
                return null

            for (let index = 1; index < sorted.length; index += 1) {
                if (!sorted[index - 1].end.isSame(sorted[index].start))
                    return null
            }

            return sorted
        },
        syncTransferSelection(cells = []) {
            const sorted = this.sortTransferCells(cells)

            this.transferState.selectedCells = sorted

            if (!sorted.length) {
                this.transferState.performer = null
                this.transferState.start = null
                this.transferState.end = null
                return
            }

            this.transferState.performer = sorted[0].performer
            this.transferState.start = sorted[0].start.clone()
            this.transferState.end = sorted[sorted.length - 1].end.clone()
        },
        queueCardStyle(item) {
            return {
                '--planner-card-bg': '#f7f9fc',
                '--planner-card-border': '#dbe3ef',
                '--planner-card-color': item.meta.color,
                '--planner-card-accent': item.meta.color
            }
        },
        boardCardStyle(layout) {
            const resizePreview = this.resizeState?.item?.uid === layout.item.uid ? this.resizeState.previewEndAt : null
            const endMinute = resizePreview
                ? Math.max(resizePreview.diff(layout.item.startAt, 'minutes') + layout.startMinute, layout.startMinute + this.timedSlotMinutes)
                : layout.endMinute
            const top = layout.startMinute * PIXELS_PER_MINUTE
            const height = Math.max((endMinute - layout.startMinute) * PIXELS_PER_MINUTE, 34)
            const width = 100 / layout.lanes
            const left = layout.lane * width

            return {
                top: `${top}px`,
                height: `${height}px`,
                width: `calc(${width}% - 8px)`,
                left: `calc(${left}% + 4px)`,
                '--planner-card-bg': '#f7f9fc',
                '--planner-card-border': '#dbe3ef',
                '--planner-card-color': layout.item.meta.color,
                '--planner-card-accent': layout.item.meta.color
            }
        },
        getCardSecondary(item) {
            if (this.getTransferEntityType(item) === 'request')
                return item.raw?.customer_card?.name || item.raw?.org_admin?.name || ''

            if (this.getTransferEntityType(item) === 'task')
                return item.raw?.counter ? `#${item.raw.counter}` : item.relatedUsers?.[0]?.full_name || ''

            return item.relatedUsers?.[0]?.full_name || ''
        },
        getCardUsers(item) {
            return Array.isArray(item.relatedUsers) ? item.relatedUsers.slice(0, 2) : []
        },
        openItem(item) {
            if (this.suppressCardClick) {
                this.suppressCardClick = false
                return
            }

            const query = { ...this.$route.query }
            const entityType = this.getTransferEntityType(item)

            delete query.task
            delete query.event
            delete query.requestView

            if (entityType === 'task')
                query.task = item.id
            if (entityType === 'request')
                query.requestView = item.id
            if (entityType === 'event')
                query.event = item.id

            this.$router.push({ query })
        },
        getPlannerSlotStart(dayDate, minute) {
            return moment(dayDate)
                .startOf('day')
                .add(DEFAULT_DAY_START + minute, 'minutes')
                .seconds(0)
                .milliseconds(0)
        },
        detachResizeListeners() {
            if (this.resizeMoveHandler)
                window.removeEventListener('mousemove', this.resizeMoveHandler)
            if (this.resizeUpHandler)
                window.removeEventListener('mouseup', this.resizeUpHandler)
        },
        openSlotPicker(performer, minute, dayDate, durationMinutes = 60) {
            const start = this.getPlannerSlotStart(dayDate, minute)

            this.slotPicker = {
                visible: true,
                performer,
                start,
                end: start.clone().add(durationMinutes, 'minutes')
            }
        },
        closeSlotPicker() {
            this.slotPicker = { visible: false, performer: null, start: null, end: null }
        },
        createFromSlot(type) {
            const performer = this.slotPicker.performer
            const start = this.slotPicker.start
            const end = this.slotPicker.end

            this.closeSlotPicker()

            if (!performer || !start || !end)
                return

            if (type === 'task') {
                eventBus.$emit('add_task_modal', {
                    task_type: 'task',
                    create_handler: 'planner',
                    operator: performer,
                    date_start_plan: start.toISOString(),
                    dead_line: end.toISOString(),
                    is_indefinite: false
                })
                return
            }

            if (type === 'event') {
                eventBus.$emit('open_event_form', start.toISOString(), end.toISOString(), null, null, 'planner', true, null, {
                    members: [performer]
                })
                return
            }

            eventBus.$emit('helpdesc_add_tickets', {
                plannerCreate: true,
                specialist: performer,
                receipt_date: start.toISOString(),
                dead_line: end.toISOString()
            })
        },
        clearDrag() {
            this.dragState = null
            this.clearDropPreview()
            document.body.classList.remove('planner-dragging')
            this.destroyDragPreviewElement()
        },
        handleDayDragOver(performer, dayDate, event) {
            if (!this.dragState?.item)
                return

            const start = this.resolveDayDropStart(dayDate, event)
            const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

            this.setDropPreview({
                mode: 'timed',
                performerId: performer.id,
                dayKey: moment(dayDate).format('YYYY-MM-DD'),
                start,
                end
            })
        },
        handleOverviewDragOver(performer, date) {
            if (!this.dragState?.item)
                return

            const start = moment(date)
                .startOf('day')
                .hour(DEFAULT_DAY_START / 60)
                .minute(DEFAULT_DAY_START % 60)
                .second(0)
                .millisecond(0)
            const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

            this.setDropPreview({
                mode: 'overview',
                performerId: performer.id,
                dayKey: moment(date).format('YYYY-MM-DD'),
                start,
                end
            })
        },
        handleDropAreaLeave(event) {
            const relatedTarget = event.relatedTarget

            if (relatedTarget && event.currentTarget?.contains?.(relatedTarget))
                return

            this.clearDropPreview()
        },
        resolveDayDropStartFromTarget(dayDate, target, clientY) {
            const bounds = target.getBoundingClientRect()
            const rawTop = clamp(clientY - bounds.top, 0, bounds.height)
            const slotMinutes = this.timedSlotMinutes || SLOT_MINUTES
            const minutesFromStart = Math.floor(rawTop / PIXELS_PER_MINUTE / slotMinutes) * slotMinutes

            return this.getPlannerSlotStart(dayDate, minutesFromStart)
        },
        resolveDayDropStart(dayDate, event) {
            return this.resolveDayDropStartFromTarget(dayDate, event.currentTarget, event.clientY)
        },
        async handleDayDrop(performer, dayDate, event) {
            if (!this.dragState?.item)
                return

            const start = this.resolveDayDropStart(dayDate, event)
            const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

            await this.applyTransfer({
                item: this.dragState.item,
                performer,
                start,
                end,
                replacePerformerId: this.dragState.performerId
            })

            this.clearDrag()
        },
        async handleOverviewDrop(performer, date, event) {
            if (!this.dragState?.item)
                return

            event.preventDefault()

            const start = moment(date)
                .startOf('day')
                .hour(DEFAULT_DAY_START / 60)
                .minute(DEFAULT_DAY_START % 60)
                .second(0)
                .millisecond(0)
            const end = start.clone().add(getDefaultDurationMinutes(this.dragState.item), 'minutes')

            await this.applyTransfer({
                item: this.dragState.item,
                performer,
                start,
                end,
                replacePerformerId: this.dragState.performerId
            })

            this.clearDrag()
        },
        async loadColumnRange(performer, startDayOffset, daysCount, mode = 'timed') {
            if (!performer?.id || daysCount <= 0)
                return false

            const performerId = String(performer.id)
            const viewToken = this.plannerViewToken
            const start = this.rangeStart.clone().add(startDayOffset, 'days').startOf('day')
            const end = start.clone().add(daysCount - 1, 'days').endOf('day')

            this.setColumnLoading(performerId, true, mode)

            try {
                const items = await this.fetchPlannerRangeItems({
                    performerIds: [performer.id],
                    performers: this.performers,
                    start,
                    end
                })

                if (viewToken !== this.plannerViewToken)
                    return

                this.columnExtraItemsByPerformer = {
                    ...this.columnExtraItemsByPerformer,
                    [performerId]: this.mergePlannerItemCollections([
                        this.columnExtraItemsByPerformer[performerId] || [],
                        items
                    ])
                }
                return true
            } catch (error) {
                errorHandler({ error })
                return false
            } finally {
                this.setColumnLoading(performerId, false, mode)
            }
        },
        handleTimedColumnScroll(performer, event) {
            if (!this.isTimedView)
                return

            const target = event.target
            if (!target)
                return

            if (target.scrollTop + target.clientHeight >= target.scrollHeight - 320)
                this.extendTimedDays(performer)
        },
        startResize(item, performerId, event) {
            if (event.button !== 0 || !item?.startAt)
                return

            event.preventDefault()

            const performer = this.performers.find(user => String(user.id) === String(performerId))
            const endAt = item.endAt ? item.endAt.clone() : item.startAt.clone().add(getDefaultDurationMinutes(item), 'minutes')

            this.resizeState = {
                item,
                performer,
                performerId,
                startAt: item.startAt.clone(),
                baseEndAt: endAt.clone(),
                previewEndAt: endAt.clone(),
                originY: event.clientY
            }

            if (!this.resizeMoveHandler)
                this.resizeMoveHandler = resizeEvent => this.handleResizeMove(resizeEvent)
            if (!this.resizeUpHandler)
                this.resizeUpHandler = () => this.finishResize()

            this.detachResizeListeners()
            window.addEventListener('mousemove', this.resizeMoveHandler)
            window.addEventListener('mouseup', this.resizeUpHandler)
        },
        handleResizeMove(event) {
            if (!this.resizeState)
                return

            const deltaPixels = event.clientY - this.resizeState.originY
            const deltaSteps = Math.round(deltaPixels / (PIXELS_PER_MINUTE * this.timedSlotMinutes))
            const baseDuration = this.resizeState.baseEndAt.diff(this.resizeState.startAt, 'minutes')
            const duration = Math.max(this.timedSlotMinutes, baseDuration + (deltaSteps * this.timedSlotMinutes))
            const dayLimit = this.resizeState.startAt.clone().startOf('day').add(DEFAULT_DAY_END, 'minutes')
            const previewEndAt = this.resizeState.startAt.clone().add(duration, 'minutes')

            this.resizeState.previewEndAt = previewEndAt.isAfter(dayLimit) ? dayLimit : previewEndAt
        },
        async finishResize() {
            if (!this.resizeState)
                return

            const resizeState = { ...this.resizeState }

            this.detachResizeListeners()
            this.resizeState = null

            if (!resizeState.performer || !resizeState.previewEndAt || resizeState.previewEndAt.isSame(resizeState.baseEndAt))
                return

            await this.applyTransfer({
                item: resizeState.item,
                performer: resizeState.performer,
                start: resizeState.startAt,
                end: resizeState.previewEndAt,
                replacePerformerId: resizeState.performerId
            })
        },
        getTransferRange(daysVisible = this.transferState.daysVisible || TRANSFER_LOOKAHEAD_DAYS) {
            const start = moment(this.selectedDate).startOf('day')

            return {
                start,
                end: start.clone().add(daysVisible - 1, 'days').endOf('day')
            }
        },
        createTransferSlotKey(start, end) {
            return `${start.toISOString()}__${end.toISOString()}`
        },
        async fetchTransferPlannerItems() {
            const transferRange = this.getTransferRange()
            return this.fetchPlannerRangeItems({
                performerIds: this.performers.map(user => user.id),
                performers: this.performers,
                start: transferRange.start,
                end: transferRange.end
            })
        },
        getTransferCellItems(items, performerId, start, end) {
            return items.filter(item =>
                this.itemHasPerformer(item, performerId)
                && item.startAt
                && item.endAt
                && item.startAt.isBefore(end)
                && item.endAt.isAfter(start)
            )
        },
        buildTransferScheduleDays(items, durationMinutes) {
            const transferRange = this.getTransferRange()
            const sourceId = this.transferState.item?.id
            const sourceType = this.getTransferEntityType()

            return Array.from({ length: this.transferState.daysVisible }).map((_, index) => {
                const dayStart = transferRange.start.clone().add(index, 'days')
                const dayEnd = dayStart.clone().endOf('day')
                const dayItems = items
                    .filter(item => !(String(item.id) === String(sourceId) && this.getEntityType(item) === sourceType))
                    .filter(item => item.startAt && item.endAt)
                    .filter(item => item.startAt.isBefore(dayEnd) && item.endAt.isAfter(dayStart))

                const slots = []

                for (let minute = DEFAULT_DAY_START; minute <= DEFAULT_DAY_END - durationMinutes; minute += durationMinutes) {
                    const start = dayStart.clone().add(minute, 'minutes')
                    const end = start.clone().add(durationMinutes, 'minutes')
                    const cells = this.performers.map(performer => {
                        const cellItems = this.getTransferCellItems(dayItems, performer.id, start, end)

                        return {
                            key: `${performer.id}:${this.createTransferSlotKey(start, end)}`,
                            performer,
                            performerId: performer.id,
                            start,
                            end,
                            items: cellItems
                        }
                    })

                    slots.push({
                        key: this.createTransferSlotKey(start, end),
                        start,
                        end,
                        label: `${start.format('HH:mm')} - ${end.format('HH:mm')}`,
                        cells
                    })
                }

                return {
                    key: dayStart.format('YYYY-MM-DD'),
                    date: dayStart,
                    slots
                }
            })
        },
        getTransferCellClass(cell) {
            return {
                'is-active': this.isTransferCellSelected(cell),
                'is-busy': cell.items.length > 0,
                'is-free': cell.items.length === 0
            }
        },
        getTransferCellStyle(cell) {
            return {
                '--planner-transfer-cell-bg': cell.items.length ? '#fff1e8' : '#f8fafc',
                '--planner-transfer-cell-border': cell.items.length ? '#f97316' : '#dbe3ef',
                '--planner-transfer-cell-color': cell.items.length ? '#c2410c' : '#0f172a'
            }
        },
        getTransferCellTitle(cell, slot) {
            const performerName = cell.performer?.full_name || cell.performer?.name || ''
            const baseLabel = `${performerName}: ${slot.label}`

            if (!cell.items.length)
                return baseLabel

            const itemNames = cell.items.slice(0, 3).map(item => item.name).join(', ')
            const suffix = cell.items.length > 3 ? '...' : ''
            return `${baseLabel}\n${itemNames}${suffix}`
        },
        getTransferCellBusyLabel(cell) {
            if (!cell?.items?.length)
                return ''

            const names = cell.items.slice(0, 2).map(item => item.name).filter(Boolean)
            if (cell.items.length > 2)
                names.push(`+${cell.items.length - 2}`)

            return names.join(', ')
        },
        selectTransferSlot(cell) {
            if (!cell)
                return

            const currentCells = [...this.transferState.selectedCells]
            const existingIndex = currentCells.findIndex(selectedCell => selectedCell.key === cell.key)

            if (existingIndex !== -1) {
                const nextCells = currentCells.filter(selectedCell => selectedCell.key !== cell.key)
                const normalizedSelection = this.normalizeTransferCells(nextCells)

                this.syncTransferSelection(normalizedSelection || [])
                return
            }

            const normalizedSelection = this.normalizeTransferCells([...currentCells, cell])
            this.syncTransferSelection(normalizedSelection || [cell])
        },
        async loadTransferSlots() {
            if (!this.transferState.item || !this.performers.length)
                return

            const itemUid = this.transferState.item.uid
            const durationMinutes = this.transferState.durationMinutes || this.transferSlotMinutes
            const prevSelectedCells = [...this.transferState.selectedCells]
            const prevStart = this.transferState.start ? this.transferState.start.clone() : null
            const prevEnd = this.transferState.end ? this.transferState.end.clone() : null
            const prevPerformer = this.transferState.performer

            this.transferState.slotsLoading = true

            try {
                const items = await this.fetchTransferPlannerItems()

                if (!this.transferState.visible
                    || this.transferState.item?.uid !== itemUid)
                    return

                this.transferState.scheduleDays = this.buildTransferScheduleDays(items, durationMinutes)

                if (prevSelectedCells.length) {
                    const scheduleCells = this.transferState.scheduleDays.reduce((acc, day) => {
                        day.slots.forEach(slot => acc.push(...slot.cells))
                        return acc
                    }, [])
                    const matchedCells = prevSelectedCells
                        .map(selectedCell => scheduleCells.find(cell => cell.key === selectedCell.key))
                        .filter(Boolean)

                    if (matchedCells.length) {
                        this.syncTransferSelection(matchedCells)
                    } else {
                        this.transferState.start = prevStart
                        this.transferState.end = prevEnd
                        this.transferState.performer = prevPerformer
                        this.transferState.selectedCells = prevSelectedCells
                    }
                }
            } catch (error) {
                errorHandler({ error })
                this.transferState.scheduleDays = []
            } finally {
                if (this.transferState.visible && this.transferState.item?.uid === itemUid)
                    this.transferState.slotsLoading = false
            }
        },
        handleTransferScheduleScroll(event) {
            const target = event.target
            if (!target || this.transferState.slotsLoading)
                return

            if (target.scrollTop + target.clientHeight >= target.scrollHeight - 320)
                this.extendTransferSchedule()
        },
        async extendTransferSchedule() {
            if (this.transferState.slotsLoading || !this.transferState.visible)
                return

            this.transferState.daysVisible += TRANSFER_LOOKAHEAD_CHUNK
            await this.loadTransferSlots()
        },
        handleOverviewDaysScroll(performer, event) {
            if (this.isTimedView)
                return

            const target = event.target
            if (!target)
                return

            if (target.scrollTop + target.clientHeight >= target.scrollHeight - 240)
                this.extendOverviewDays(performer)
        },
        async extendOverviewDays(performer) {
            if (this.isTimedView || !performer?.id || this.isOverviewColumnLoading(performer.id))
                return

            const performerId = String(performer.id)
            const currentVisible = this.getOverviewVisibleLength(performerId)
            const loaded = await this.loadColumnRange(performer, currentVisible, 7, 'overview')

            if (!loaded)
                return

            this.overviewDaysVisibleByPerformer = {
                ...this.overviewDaysVisibleByPerformer,
                [performerId]: currentVisible + 7
            }
        },
        async extendTimedDays(performer) {
            if (!this.isTimedView || !performer?.id || this.isTimedColumnLoading(performer.id))
                return

            const performerId = String(performer.id)
            const currentVisible = this.getTimedVisibleLength(performerId)
            const loaded = await this.loadColumnRange(performer, currentVisible, TIMED_DAYS_CHUNK, 'timed')

            if (!loaded)
                return

            this.timedDaysVisibleByPerformer = {
                ...this.timedDaysVisibleByPerformer,
                [performerId]: currentVisible + TIMED_DAYS_CHUNK
            }
        },
        async openTransfer(item, performerId = null) {
            const entityType = this.getEntityType(item)

            this.transferState = {
                ...createTransferState(),
                visible: true,
                item,
                entityType,
                durationMinutes: this.transferSlotMinutes,
                replacePerformerId: performerId
            }

            await this.loadTransferSlots()
        },
        closeTransfer() {
            this.transferState = createTransferState()
        },
        async submitTransfer() {
            if (!this.transferState.item || !this.transferState.performer || !this.transferState.start || !this.transferState.end || !this.transferState.selectedCells.length) {
                this.$message.warning(this.$t('planner.transfer_need_slot'))
                return
            }

            await this.applyTransfer({
                item: this.transferState.item,
                entityType: this.transferState.entityType,
                performer: this.transferState.performer,
                start: this.transferState.start,
                end: this.transferState.end,
                replacePerformerId: this.transferState.replacePerformerId
            }, true)
        },
        updatePlannerItemCollectionAfterTransfer(collection = [], payload = {}) {
            if (!Array.isArray(collection) || !collection.length)
                return collection

            const {
                item,
                performer,
                start,
                end,
                replacePerformerId = null,
                resolvedEntityType = this.getTransferEntityType(item)
            } = payload

            return collection.map(collectionItem => {
                if (!collectionItem || collectionItem.uid !== item.uid)
                    return collectionItem

                const nextRaw = { ...(collectionItem.raw || {}) }
                const nextItem = {
                    ...collectionItem,
                    startAt: start.clone(),
                    endAt: end.clone(),
                    hasRange: true,
                    overlapsRange: start.isBefore(this.rangeEnd) && end.isAfter(this.rangeStart),
                    allDay: false
                }

                if (resolvedEntityType === 'task') {
                    nextRaw.operator = performer.id
                    nextItem.performerIds = [performer.id]
                    nextItem.relatedUsers = [performer]
                    nextItem.primaryPerformerId = performer.id
                } else if (resolvedEntityType === 'request') {
                    nextRaw.specialist = performer.id
                    nextRaw.start_date = start.toISOString()
                    nextRaw.end_date = end.toISOString()
                    nextRaw.dead_line = end.toISOString()
                    nextItem.performerIds = [performer.id]
                    nextItem.relatedUsers = [performer]
                    nextItem.primaryPerformerId = performer.id
                } else if (resolvedEntityType === 'event') {
                    const existingUsers = Array.isArray(collectionItem.relatedUsers) ? [...collectionItem.relatedUsers] : []
                    const filteredUsers = replacePerformerId
                        ? existingUsers.filter(user => String(user?.id) !== String(replacePerformerId))
                        : existingUsers
                    const nextRelatedUsers = filteredUsers.some(user => String(user?.id) === String(performer.id))
                        ? filteredUsers
                        : [...filteredUsers, performer]
                    const nextPerformerIds = nextRelatedUsers.map(user => user.id).filter(Boolean)

                    nextRaw.members = nextPerformerIds
                    nextRaw.start_at = start.toISOString()
                    nextRaw.end_at = end.toISOString()
                    nextItem.performerIds = nextPerformerIds
                    nextItem.relatedUsers = nextRelatedUsers
                    nextItem.primaryPerformerId = nextPerformerIds[0] || performer.id
                }

                nextItem.raw = nextRaw
                nextItem.hasPerformer = Array.isArray(nextItem.performerIds) && nextItem.performerIds.length > 0
                nextItem.isScheduled = nextItem.hasPerformer && nextItem.hasRange && !nextItem.allDay && nextItem.overlapsRange

                return nextItem
            })
        },
        applyTransferOptimisticUpdate(payload) {
            this.plannerBaseItems = this.updatePlannerItemCollectionAfterTransfer(this.plannerBaseItems, payload)

            this.columnExtraItemsByPerformer = Object.entries(this.columnExtraItemsByPerformer || {}).reduce((acc, [performerId, items]) => {
                acc[performerId] = this.updatePlannerItemCollectionAfterTransfer(items, payload)
                return acc
            }, {})
        },
        async applyTransfer({ item, entityType = null, performer, start, end, replacePerformerId = null }, closeModal = false) {
            if (!item || !performer || !start || !end)
                return

            try {
                this.transferState.loading = true
                const resolvedEntityType = entityType || this.getTransferEntityType(item)

                if (resolvedEntityType === 'task') {
                    await this.$http.patch(`/tasks/task/${item.id}/`, {
                        operator: performer.id,
                        date_start_plan: start.toISOString(),
                        dead_line: end.toISOString()
                    })
                } else if (resolvedEntityType === 'request') {
                    await this.$http.patch(`/help_desk/tickets/${item.id}/`, {
                        specialist: performer.id,
                        start_date: start.toISOString(),
                        end_date: end.toISOString(),
                        dead_line: end.toISOString()
                    })
                } else if (resolvedEntityType === 'event') {
                    const detailResponse = await this.$http.get(`/calendars/events/${item.id}/`)
                    const detail = detailResponse.data || {}
                    const fallbackMembers = Array.isArray(item.relatedUsers) ? item.relatedUsers : []
                    let members = Array.isArray(detail.members)
                        ? detail.members.map(member => member.id || member).filter(Boolean)
                        : fallbackMembers.map(member => member.id).filter(Boolean)

                    if (replacePerformerId)
                        members = members.filter(memberId => String(memberId) !== String(replacePerformerId))
                    if (!members.includes(performer.id))
                        members.push(performer.id)

                    await this.$http.patch(`/calendars/events/${item.id}/`, {
                        members,
                        start_at: start.toISOString(),
                        end_at: end.toISOString()
                    })
                } else {
                    this.$message.error('Unknown planner entity type')
                    return
                }

                this.applyTransferOptimisticUpdate({
                    item,
                    performer,
                    start,
                    end,
                    replacePerformerId,
                    resolvedEntityType
                })
                this.$message.success(this.$t('planner.moved_success'))
                await this.reloadPlanner()

                if (closeModal)
                    this.closeTransfer()
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.transferState.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped src="./page.scss"></style>
