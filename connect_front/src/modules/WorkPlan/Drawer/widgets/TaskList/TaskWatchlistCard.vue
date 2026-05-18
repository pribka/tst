<template>
    <div class="task_card rounded-lg select-none" :class="collapse && 'task_card_open'">
        <div class="task_card__wrapper cursor-pointer md:flex md:items-center" @click="collapseTask()">
            <div class="w-full truncate">
                <div class="flex items-start justify-between gap-5 mb-2">
                    <div class="flex items-center truncate min-w-0" @click.stop="openTask()">
                        <StatusDropdown :task="task" :storeKey="storeKey" :popupContainer="popupContainer" />
                        <span class="font-semibold truncate task_name" :title="task.name">
                            <span style="color: rgb(136, 136, 136);">#{{ task.counter }}</span> {{ task.name }}
                        </span>
                    </div>
                    <div class="card_actions gap-2 md:gap-3">
                        <i class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                    </div>
                </div>
                <div class="flex items-center flex-wrap gap-x-4 gap-y-1">
                    <RelatedUsers v-if="task.related_users?.length" :relatedUsers="task.related_users" :storeKey="storeKey" />
                    <div class="flex items-center opacity-80">
                        <i class="fi fi-rr-clock mr-1" />
                        {{ $t('workplan.in_work') }} {{ actualDurationDays }}
                    </div>
                    <div class="flex items-center opacity-80">
                        {{ $t('workplan.total_short') }}:<span class="font-semibold ml-1">{{ secondsFormat(task.duration_total_all) }}</span>
                    </div>
                    <div v-if="task.dead_line" class="flex items-center opacity-80">
                        {{ $t('task.dead_line') }}:<span class="font-semibold ml-1">{{ formattedDeadline }}</span>
                    </div>
                </div>
                <div v-if="task.blockers && task.blockers.length || task.has_new_comments" class="flex items-center flex-wrap gap-x-3 md:gap-x-4 gap-y-2 mt-2 text-xs">
                    <transition name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                        <div v-if="task.has_new_comments" class="flex items-center blue_color" @click.stop="openTask(true)">
                            <i class="fi fi-rr-comment-dots mr-1" />
                            {{ $t('workplan.new_comments') }}
                        </div>
                    </transition>
                    <template v-if="task.blockers && task.blockers.length">
                        <div v-for="blocker in task.blockers" :key="blocker.id" :title="blocker.name" class="flex items-center" :style="`color: ${blocker.color};`">
                            <i class="fi fi-rr-exclamation mr-1" />
                            {{ blocker.name }}
                        </div>
                    </template>
                </div>
            </div>
        </div>
        <div v-if="collapse" class="collapse_wrapper">
            <div class="collapse_wrapper__divider" />
            <div class="task_watchlist_edit">
                <div v-if="!canEdit" class="mb-4">
                    <a-alert
                        type="warning"
                        show-icon
                        :message="$t('workplan.task_watchlist_no_edit_rights')" />
                </div>
                <template v-if="canEdit">
                    <div class="task_watchlist_edit__title">
                        <i class="fi fi-rr-exclamation" />
                        <span>{{ $t('workplan.task_watchlist_edit_title') }}</span>
                    </div>
                    <div class="task_watchlist_edit__row">
                        <div class="task_watchlist_edit__label">
                            {{ $t('workplan.task_watchlist_action_label') }}
                        </div>
                        <a-radio-group v-model="form.action" class="task_watchlist_edit__radio_group">
                            <a-radio :value="'snooze'">
                                {{ $t('workplan.task_watchlist_action_snooze') }}
                            </a-radio>
                            <a-radio :value="'complete'">
                                {{ $t('workplan.task_watchlist_action_complete') }}
                            </a-radio>
                            <a-radio :value="'extend'">
                                {{ $t('workplan.task_watchlist_action_extend') }}
                            </a-radio>
                        </a-radio-group>
                    </div>
                </template>
                <div v-if="form.action === 'extend'" class="task_watchlist_edit__row task_watchlist_edit__row_date">
                    <div class="task_watchlist_edit__field task_watchlist_edit__field_date">
                        <div class="task_watchlist_edit__field_label">
                            {{ $t('workplan.task_watchlist_date_label') }}
                        </div>
                        <DatePicker
                            v-model="form.date"
                            size="large"
                            dateFormat="DD.MM.YYYY HH:mm"
                            valueFormat="YYYY-MM-DD HH:mm:ss"
                            :show-time="{ format: 'HH:mm' }"
                            :disabled="!canEdit"
                            :allowClear="false"
                            :disabledBefore="minAvailableDate"
                            :disabledAfter="maxAvailableDate"
                            class="task_watchlist_edit__date_picker"
                            :getCalendarContainer="popupContainer">
                            <template #suffixIcon>
                                <i class="fi fi-rr-calendar" />
                            </template>
                        </DatePicker>
                    </div>
                </div>
                <div class="task_watchlist_edit__form">
                    <div class="task_watchlist_edit__field">
                        <div class="task_watchlist_edit__field_label">
                            {{ $t('workplan.task_watchlist_comment_label') }}
                        </div>
                        <a-textarea
                            v-model="form.comment"
                            :auto-size="commentAutosize"
                            class="task_watchlist_edit__textarea"
                            :class="{ 'is-empty': !form.comment }"
                            :placeholder="$t('workplan.task_watchlist_comment_placeholder')" />
                    </div>
                    <div class="task_watchlist_edit__actions">
                        <a-button
                            type="primary"
                            size="large"
                            :loading="submitLoading"
                            :disabled="submitDisabled"
                            @click.stop="submitForm">
                            {{ $t('workplan.task_watchlist_done') }}
                        </a-button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from '@/config/axios'
