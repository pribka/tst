<template>
    <a-spin
        v-if="canUseTimer"
        size="small"
        :spinning="loading || actionLoading"
        class="task-timer"
        :class="[
            `task-timer--${variant}`,
            {
                'task-timer--current': isCurrent
            }
        ]">
        <button
            type="button"
            class="task-timer__button"
            :disabled="actionLoading"
            v-tippy
            :content="isCurrent ? $t('task.stop_timer') : $t('task.start_timer')"
            @click="toggleTimer">
            <i
                class="fi task-timer__icon"
                :class="isCurrent ? 'fi-rr-pause' : 'fi-rr-play'" />
            <template v-if="isCurrent">
                <span class="task-timer__label">{{ $t('task.execution') }}:</span>
                <span class="task-timer__value">{{ formattedDuration }}</span>
            </template>
            <span v-else class="task-timer__label">{{ $t('task.start_timer') }}</span>
        </button>
    </a-spin>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

const POLL_INTERVAL = 60 * 60 * 1000
const SOCKET_SYNC_INTERVAL = 60 * 1000

export default {
    name: 'TaskTimer',
    sockets: {
        notify({ data }) {
            if(data?.event_type === 'update_current_work')
                this.fetchTimerState({ silent: true })
        }
    },
    props: {
        task: {
            type: Object,
            default: () => null
        },
        dropActions: {
            type: Object,
            default: () => null
        },
        variant: {
            type: String,
            default: 'footer'
        }
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            durationSeconds: 0,
            isCurrent: false,
            pollIntervalId: null,
            runTimerId: null,
            fetchPromise: null,
            lastFetchAt: 0,
            lastFetchedTaskId: null
        }
    },
    computed: {
        canUseTimer() {
            return Boolean(this.dropActions?.can_use_timer?.availability && this.task?.id)
        },
        formattedDuration() {
            const totalSeconds = Math.max(0, Math.floor(Number(this.durationSeconds) || 0))
            const hours = Math.floor(totalSeconds / 3600)
            const minutes = Math.floor((totalSeconds % 3600) / 60)
            const seconds = totalSeconds % 60

            if (hours > 0) {
                return `${this.pad(hours)}:${this.pad(minutes)}:${this.pad(seconds)}`
            }

            return `${this.pad(minutes)}:${this.pad(seconds)}`
        }
    },
    watch: {
        canUseTimer: {
            immediate: true,
            handler(value) {
                if (value) {
                    this.initTimer()
                } else {
                    this.resetTimerState()
                }
            }
        },
        'task.id'(value, oldValue) {
            if (value && value !== oldValue && this.canUseTimer) {
                this.initTimer()
            }
        }
    },
    methods: {
        pad(value) {
            return String(value).padStart(2, '0')
        },
        setTimerState(data = {}) {
            this.isCurrent = Boolean(data.is_current)
            this.durationSeconds = this.isCurrent
                ? Number(data.duration_incomplete || 0)
                : 0

            if (this.isCurrent) {
                this.startLocalTimer()
            } else {
                this.stopLocalTimer()
            }
        },
        startLocalTimer() {
            this.stopLocalTimer()
            this.runTimerId = setInterval(() => {
                this.durationSeconds += 1
            }, 1000)
        },
        stopLocalTimer() {
            if (this.runTimerId) {
                clearInterval(this.runTimerId)
                this.runTimerId = null
            }
        },
        stopPolling() {
            if (this.pollIntervalId) {
                clearInterval(this.pollIntervalId)
                this.pollIntervalId = null
            }
        },
        startPolling() {
            this.stopPolling()
            this.pollIntervalId = setInterval(() => {
                this.fetchTimerState({ silent: true })
            }, POLL_INTERVAL)
        },
        resetTimerState() {
            this.stopPolling()
            this.stopLocalTimer()
            this.durationSeconds = 0
            this.isCurrent = false
            this.loading = false
            this.actionLoading = false
            this.fetchPromise = null
            this.lastFetchAt = 0
            this.lastFetchedTaskId = null
        },
        async initTimer() {
            if (!this.canUseTimer) {
                this.resetTimerState()
                return
            }

            this.startPolling()
            await this.fetchTimerState()
        },
        async fetchTimerState({ silent = false, force = false } = {}) {
            const taskId = this.task?.id

            if (!taskId || !this.canUseTimer) { return }

            const isSameTask = this.lastFetchedTaskId === taskId
            const isSocketCooldownActive = silent
                && !force
                && isSameTask
                && Date.now() - this.lastFetchAt < SOCKET_SYNC_INTERVAL

            if (isSocketCooldownActive) { return }
            if (this.fetchPromise) { return this.fetchPromise }

            const request = (async() => {
                try {
                    if (!silent) {
                        this.loading = true
                    }

                    const { data } = await this.$http.get(`/tasks/${taskId}/time_tracking/duration/`)
                    this.setTimerState(data)
                    this.lastFetchAt = Date.now()
                    this.lastFetchedTaskId = taskId
                } catch(error) {
                    this.stopLocalTimer()
                    errorHandler({ error, show: !silent })
                } finally {
                    if (!silent) {
                        this.loading = false
                    }
                }
            })()

            this.fetchPromise = request

            try {
                return await request
            } finally {
                if (this.fetchPromise === request) {
                    this.fetchPromise = null
                }
            }
        },
        emitRuntimeUpdate() {
            if (!this.task?.id) { return }

            eventBus.$emit(`task_update_actions_${this.task.id}`)
        },
        async toggleTimer() {
            if (!this.task?.id || !this.canUseTimer || this.actionLoading) { return }

            const endpoint = this.isCurrent ? 'stop' : 'start'
            const action = this.isCurrent ? 'stop_timer' : 'start_timer'
            const payload = {
                duration: Math.max(0, Math.floor(Number(this.durationSeconds) || 0)),
                is_current: !this.isCurrent
            }

            try {
                this.actionLoading = true
                const { data } = await this.$http.post(`/tasks/${this.task.id}/time_tracking/${endpoint}/`, payload)
                this.setTimerState(data)
                this.lastFetchAt = Date.now()
                this.lastFetchedTaskId = this.task.id
                this.emitRuntimeUpdate()
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.actionLoading = false
            }
        }
    },
    beforeDestroy() {
        this.stopPolling()
        this.stopLocalTimer()
    }
}
</script>

<style lang="scss" scoped>
.task-timer{
    min-width: 0;

    &--footer{
        flex-shrink: 0;
    }

    &--aside{
        margin-left: 12px;
    }
}

.task-timer__button{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 36px;
    padding: 6px 14px;
    border: 0;
    border-radius: 8px;
    background: #dce7da;
    color: #1f2937;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    cursor: pointer;
    transition: opacity .2s ease, background-color .2s ease;
    user-select: none;

    &:disabled{
        cursor: default;
        opacity: .7;
    }
}

.task-timer--footer .task-timer__button{
    min-height: 36px;
}

.task-timer--aside .task-timer__button{
    min-height: 34px;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
}

.task-timer--current .task-timer__button{
    background: #d6ead8;
}

.task-timer__icon{
    font-size: 16px;
}

.task-timer__label,
.task-timer__value{
    white-space: nowrap;
}

.task-timer__value{
    font-weight: 600;
    letter-spacing: 0.04em;
}

@media (max-width: 764px) {
    .task-timer--footer{
        width: 100%;
        margin-top: 10px;
        margin-left: 0;
    }

    .task-timer--footer .task-timer__button{
        width: 100%;
        justify-content: center;
    }
}
</style>
