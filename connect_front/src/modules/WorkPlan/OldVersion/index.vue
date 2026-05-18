<template>
    <div 
        ref="workPlanWrapper" 
        class="mr-2 ml-4">
        <a-popover 
            v-model="visible"
            :trigger="taskEdit ? 'none' : 'click'"
            :autoAdjustOverflow="false"
            placement="bottomRight"
            transitionName=""
            :overlayStyle="taskEdit ? { pointerEvents: 'auto' } : {}"
            :overlayClassName="`work_plan_popover ${full && 'full_popover'}`"
            @visibleChange="visibleChange">
            <a-button 
                type="green"
                :loading="submitLoading"
                class="flex items-center work_btn"
                :class="!visible && 'work_plan_btn'">
                {{ $t('workplan.my_day') }}
                <i class="fi fi-rr-play ml-5" />
            </a-button>
            <template #content>
                <a-spin 
                    class="w-full" 
                    size="small" 
                    :spinning="loading || submitLoading">
                    <div 
                        ref="workPlanPopWrap" 
                        class="wp_wrapper">
                        <div class="wp_wrapper__header flex items-center justify-between">
                            <div class="flex items-center">
                                <a-date-picker 
                                    :value="selectedDay"
                                    format="DD.MM.YYYY"
                                    :allowClear="false"
                                    :locale="locale"
                                    :disabledDate="disabledFutureDates"
                                    :getCalendarContainer="getPopupContainer"
                                    :placeholder="$t('workplan.old_select_day')"
                                    @change="changeDate"
                                    @openChange="onOpenChange"
                                    @panelChange="onPanelChange">
                                    <i slot="suffixIcon" class="fi fi-rr-calendar-lines" />
                                    <template slot="dateRender" slot-scope="current, today">
                                        <div 
                                            v-if="dailyWorkRecords[current.format('YYYY-MM-DD')]"
                                            class="ant-calendar-date" 
                                            :style="getCurrentStyle(current, today)"
                                            v-tippy="{ inertia : true, duration : [300, 300], delay: [500, 0], content: tippyContent(current) }">
                                            {{ current.date() }}
                                        </div>
                                        <div 
                                            v-else
                                            class="ant-calendar-date" 
                                            :style="getCurrentStyle(current, today)">
                                            {{ current.date() }}
                                        </div>
                                    </template>
                                </a-date-picker>
                                <a-button 
                                    v-if="!isSelectedDayToday"
                                    type="ui" 
                                    ghost
                                    shape="circle"
                                    flaticon
                                    v-tippy="{ inertia : true}"
                                    :content="$t('workplan.today')"
                                    class="ml-1 blue_color"
                                    icon="fi-rr-calendar-day"
                                    @click="changeDate($moment())" />
                                <h4 class="ml-3">{{ $t('workplan.drawer_title') }}</h4>
                            </div>
                            <div class="flex items-center">
                                <a-button
                                    v-if="daily && isCompleted"
                                    type="ui" 
                                    ghost
                                    shape="circle"
                                    flaticon
                                    :disabled="isEdit"
                                    v-tippy="{ inertia : true}"
                                    :content="$t('workplan.edit')"
                                    icon="fi fi-rr-edit"
                                    @click="edit" />
                                <a-button 
                                    type="ui" 
                                    ghost
                                    shape="circle"
                                    flaticon
                                    :key="`${full}`"
                                    v-tippy="{ inertia : true}"
                                    :content="full ? $t('workplan.collapse') : $t('workplan.fullscreen')"
                                    :icon="full ? 'fi-rr-compress' : 'fi fi-rr-expand'"
                                    @click="full = !full" />
                                <a-button 
                                    type="ui" 
                                    ghost
                                    shape="circle"
                                    class="mr-2"
                                    flaticon
                                    icon="fi fi-rr-settings"
                                    v-tippy="{ inertia : true}"
                                    :content="$t('workplan.open_access')"
                                    @click="openProfile" />
                                <a-button 
                                    type="ui" 
                                    ghost
                                    shape="circle"
                                    flaticon
                                    icon="fi-rr-cross"
                                    @click="visible = false" />
                            </div>
                        </div>
                        <div class="wp_wrapper__body">
                            <div class="body_block body_block__tasks">
                                <div 
                                    class="body_block__head day-plan"
                                    :style="isTaskScrolled && 'box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.02), 0px 3px 4px rgba(0, 0, 0, 0.08);'">
                                    <div class="block_title">
                                        
                                    </div>
                                    <div class="block_title">{{ $t('workplan.tab_tasks') }}</div>
                                    <div class="block_title text-right">{{ $t('workplan.plan') }}</div>
                                    <div class="block_title text-right">{{ $t('workplan.fact') }}</div>
                                </div>
                                <div 
                                    ref="taskList" 
                                    class="body_block__body"
                                    @scroll="taskListScroll">
                                    <a-form-model
                                        ref="ruleForm"
                                        :model="form">
                                        <div v-if="isCompleted && !isEdit" class="comlited-deyly">
                                            <div 
                                                v-for="(item, index) in daily.plane_items" 
                                                :key="item.id"
                                                class="day-plan py-1">
                                                <div class="text-right">{{ index+1 }}.</div>
                                                <div class="break-words task_label w-full" @click="openTask(item.task.id)">
                                                    <span>{{ item.task.name }}</span>
                                                </div>
                                                <div  class="text-right">
                                                    {{ timeFormat(item.duration_plane) }}{{ $t('workplan.hour_letter') }}
                                                </div>
                                                <div  class="text-right">
                                                    {{ timeFormat(item.duration_fact) }}{{ $t('workplan.hour_letter') }}
                                                </div>
                                                <div class="text-right">
                                                    <i v-if="item.is_result" 
                                                       v-tippy="{ inertia : true, duration : '[600,300]'}" 
                                                       :content="$t('workplan.old_not_count')"
                                                       class="fi fi-rr-check text-green-500" />
                                                </div>
                                                <div class="">
                                                    <a-popover 
                                                        v-if="item.description.length"
                                                        destroyTooltipOnHide
                                                        trigger="click"
                                                        transitionName=""
                                                        :title="$t('workplan.comment')"
                                                        :overlayStyle="popoverStyle"
                                                        autoAdjustOverflow
                                                        :getPopupContainer="getPopupContainer"
                                                        overlayClassName="plan_comment_popover">
                                                        <a-button 
                                                            flaticon
                                                            type="ui"
                                                            ghost
                                                            size="small"
                                                            shape="circle"
                                                            class="relative -top-1"
                                                            icon="fi-rr-comment-alt" />
                                                        <template #content>
                                                            <div class="comment_wrapper">
                                                                <div class="comment_desc_text">
                                                                    {{ item.description }}
                                                                </div>
                                                            </div>
                                                        </template>
                                                    </a-popover>
                                                </div>
                                            </div>
                                        </div>
                                        <template v-else>
                                            <div 
                                                v-for="(item, index) in form.plane_items" 
                                                :key="item.id"
                                                class="form_item"
                                                :class="form.plane_items.length > 1 && 'long'">
                                                <div class="form_item__row">
                                                    <div class="flex items-center form_item_col form_item_col__1">
                                                        <div class="mr-2">
                                                            {{ index+1 }}
                                                        </div>
                                                        <a-form-model-item 
                                                            :prop="'plane_items.' + index + '.work_type'" 
                                                            :ref="'plane_items.' + index + '.work_type'" 
                                                            :rules="{
                                                                required: true,
                                                                message: $t('field_required'),
                                                                trigger: ['change', 'blur']
                                                            }"
                                                            class="mb-0 w-full s_work_type min-w-0">
                                                            <a-select 
                                                                v-model="item.work_type" 
                                                                size="large"
                                                                class="select_item w-full"
                                                                :class="item.work_type && 'selected'"
                                                                :loading="taskWorkTypesLoading"
                                                                :getPopupContainer="getPopupContainer" 
                                                                :placeholder="$t('workplan.old_work_type')"
                                                                @change="taskChange(index, item)">
                                                                <i class="fi fi-rr-angle-small-down" slot="suffixIcon" />
                                                                <a-select-option 
                                                                    v-for="type in taskWorkTypes" 
                                                                    :key="type.code" 
                                                                    :value="type.code">
                                                                    {{ type.string_view }}
                                                                </a-select-option>
                                                            </a-select>
                                                        </a-form-model-item>
                                                    </div>
                                                    <a-form-model-item 
                                                        :prop="'plane_items.' + index + '.task'" 
                                                        :ref="'plane_items.' + index + '.task'" 
                                                        :rules="{
                                                            required: true,
                                                            message: $t('field_required'),
                                                            trigger: ['change', 'blur'],
                                                        }"
                                                        class="mb-0 form_item_col form_item_col__2">
                                                        <div class="flex items-center">
                                                            <TaskSelectDrawer 
                                                                v-model="item.task" 
                                                                :placeholder="$t('workplan.old_select_task')"
                                                                :toogleTaskEdit="toogleTaskEdit"
                                                                @change="changeTask($event, index)" />
                                                            <a-button 
                                                                size="large" 
                                                                flaticon 
                                                                :disabled="item.task ? false : true"
                                                                v-tippy="{ 
                                                                    content: $t('workplan.old_open_task'),
                                                                    trigger: 'mouseenter', 
                                                                    hideOnClick: true, 
                                                                    inertia: true, 
                                                                    duration: [200,200], 
                                                                    interactive: false, 
                                                                    placement: 'top'
                                                                }"
                                                                class="n_c_t_btn flex items-center justify-center"
                                                                style="min-width: 33px;max-width: 33px;font-size: 14px;height: 40px;min-height: 40px;padding-left: 0px;padding-right: 0px;"
                                                                icon="fi-rr-arrow-up-right-from-square"
                                                                @click="openTask(item.task.id)" />
                                                            <a-button 
                                                                ref="addTaskBtn"
                                                                size="large" 
                                                                flaticon 
                                                                v-tippy="{ 
                                                                    content: $t('workplan.old_add_task'),
                                                                    trigger: 'mouseenter', 
                                                                    hideOnClick: true, 
                                                                    inertia: true, 
                                                                    duration: [200,200], 
                                                                    interactive: false, 
                                                                    placement: 'top'
                                                                }"
                                                                class="n_t_btn flex items-center justify-center"
                                                                style="min-width: 33px;max-width: 33px;font-size: 14px;height: 40px;min-height: 40px;padding-left: 0px;padding-right: 0px;"
                                                                icon="fi-rr-plus"
                                                                @click="openAddTask(index)" />
                                                        </div>
                                                    </a-form-model-item>
                                                    <a-form-model-item 
                                                        :prop="'plane_items.' + index + '.duration_plane'" 
                                                        :ref="'plane_items.' + index + '.duration_plane'" 
                                                        class="mb-0 form_item_col form_item_col__3">
                                                        <a-input-number 
                                                            v-model="item.duration_plane" 
                                                            size="large" 
                                                            :min="0"
                                                            :step="0.5"
                                                            :max="100"
                                                            class="w-full" 
                                                            :placeholder="$t('workplan.old_plan_hours')"
                                                            @change="taskChange(index, item)" />
                                                    </a-form-model-item>
                                                    <a-form-model-item 
                                                        :prop="'plane_items.' + index + '.duration_fact'" 
                                                        :ref="'plane_items.' + index + '.duration_fact'" 
                                                        :rules="(daily && !item.add && !editedDaily) ? {
                                                            required: true,
                                                            message: $t('field_required'),
                                                            trigger: ['change', 'blur']
                                                        } : null"
                                                        class="mb-0 form_item_col form_item_col__4">
                                                        <a-input-number 
                                                            v-model="item.duration_fact" 
                                                            size="large"
                                                            :min="0"
                                                            :step="0.5"
                                                            :max="100"
                                                            class="w-full" 
                                                            :placeholder="$t('workplan.old_fact_hours')"
                                                            @change="taskChange(index, item)" />
                                                    </a-form-model-item>
                                                    <div class="flex items-center justify-end form_item_col form_item_col__5">
                                                        <a-badge 
                                                            :number-style="{
                                                                backgroundColor: '#4ac428'
                                                            }"
                                                            :dot="item.description.length ? true : false">
                                                            <a-button 
                                                                flaticon
                                                                type="ui"
                                                                ghost
                                                                shape="circle"
                                                                @click="addComment(index)"
                                                                icon="fi-rr-comment-alt" />
                                                        </a-badge>
                                                        <a-modal
                                                            v-model="item.commentVisible"
                                                            :width="600"
                                                            destroyOnClose
                                                            :title="$t('workplan.old_work_done_desc')"
                                                            dialogClass="task-work-time-modal"
                                                            @afterVisibleChange="commentVisibleChange($event)">
                                                            <div class="comment_wrapper">
                                                                <div v-if="isCompleted && !isEdit" class="comment_desc_text">
                                                                    {{ item.description }}
                                                                </div>
                                                                <template v-else>
                                                                    <div class="textarea_wrapper">
                                                                        <a-textarea
                                                                            v-model="item.description"
                                                                            ref="commentRef"
                                                                            class="textarea_input"
                                                                            :maxLength="commentMaxCount"
                                                                            :autoFocus="item.commentVisible"
                                                                            :placeholder="$t('workplan.old_work_desc')"
                                                                            @input="adjustHeight"
                                                                            @change="handleCommentChange($event, index, item)" />
                                                                        <div class="description_length">
                                                                            {{item.description.length}}/{{ commentMaxCount }}
                                                                        </div>
                                                                    </div>
                                                                </template>
                                                            </div>
                                                            <template slot="footer">
                                                                <div class="flex items-center justify-between pt-2">
                                                                    <div class="flex items-center">
                                                                        <a-button 
                                                                            type="ui_ghost" 
                                                                            @click="closeComment(index, item)">
                                                                            {{ $t('workplan.close') }}
                                                                        </a-button>
                                                                        <a-checkbox v-model="item.is_result" class="ml-3" @change="taskChange(index, item)">
                                                                            {{ $t('workplan.old_not_count') }}
                                                                        </a-checkbox>
                                                                    </div>
                                                                </div>
                                                            </template>
                                                        </a-modal>
                                                        <div 
                                                            v-if="(!isCompleted || isEdit) && form.plane_items.length > 1" 
                                                            class="item_delete">
                                                            <a-button 
                                                                type="ui" 
                                                                class="text_red"
                                                                flaticon
                                                                ghost
                                                                :loading="item.dLoading"
                                                                shape="circle"
                                                                icon="fi-rr-trash"
                                                                @click="deleteItem(index, item)" />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </a-form-model>
                                </div>
                                <div v-if="(!isCompleted || isEdit)" class="body_block__footer">
                                    <a-button 
                                        type="link" 
                                        class="flex items-center px-0"
                                        @click="addTask()">
                                        <div class="flex items-center">
                                            <i class="fi fi-rr-plus-small mr-1" />
                                            {{ $t('workplan.old_add_task') }}
                                        </div>
                                    </a-button>
                                </div>
                            </div>
                            <div class="body_block body_block__events">
                                <div 
                                    class="body_block__head"
                                    :style="isEventsScrolled && 'box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.02), 0px 3px 4px rgba(0, 0, 0, 0.08);'">
                                    <div class="block_title">{{ $t('workplan.tab_events') }}</div>
                                </div>
                                <div 
                                    ref="eventsList" 
                                    class="body_block__body"
                                    @scroll="eventsListScroll">
                                    <a-spin 
                                        :spinning="eventsLoading" 
                                        class="w-full">
                                        <div v-if="!events.length" class="empty_events">
                                            {{ $t('workplan.no_events') }}
                                        </div>
                                        <div 
                                            v-for="event in events" 
                                            :key="event.id"  
                                            class="flex">
                                            <div 
                                                class="event_item flex items-center"
                                                @click="openEvent(event.id)">
                                                <i class="fi fi-rr-clock mr-2" />
                                                <span :class="event.is_finished && 'line-through'">
                                                    <template v-if="event.all_day">{{ $t('calendar.all_day') }}</template>
                                                    <template v-else>
                                                        {{ $moment(event.start_at).format('HH:mm') }} 
                                                        <template v-if="event.end_at">- {{ $moment(event.end_at).format('HH:mm') }}</template>
                                                    </template>
                                                    {{ event.name }}
                                                </span>
                                            </div>
                                        </div>
                                    </a-spin>
                                </div>
                                <div v-if="!isCompleted" class="body_block__footer">
                                    <a-button 
                                        type="link" 
                                        class="flex items-center px-0"
                                        @click="addEvent()">
                                        <div class="flex items-center">
                                            <i class="fi fi-rr-plus-small mr-1" />
                                            {{ $t('workplan.old_create_event') }}
                                        </div>
                                    </a-button>
                                </div>
                            </div>
                            <div v-if="checkDailyComment" class="body_block body_block__comment">
                                <div v-if="isCompleted && !isEdit" class="comment_desc_text">
                                    {{ form.description }}
                                </div>
                                <a-textarea
                                    v-else
                                    v-model="form.description"
                                    :placeholder="$t('workplan.comment')"
                                    @change="handleDeilyCommentChange"
                                    :auto-size="{ minRows: 2, maxRows: 5 }"/>
                                <div v-if="!isCompleted || isEdit" class="comment_length">
                                    {{ form.description.length }}/{{ descriptionMaxCount }}
                                </div>
                            </div>
                        </div>
                        <div class="wp_wrapper__footer flex items-center justify-between">
                            <div class="flex items-center">
                                <a-button 
                                    v-if="!isCompleted || isEdit"
                                    type="primary" 
                                    :disabled="loading"
                                    class="px-6 mr-4"
                                    :size="full ? 'large' : 'default'"
                                    :loading="submitLoading"
                                    @click="dailyHandle()">
                                    <template v-if="editedDaily || isEdit">
                                        {{ $t('workplan.old_save_changes') }}
                                    </template>
                                    <template v-else>
                                        {{ daily ? $t('workplan.old_finish_day') : startDailyText }}
                                    </template>
                                </a-button>
                                <div 
                                    v-if="daily && totalDurationFact > 0" 
                                    class="work_hours">
                                    <span>{{ $t('workplan.old_worked') }}</span> {{ totalDurationFact }} {{ $t('workplan.hour_letter') }}
                                </div>
                            </div>
                        </div>
                    </div>
                </a-spin>
            </template>
        </a-popover>
    </div>