import { errorHandler } from '@/utils/index.js'
import { declOfNum, secondsFormat } from '@/utils/utils.js'

export default {
    components: {
        StatusDropdown: () => import('./StatusDropdown.vue'),
        RelatedUsers: () => import('../RelatedUsers.vue'),
        DatePicker: () => import('@/modules/vue2TaskComponent/components/EditDrawer/DatePick')
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        popupContainer: {
            type: Function,
            default: () => document.body
        },
        group: {
            type: String,
            default: 'overdue'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        canEdit() {
            return !!(this.task?.action_info?.edit?.availability ?? this.task?.actions?.edit?.availability)
        },
        minAvailableDate() {
            return this.$moment().startOf('day').format('YYYY-MM-DD HH:mm:ss')
        },
        maxAvailableDate() {
            return ''
        },
        formattedDeadline() {
            if(!this.task.dead_line) return ''
            return this.$moment(this.task.dead_line).format('DD.MM.YYYY HH:mm')
        },
        actualDurationDays() {
            return `${this.task.actual_duration_days} ${declOfNum(this.task.actual_duration_days, [this.$t('workplan.day_one'), this.$t('workplan.day_few'), this.$t('workplan.day_many')])}`
        },
        collapse: {
            get() {
                return this.task.collapse !== undefined ? this.task.collapse : true
            },
            set(value) {
                this.$set(this.task, 'collapse', value)
            }
        },
        submitDisabled() {
            if(this.submitLoading)
                return true

            if(!this.canEdit)
                return !this.form.comment

            if(this.form.action === 'extend' && !this.form.date)
                return true

            return false
        },
        commentAutosize() {
            if(!this.form.comment)
                return false

            return {
                minRows: 1,
                maxRows: 4
            }
        }
    },
    data() {
        return {
            submitLoading: false,
            form: {
                action: 'snooze',
                comment: '',
                date: null
            }
        }
    },
    methods: {
        secondsFormat,
        buildCommentText() {
            const text = (this.form.comment || '').trim()

            if(!text)
                return ''

            const escapedText = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/\n/g, '<br>')

            return `<p>${escapedText}&nbsp;</p>`
        },
        getDeadlineValue() {
            if(!this.form.date)
                return null

            return this.$moment(this.form.date, 'YYYY-MM-DD HH:mm:ss').format()
        },
        resetForm() {
            this.form = {
                action: 'snooze',
                comment: '',
                date: null
            }
        },
        collapseTask() {
            this.collapse = !this.collapse
        },
        async submitForm() {
            if(this.submitDisabled)
                return

            try {
                this.submitLoading = true

                if(!this.canEdit) {
                    const commentText = this.buildCommentText()
                    if(commentText) {
                        await axios.post('/comments/create/', {
                            parent: null,
                            text: commentText,
                            readers: [],
                            attachments: [],
                            mentions: [],
                            related_object: this.task.id,
                            model: 'tasks'
                        })
                    }
                } else {
                    if(this.form.action === 'snooze') {
                        await axios.post(`/tasks/task/${this.task.id}/watchlist_snooze/`)
                    }

                    if(this.form.action === 'complete') {
                        await axios.put(`/tasks/task/${this.task.id}/status/`, {
                            status: 'completed'
                        })
                    }

                    if(this.form.action === 'extend') {
                        await axios.put(`/tasks/task/${this.task.id}/update_deadline/`, {
                            dead_line: this.getDeadlineValue()
                        })
                    }

                    const commentText = this.buildCommentText()
                    if(commentText) {
                        await axios.post('/comments/create/', {
                            parent: null,
                            text: commentText,
                            readers: [],
                            attachments: [],
                            mentions: [],
                            related_object: this.task.id,
                            model: 'tasks'
                        })
                    }
                }

                if(this.canEdit || this.group === 'stalled')
                    this.$emit('reload')

                this.resetForm()
                if(this.canEdit)
                    this.collapse = false
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.submitLoading = false
            }
        },
        openTask(comment = false) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = this.task.id
            if(comment) {
                this.$set(this.task, 'has_new_comments', null)
                query.comment = true
            }
            this.$router.replace({ query })
        }
    }
}
</script>

<style lang="scss" scoped>
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}
.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.task_name{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.collapse_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    @media (min-width: 768px) {
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    &__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
    }
}
.task_card{
    background: #fff;
    width: 100%;
    overflow: hidden;
    .card_actions{
        display: flex;
        align-items: center;
        flex-shrink: 0;
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &__wrapper{
        padding: 15px;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
    &.task_card_open{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
}

.task_watchlist_edit {
    width: 100%;
    overflow: hidden;

    &__title {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        color: #d97706;
        line-height: 1.3;
    }

    &__row {
        display: flex;
        align-items: center;
        gap: 18px;
        flex-wrap: wrap;
        margin-bottom: 18px;
    }

    &__row_date {
        margin-bottom: 10px;
    }

    &__label {
        color: #667085;
    }

    &__radio_group {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }

    &__form {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: end;
    }

    &__field {
        min-width: 0;
        width: 100%;
    }

    &__field_date {
        width: 270px;
    }

    &__field_label {
        color: #98a2b3;
        margin-bottom: 8px;
    }

    &__date_picker {
        width: 100%;
    }

    &__actions {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 10px;

        .ant-btn {
            min-width: 160px;
        }
    }
}

.task_watchlist_edit__textarea {
    &.ant-input{
        min-height: 36px!important;
        height: 36px;
        max-width: 100%;
        resize: vertical;
    }
}

@media (max-width: 992px) {
    .task_watchlist_edit {
        &__row {
            margin-bottom: 16px;
        }

        &__row_date {
            margin-bottom: 16px;
        }

        &__form {
            grid-template-columns: 1fr;
            gap: 16px;
        }

        &__field_date {
            width: 100%;
        }

        &__field_label {
            margin-bottom: 8px;
        }

        &__actions {
            flex-direction: column;
            align-items: stretch;

            .ant-btn {
                width: 100%;
                min-width: 0;
            }
        }
    }
}
</style>