</template>

<script>
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
//import DSelect from '@apps/DrawerSelect/Select.vue'
const dateFormat = "YYYY-MM-DD"
import { dailyGenerate, taskFields } from './utils.js'
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
import { onKeyStroke } from '@vueuse/core'
import { hideAll } from 'tippy.js'
import { errorHandler } from '@/utils/index.js'
//let editTimer;
//let addTimer;
export default {
    components: {
        //DSelect,
        TaskSelectDrawer: () => import('./TaskSelectDrawer.vue')
    },
    data() {
        return {
            fastTaskForm: {
                name: ""
            },
            commentMaxCount: 1024,
            descriptionMaxCount: 500,
            locale,
            full: false,
            currentOrg: null,
            orgLoading: false,
            fastTaskLoading: false,
            emptyDay: false,
            isTaskScrolled: false,
            isEventsScrolled: false,
            visible: false,
            selectedDay: this.$moment(),
            commentVisible: false,
            loading: false,
            daily: null,
            taskWorkTypes: [],
            taskWorkTypesLoading: false,
            submitLoading: false,
            eventsLoading: false,
            descLoading: false,
            taskEdit: false,
            isDescriptionChange: false,
            addIndex: 0,
            form: {
                description: "",
                plane_items: []
            },
            events: [],
            observer: null,
            dailyWorkRecords: {},
            lastLoadedMonth: null,
            isEdit: false
        }
    },
    watch: {
        visible(val) {
            if (val) {
                this.createMask()
            } else {
                if(this.form.plane_items?.length) {
                    this.form.plane_items.forEach((item, index) => {
                        if(item.commentVisible)
                            this.$set(this.form.plane_items[index], 'commentVisible', false)
                    })
                }
                this.commentVisible = false
                this.removeMask()
            }
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isSelectedDayToday() {
            return this.selectedDay.isSame(this.$moment(), 'day')
        },
        startDailyText() {
            return this.isSelectedDayToday ? this.$t('workplan.old_start_day') : this.$t('workplan.old_fill_day')
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        popoverStyle() {
            if(this.windowWidth >= 1100) {
                return {
                    width: '500px'
                }
            }
            return {}
        },
        checkDailyComment() {
            if(this.daily) {
                if(this.isCompleted)
                    return this.form.description ? true : false
                return true
            }
            return false
        },
        isTodaySelected() {
            return this.selectedDay.isSame(this.$moment(), 'day')
        },
        totalDurationFact() {
            return Math.round(this.form.plane_items.reduce((sum, item) => {
                const value = parseFloat(item.duration_fact) || 0;
                return sum + value;
            }, 0) * 10) / 10;
        },
        editedDaily() {
            if(this.daily) {
                const filter = this.form.plane_items.filter(f => f.edited || f.add)
                return (filter.length || this.isDescriptionChange || this.isEdit) ? true : false
            }
            return false
        },
        isCompleted() {
            if(this.daily?.status?.code === 'completed')
                return true
            return false
        },
    },
    methods: {
        async edit() {
            this.isEdit = true
        },
        getCurrentStyle(current, today) {
            const dateKey = current.format('YYYY-MM-DD')
            const isSelected = current.isSame(this.selectedDay, 'day')
            
            if (isSelected) {
                return {}
            }
            
            if (this.dailyWorkRecords[dateKey]) {
                const dateInfo = this.dailyWorkRecords[dateKey]
                if (dateInfo.status === 'in_work') {
                    return { backgroundColor: '#f9f0ff', color: '#722ed1' }
                } else if (dateInfo.status === 'completed') {
                    return { backgroundColor: '#e6efe3', color: '#368225' }
                }
            }
            
            return {}
        },
        tippyContent(current) {
            const dateKey = current.format('YYYY-MM-DD')
            if (this.dailyWorkRecords[dateKey]) {
                const dateInfo = this.dailyWorkRecords[dateKey]
                if (dateInfo.status === 'in_work') {
                    return this.$t('workplan.old_current_day')
                } else if (dateInfo.status === 'completed') {
                    return this.$t('workplan.old_day_completed_hours', { hours: dateInfo.description })
                }
            }
        },
        adjustHeight(event) {
            const textarea = event.target;
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
        openProfile() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.my_profile = 'open'
            query.menu_page = 'setting'
            if(!this.$route.query.my_profile) {
                this.$router.push({query})
            }
        },
        commentVisibleChange(vis) {
            if (vis) {
                this.$nextTick(() => {
                    const el = (this.$refs['commentRef'] && this.$refs['commentRef'].length) ? this.$refs['commentRef'][0].$el : undefined
                    if (el) {
                        setTimeout(() => {
                            el.style.height = 'auto'
                            const maxHeight = window.innerHeight - 100
                            el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`
                            el.focus ? el.focus() : el.dispatchEvent(new Event('focus'))
                        }, 0)
                    }
                })
            } else {
                if (this.taskEdit) {
                    this.toogleTaskEdit(false)
                }
            }
        },
        openAddTask(index) {
            hideAll({duration: 0});
            this.toogleTaskEdit(true)
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            eventBus.$emit('add_task_modal', {
                task_type: 'task',
                isWorkPlan: true,
                planeIndex: index
            })
        },
        addEvent() {
            this.taskEdit = true
            eventBus.$emit('open_event_form', 
                this.selectedDay.format('YYYY-MM-DD'), 
                this.selectedDay.format('YYYY-MM-DD'), 
                null, 
                null, 
                'default',
                true)
        },
        changeTask(value, index) {
            this.$set(this.form.plane_items[index], 'edited', true)
        },
        toogleTaskEdit(value) {
            this.taskEdit = value
        },
        changeSelectTask(task) {
            const taskObj = {
                ...task,
                string_view: `${task.counter} ${task.name}`
            }
            const findRow = () => {
                const newIndex = this.form.plane_items.length-1
                if(this.form.plane_items[newIndex]) {
                    this.form.plane_items[newIndex].task = task.id
                    this.$nextTick(() => {
                        this.$refs.taskSelectRef[newIndex].pushListData(taskObj)
                    })
                }
            }

            this.addTask()
            setTimeout(() => {
                findRow()
            }, 500)
        },
        openTask(id) {
            this.toogleTaskEdit(true)
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = id
            if(!this.$route.query.task) {
                //this.visible = false
                this.$router.push({query})
            }
        },
        timeFormat(value) {
            return value % 1 === 0 ? Math.floor(value) : value
        },
        async addItem(task) {
            this.submitLoading = true
            const payload = {
                plane: this.daily.id,
                task: task.id
            }
            try {
                await this.$http.post(`/personal_planes/item/`, payload)
                this.$message.success(this.$t('workplan.old_task_added_to_plan', { date: this.$moment(this.selectedDay).format('DD.MM.YYYY') }))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.submitLoading = false
            }
        },
        async getDailyWorkRecords(startDate, endDate) {
            const currentMonth = this.$moment(startDate).format('YYYY-MM')
            if (this.lastLoadedMonth === currentMonth) {
                return
            }
            
            this.loading = true
            try {
                const { data } = await this.$http.get('/personal_planes/days/', {
                    params: {
                        start_date: startDate,
                        end_date: endDate
                    }
                })
                this.dailyWorkRecords = data
                this.lastLoadedMonth = currentMonth
            } catch (error) {
                this.lastLoadedMonth = null
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        async onOpenChange(open) {
            if (open) {
                await this.$nextTick()
                this.$nextTick(() => {
                    const panel = this.$refs.workPlanPopWrap.querySelector('.ant-calendar')
                    const prevMonth = panel.querySelector('.ant-calendar-prev-month-btn')
                    const nextMonth = panel.querySelector('.ant-calendar-next-month-btn')
                    const prevYear = panel.querySelector('.ant-calendar-prev-year-btn')
                    const nextYear = panel.querySelector('.ant-calendar-next-year-btn')

                    prevMonth?.addEventListener('click', this.onMonthChange)
                    nextMonth?.addEventListener('click', this.onMonthChange)
                    prevYear?.addEventListener('click', this.onMonthChange)
                    nextYear?.addEventListener('click', this.onMonthChange)

                    this.observer = { prevMonth, nextMonth, prevYear, nextYear }
                })
                this.onMonthChange()
            } else {
                this.removeMonthListeners()
            }
        },
        onMonthChange() {
            this.$nextTick(() => {
                const label = this.$refs.workPlanPopWrap.querySelector('.ant-calendar-my-select')?.textContent.trim()
                if (!label) return

                const parsed = this.$moment(label, 'MMM.YYYY', 'ru')
                if (parsed.isValid()) {
                    const startDate = parsed.clone().startOf('month').format('YYYY-MM-DD')
                    const endDate = parsed.clone().endOf('month').format('YYYY-MM-DD')
    
                    this.getDailyWorkRecords(startDate, endDate)
                }
            })
        },
        removeMonthListeners() {
            if (!this.observer) return
            const { prevMonth, nextMonth, prevYear, nextYear } = this.observer
            prevMonth?.removeEventListener('click', this.onMonthChanged)
            nextMonth?.removeEventListener('click', this.onMonthChanged)
            prevYear?.removeEventListener('click', this.onMonthChanged)
            nextYear?.removeEventListener('click', this.onMonthChanged)
            this.observer = null
        },
        onPanelChange(value, mode) {
            if (mode === 'date') {
                const startDate = value.clone().startOf('month').format('YYYY-MM-DD');
                const endDate = value.clone().endOf('month').format('YYYY-MM-DD');
                this.getDailyWorkRecords(startDate, endDate)
            }
        },
        createDailyAndAddItem(task) {
            try {
                this.submitLoading = true
                const queryData = {
                    plane_date: this.selectedDay.format(dateFormat),
                    plane_items: [
                        {
                            task: task.id
                        }
                    ]
                }
                this.$http.post('/personal_planes/', queryData)
                this.$message.success(this.$t('workplan.old_task_added_to_plan', { date: this.$moment(this.selectedDay).format('DD.MM.YYYY') }))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.submitLoading = false
            }
        },
        disabledFutureDates(current) {
            return current && current.isAfter(this.$moment().endOf("day"))
        },
        checkTaskComment(item) {
            if(this.daily) {
                if(this.isCompleted) {
                    return item.description ? true : false
                }
                return true
            }
            return true
        },
        handleDeilyCommentChange(event) {
            this.isDescriptionChange = true
            const value = event.target.value.slice(0, this.descriptionMaxCount)
            this.$set(this.form, 'description', value)
        },
        handleCommentChange(event, index, item) {
            const value = event.target.value.slice(0, this.commentMaxCount)
            this.$set(this.form.plane_items[index], 'description', value)
            this.taskChange(index, item)
        },
        taskChange(index, item) {
            if(this.daily && !this.checkEdited())
                this.clearFormValues(index)
            if(!item.add)
                this.$set(this.form.plane_items[index], 'edited', true)
        },
        openEvent(id) {
            this.visible = false
            let query = Object.assign({}, this.$route.query)
            if(query.event && Number(query.event) !== id || !query.event) {
                query.event = id
                this.$router.push({query})
            }
        },
        async getEvents() {
            try {
                this.eventsLoading = true
                const startDate = this.selectedDay.set('hour', 0).set('minute', 1).set('second', 1).set('millisecond', 0).toISOString(true),
                    endDate = this.selectedDay.set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59).toISOString(true),
                    params = {
                        start: startDate,
                        end: endDate
                    }
                const { data } = await this.$http.get('/calendars/events/top/', { params })
                if(data) {
                    this.events = data
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.eventsLoading = false
            }
        },
        updateDailyWorkRecords(data) {
            const record = this.dailyWorkRecords[data?.plane_date]
            if (record) {
                record.status = data.status.code
                record.description = Math.round(data.plane_items.reduce((sum, item) => {
                    const value = parseFloat(item.duration_fact) || 0;
                    return sum + value;
                }, 0) * 10) / 10;
            }
        },
        dailyHandle() {
            this.$refs.ruleForm.validate((valid, errors) => {
                if (valid) {
                    if(this.daily && !this.editedDaily && !this.isEdit)
                        this.completedDaily()
                    else
                        this.dailySave()
                } else {
                    return false
                }
            })
        },
        completedDaily() {
            this.toogleTaskEdit(true)
            this.$confirm({
                title: this.$t('workplan_end'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onCancel: () => {
                    this.toogleTaskEdit(false)
                },
                onOk: async () => {
                    try {
                        this.submitLoading = true
                        const { data } = await this.$http.post(`/personal_planes/${this.daily.id}/complete/`)
                        if(data) {
                            this.daily = data
                            this.isDescriptionChange = false
                            this.updateDailyWorkRecords(data)
                        }
                    } catch(error) {
                        this.toogleTaskEdit(false)
                        errorHandler({error})
                    } finally {
                        this.toogleTaskEdit(false)
                        this.submitLoading = false
                    }
                }
            })
        },
        async dailySave() {
            try {
                this.submitLoading = true
                const queryData = {...this.form}
                queryData.plane_date = this.selectedDay.format('YYYY-MM-DD')
                if(queryData.plane_items?.length) {
                    queryData.plane_items = queryData.plane_items.map(item => {
                        return {
                            ...item,
                            task: item.task?.id || null,
                            duration_fact: item.duration_fact || 0,
                            duration_plane: item.duration_plane || 0,
                            is_result: item.is_result
                        }
                    })
                }
                if(this.editedDaily) {
                    const { data } = await this.$http.put(`/personal_planes/${this.daily.id}/`, queryData)
                    if(data) {
                        this.daily = data
                        this.form = dailyGenerate(data)
                        this.isDescriptionChange = false
                        this.isEdit = false
                        this.$message.success(this.$t('workplan.old_changes_saved'))
                    }
                } else {
                    const { data } = await this.$http.post('/personal_planes/', queryData)
                    if(data) {
                        this.daily = data
                        this.form = dailyGenerate(data)
                        this.isDescriptionChange = false
                        this.$message.success(this.$t('workplan.old_changes_saved'))
                    }
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.submitLoading = false
            }
        },
        async getTaskWorkTypes() {
            try {
                this.taskWorkTypesLoading = true
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'tasks.TaskWorkTypeModel',
                        filters: JSON.stringify({work_type_task_type__task_type_id: 'task'})
                    }
                })
                if(data?.selectList) {
                    this.taskWorkTypes = data.selectList
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.taskWorkTypesLoading = false
            }
        },
        changeDate(e) {
            if(this.selectedDay.format(dateFormat) !== e.format(dateFormat)) {
                this.selectedDay = e
                this.getOtherDaily()
                this.isEdit = false
                this.$nextTick(() => {
                    this.$refs.taskList.scrollTop = 0
                    this.$refs.eventsList.scrollTop = 0
                })
            }
        },
        taskListScroll() {
            const taskList = this.$refs.taskList
            if (taskList.scrollTop > 0) {
                if (!this.isTaskScrolled) {
                    this.isTaskScrolled = true
                }
            } else {
                if (this.isTaskScrolled) {
                    this.isTaskScrolled = false
                }
            }
        },
        eventsListScroll() {
            const eventsList = this.$refs.eventsList
            if (eventsList.scrollTop > 0) {
                if (!this.isEventsScrolled) {
                    this.isEventsScrolled = true
                }
            } else {
                if (this.isEventsScrolled) {
                    this.isEventsScrolled = false
                }
            }
        },
        async addDailyComment() {
            this.commentVisible = false
            if(this.daily && !this.isCompleted) {
                try {
                    this.submitLoading = true
                    await this.$http.patch(`/personal_planes/${this.daily.id}/`, {
                        description: this.form.description
                    })
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.submitLoading = false
                }
            }
        },
        closeComment(index, item) {
            //this.$set(this.form.plane_items[index], 'description', item.oldDescription)
            this.$set(this.form.plane_items[index], 'commentVisible', false)
        },
        addComment(index) {
            this.toogleTaskEdit(true)
            this.$set(this.form.plane_items[index], 'commentVisible', true)
        },
        taskScrollBottom() {
            this.$nextTick(() => {
                const taskList = this.$refs.taskList
                if (taskList)
                    taskList.scrollTop = taskList.scrollHeight - taskList.clientHeight
            })
        },
        deleteItem(index, item) {
            if(item.add)
                this.$delete(this.form.plane_items, index)
            else {
                this.toogleTaskEdit(true)
                this.$confirm({
                    title: this.$t('workplan_task_delete'),
                    cancelText: this.$t('cancel'),
                    okText: this.$t('remove'),
                    onCancel: () => {
                        this.toogleTaskEdit(false)
                    },
                    onOk: async () => {
                        try {
                            this.$set(this.form.plane_items[index], 'dLoading', true)
                            await this.$http.delete(`/personal_planes/item/${item.id}/`)
                            this.$delete(this.form.plane_items, index)
                        } catch(error) {
                            this.toogleTaskEdit(false)
                            errorHandler({error})
                        } finally {
                            this.toogleTaskEdit(false)
                            if(this.form.plane_items[index])
                                this.$set(this.form.plane_items[index], 'dLoading', false)
                        }
                    }
                })
            }
        },
        checkEdited() {
            const filter = [...this.form.plane_items].filter(f => f.edited || f.add)
            return filter.length ? true : false
        },
        clearFormValues(index) {
            this.$refs.ruleForm.clearValidate([
                `plane_items.${index}.work_type`,
                `plane_items.${index}.task`,
                `plane_items.${index}.duration_plane`,
                `plane_items.${index}.duration_fact`
            ])
        },
        addTask() {
            if(this.daily && !this.checkEdited()) {
                this.form.plane_items.forEach((item, index) =>{
                    this.clearFormValues(index)
                })
            } 
            this.form.plane_items.push({
                key: Date.now(),
                work_type: null,
                dLoading: false,
                loading: false,
                task: null,
                add: true,
                duration_plane: null,
                duration_fact: null,
                commentVisible: false,
                description: "",
                is_result: false
            })
            setTimeout(() => {
                this.taskScrollBottom()
            }, 100)
        },
        getPopupContainer() {
            return this.$refs.workPlanPopWrap
        },
        clearDaily() {
            this.daily = null
            this.selectedDay = this.$moment()
        },
        clearForm(vis = false) {
            this.isEventsScrolled = false
            this.isTaskScrolled = false
            this.commentVisible = false
            this.form = {
                description: "",
                plane_items: vis ? [] : [
                    {
                        key: 1,
                        work_type: null,
                        task: null,
                        duration_plane: null,
                        duration_fact: null,
                        commentVisible: false,
                        description: "",
                        is_result: false
                    }
                ]
            }
        },
        visibleChange(vis) {
            if(!vis) {
                this.isDescriptionChange = false
                this.lastLoadedMonth = null
                this.removeMonthListeners()
            }
            if(this.taskEdit) {
                this.visible = true
            } else {
                this.visible = vis
                if(!vis) {
                    this.isDescriptionChange = false
                    this.emptyDay = false
                    this.messageDefaultSetting()
                    this.clearDaily()
                    this.clearForm(true)
                    this.addIndex = 0
                    if(this.taskEdit)
                        this.taskEdit = false
                } else {
                    this.getMyOrganization()
                    this.getDaily(false)
                    this.getTaskWorkTypes()
                }
            }
        },
        messageDefaultSetting() {
            this.$message.config({
                maxCount: 3,
                getContainer: () => document.body
            })
            this.$message.destroy()
        },
        messageConfig() {
            this.$message.config({
                maxCount: 1,
                getContainer: this.getPopupContainer
            })
        },
        async getOtherDaily() {
            try {
                this.loading = true

                const { data } = await this.$http.get('/personal_planes/my/calendar/', {
                    params: { plane_date: this.selectedDay.format(dateFormat) }
                })

                if (data) {
                    this.emptyDay = false
                    this.daily = data
                    this.form = dailyGenerate(data)
                } else {
                    this.emptyDay = !this.selectedDay.isSame(this.$moment(), 'day')
                    this.daily = null
                    this.clearForm()
                }

                this.getEvents()
            } catch (error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        async getDaily(change = false, getEvents = true) {
            try {
                this.loading = true

                const { data } = await this.$http.get('/personal_planes/my/current/', {
                    params: { plane_date: this.selectedDay.format(dateFormat) }
                })

                if (data) {
                    const isInWork = data.status?.code === 'in_work'
                    if (change && isInWork) {
                        this.messageConfig();
                        this.$message.warning({
                            content: this.$t('workplan.old_finish_work_day'),
                            onClose: this.messageDefaultSetting
                        })
                    }
                    if (isInWork)
                        this.selectedDay = this.$moment(data.plane_date)

                    this.daily = data
                    this.form = dailyGenerate(data)
                } else {
                    if (this.daily) this.clearDaily()
                    this.clearForm()
                }
                if (getEvents) this.getEvents()
            } catch (error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        createMask() {
            if (!document.querySelector('.popover_mask')) {
                const mask = document.createElement('div')
                mask.className = 'popover_mask'
                mask.addEventListener('click', this.closePopover)
                document.body.appendChild(mask)
            }
        },
        removeMask() {
            const mask = document.querySelector('.popover_mask')
            if (mask) {
                mask.removeEventListener('click', this.closePopover)
                document.body.removeChild(mask)
            }
        },
        closePopover() {
            this.visible = false
        },
        async getMyOrganization() {
            try {
                this.orgLoading = true
                const { data } = await this.$http.get('/users/current_contractor/detail/')
                if(data) {
                    this.currentOrg = data
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.orgLoading = false
            }
        },
        deleteEventHandler(id) {

        }
    },
    mounted() {
        onKeyStroke(['Escape'], () => {
            if(!this.full && this.visible)
                this.visible = false
            if(this.full && this.visible)
                this.full = false
        })
        onKeyStroke('w', (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault()
                if(!this.visible) {
                    this.visible = true
                    this.getMyOrganization()
                    this.getDaily(false)
                    this.getTaskWorkTypes()
                }
            }
        })
        onKeyStroke('f', (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault()
                if(this.visible && !this.full)
                    this.full = true
            }
        })
        eventBus.$on('add_task_in_my_work_plan', task => {
            this.getDaily(false, false)
                .then(async () => {
                    if (this.daily && this.daily.status.code === 'in_work') {
                        this.addItem(task)
                    } else if(this.daily && this.daily.status.code === 'completed') {
                        this.$message.error(this.$t('workplan.old_day_plan_completed', { date: this.$moment(this.selectedDay).format('DD.MM.YYYY') }))
                    } else if(!this.daily) {
                        this.createDailyAndAddItem(task)
                    }
                })
                .catch(e => {
                    console.log(e)
                    this.$message.error(this.$t('workplan.old_day_plan_load_error'))
                })
                .finally(() => {
                    this.visibleChange(false)
                })
        })
        eventBus.$on('task_drawer_close', () => {
            if(this.taskEdit)
                this.taskEdit = false
        })
        eventBus.$on('close_add_task_modal', () => {
            this.taskEdit = false
            hideAll({duration: 0});
        })
        eventBus.$on(`TASK_CREATED_task`, task => {
            const taskObj = {
                ...task,
                string_view: `${task.counter} ${task.name}`
            }

            if(this.form.plane_items[this.addIndex]) {
                this.form.plane_items[this.addIndex].task = task.id
                this.$nextTick(() => {
                    this.$refs.taskSelectRef[this.addIndex].pushListData(taskObj)
                })
            }
        })
        eventBus.$on('header_event_update', () => {
            this.getEvents()
        })
        eventBus.$on('delete_event', id => {
            this.deleteEventHandler(id)
        })
        eventBus.$on('add_event_close_drawer', () => {
            if(this.taskEdit)
                this.taskEdit = false
        })
        eventBus.$on('work_day_add_task', data => {
            if(typeof data.planeIndex === 'number') {
                hideAll({duration: 0})
                this.$set(this.form.plane_items[data.planeIndex], 'edited', true)
                this.$set(this.form.plane_items[data.planeIndex], 'task', data)
                if(this.daily) {
                    this.dailyHandle()
                } else {
                    this.$message.info(this.$t('workplan.old_start_day_for_save'))
                }
            }
        })
        eventBus.$on('close_show_drawer_task', () => {
            if(this.taskEdit)
                this.taskEdit = false
        })
        eventBus.$on('OPEN_EDIT_TASK', () => {
            if(this.taskEdit)
                this.taskEdit = false
            this.visible = false
        })
    },
    beforeDestroy() {
        eventBus.$off('add_task_in_my_work_plan')
        eventBus.$off('OPEN_EDIT_TASK')
        eventBus.$off('close_show_drawer_task')
        eventBus.$off('work_day_add_task')
        eventBus.$off('close_add_task_modal')
        eventBus.$off('add_event_close_drawer')
        eventBus.$off('task_drawer_close')
        eventBus.$off('TASK_CREATED_task')
        eventBus.$off('header_event_update')
        eventBus.$off('delete_event')
        this.removeMask()
        this.removeMonthListeners()
    }
}
</script>

<style lang="scss" scoped>
.work_btn{
    min-height: 32px;
}
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}
.fast_task_form{
    min-width: 400px;
}
.n_t_btn{
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
.n_c_t_btn{
    border-radius: 0px;
    border-right: 0px;
}
.t_select{
    max-height: 40px;
    &::v-deep{
        .ant_select{
            .ant-select-selection{
                border-right: 0px;
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
            }
        }
    }
}
.task_label{
    cursor: pointer;
    span{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &:hover{
        span{
            color: var(--blue);
        }
    }
}
.comment_desc_text{
    word-break: break-word;
    max-height: 150px;
    overflow-y: auto;
}
.comment_length{
    font-size: 12px;
    opacity: 0.5;
    padding: 4px;
    text-align: end;
}
.comment_desc{
    &:not(.validated){
        &::v-deep{
            .has-error{
                .ant-btn{
                    border-color: #f5222d;
                    color: #f5222d;
                }
            }
        }
    }
}
.empty_events{
    opacity: 0.6;
}
.comment_wrapper{
    min-width: 300px;
}
.item_delete{
    &::v-deep{
        .ant-btn{
            border: 0px;
            box-shadow: initial;
        }
    }
}
.comlited-deyly {
    td {
        padding: 4px 5px;
    }
    .min-width {
        width: min-content;
        text-wrap: nowrap;
    }
}
.form_item{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .s_work_type{
        max-height: 40px;
    }
    &__row{
        display: flex;
        align-items: center;
        position: relative;
        margin-left: -5px;
        margin-right: -5px;
        .form_item_col{
            padding-left: 5px;
            padding-right: 5px;
            &__1{
                flex: 0 0 auto;
                width: 27%;
            }
            &__2{
                flex: 0 0 auto;
                width: 41%;
            }
            &__3{
                flex: 0 0 auto;
                width: 11%;
            }
            &__4{
                flex: 0 0 auto;
                width: 11%;
            }
            &__5{
                flex: 0 0 auto;
                width: 10%;
            }
        }
    }
    /*&.long{
        grid-template-columns: 10px 1fr 1fr 100px 100px 60px;
    }*/
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &::v-deep{
        .select_item{
            &:not(.selected){
                .ant-select-selection__placeholder{
                    display: block!important;
                }
            }
        }
        .ant-form-explain{
            display: none;
        }
    }
}
.wp_wrapper{
    min-width: 700px;
    max-width: 800px;
    color: #000;
    @media (min-width: 900px) {
        min-width: 830px;
    }
    &__header{
        padding: 15px;
        h4{
            font-weight: 400;
            font-size: 16px;
            line-height: 16px;
        }
    }
    &__body{
        padding: 0 15px;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
        .body_block{
            background: #F8F8F8;
            border-radius: 4px;
            &:not(:last-child){
                margin-bottom: 10px;
            }
            &.body_block__events{
                .body_block__body{
                    max-height: 90px;
                }
            }
            &.body_block__comment{
                padding-top: 15px;
                padding-left: 15px;
                padding-right: 15px;
            }
            &.body_block__tasks{
                .body_block__body{
                    max-height: 250px;
                }
            }
            &__head{
                padding: 15px 15px 10px 15px;
                transition: all 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
                .block_title{
                    margin: 0px;
                }
            }
            &__body{
                padding: 0 15px;
                overflow-y: auto;
                &:last-child{
                    padding-bottom: 15px;
                }
            }
            &__footer{
                padding: 5px 15px 15px 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .event_item{
                cursor: pointer;
                user-select: none;
                span{
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                }
                &:hover{
                    span{
                        color: var(--blue);
                    }
                }
                &:not(:last-child){
                    margin-bottom: 6px;
                }
            }
        }
    }
    &__footer{
        padding: 15px;
        .work_hours{
            span{
                opacity: 0.6;
            }
        }
    }
    &::v-deep{
        .ant-message{
            position: absolute;
        }
    }
}
.work_plan_btn {
    &.ant-btn {
        &.ant-btn-primary {
            color: #000;
        }
    }
}
</style>

<style lang="scss">
.task-work-time-modal {
    textarea.ant-input {
        min-height: 75px;
        max-height: calc(100vh - 465px);
    }
}
.work_plan_popover{
    z-index: 900;
    & > .ant-popover-content > .ant-popover-arrow{
        display: none;
    }
    & > .ant-popover-content > .ant-popover-inner > div > .ant-popover-inner-content{
        padding: 0px;
    }
    &.full_popover{
        position: fixed;
        top: 15px!important;
        left: 15px!important;
        bottom: 15px!important;
        right: 15px!important;
        padding: 0px;
        transform-origin: initial!important;
        .ant-popover-inner > div:not([class]),
        .ant-popover-inner-content,
        .ant-spin-nested-loading,
        .ant-spin-container,
        .ant-popover-inner,
        .ant-popover-content{
            height: 100%;
        }
        .wp_wrapper{
            min-width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            &__body{
                flex-grow: 1;
                max-height: initial!important;
            }
            .body_block{
                &__body{
                    max-height: initial!important;
                    overflow-y: initial!important;
                }
                .form_item_col__1{
                    width: 20%;
                    @media (min-width: 1200px) {
                        width: 15%;
                    }
                }
                .form_item_col__2{
                    width: 40%;
                    @media (min-width: 1200px) {
                        width: 55%;
                    }
                }
                .form_item_col__4,
                .form_item_col__3{
                    width: 15%;
                    @media (min-width: 1200px) {
                        width: 10%;
                    }
                }
            }
        }
    }
}
.plan_comment_popover{
    .ant-popover-arrow{
        display: none;
    }
    .ant-popover-inner-content{
        padding: 15px;
    }
}
.popover_mask {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.3);
    z-index: 899;
}

.day-plan {
    display: grid;
    grid-template-columns: 20px 1fr 74px 74px 30px 30px;
    gap: 10px;
}
</style>
