<template>
    <div v-if="canUseTimer" class="task_timer">
        <a-button
            v-if="isRunning"
            type="green"
            flaticon
            v-tippy
            :content="$t('task.stop_timer')"
            class="timer_button timer_button_running"
            :loading="loading || actionLoading"
            @click.stop="toggleTimer()">
            <div v-if="!loading && !actionLoading" class="flex items-center">
                <i class="fi fi-rr-pause mr-2" />
                <span class="timer_text">{{ formattedDuration }}</span>
            </div>
        </a-button>

        <a-button
            v-else
            type="flat_primary"
            flaticon
            shape="circle"
            icon="fi-rr-play"
            v-tippy
            :content="$t('task.start_timer')"
            class="timer_button"
            :loading="loading || actionLoading"
            @click.stop="toggleTimer()" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'TaskTimerButton',
    props: {
        task: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            durationSeconds: 0,
            runTimerId: null
        }
    },
    computed: {
        canUseTimer() {
            return Boolean(this.task?.id)
        },
        isRunning() {
            return Boolean(this.task?.is_current)
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
        'task.id': {
            immediate: true,
            async handler() {
                this.resetTimerState()
                await this.initTimer()
            }
        },
        'task.is_current': {
            immediate: true,
            handler(value) {
                if (value) {
                    this.startLocalTimer()
                    return
                }

                this.stopLocalTimer()
                this.durationSeconds = 0
            }
        },
        'task.duration_incomplete': {
            immediate: true,
            handler(value) {
                if (this.isRunning) return
                this.durationSeconds = 0
            }
        }
    },
    mounted() {
        eventBus.$on('global_timer_sync_required', this.handleGlobalTimerSync)
    },
    beforeDestroy() {
        eventBus.$off('global_timer_sync_required', this.handleGlobalTimerSync)
        this.stopLocalTimer()
    },
    methods: {
        pad(value) {
            return String(value).padStart(2, '0')
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
        resetTimerState() {
            this.stopLocalTimer()
            this.durationSeconds = this.isRunning
                ? Number(this.task?.duration_incomplete || 0)
                : 0
            this.loading = false
            this.actionLoading = false
        },
        async initTimer() {
            if (!this.task?.id) return

            this.durationSeconds = this.isRunning
                ? Number(this.task?.duration_incomplete || 0)
                : 0

            if (this.isRunning) {
                await this.fetchTimerState()
            }
        },
        setTimerState(data = {}) {
            const durationIncomplete = Number(data.duration_incomplete || 0)
            const isCurrent = Boolean(data.is_current)

            this.durationSeconds = isCurrent ? durationIncomplete : 0
            this.$set(this.task, 'duration_incomplete', durationIncomplete)
            this.$set(this.task, 'is_current', isCurrent)

            if (isCurrent) {
                this.startLocalTimer()
            } else {
                this.stopLocalTimer()
            }
        },
        async fetchTimerState({ silent = false } = {}) {
            if (!this.task?.id || !this.canUseTimer) return

            try {
                if (!silent) this.loading = true
                const { data } = await this.$http.get(`/tasks/${this.task.id}/time_tracking/duration/`)
                this.setTimerState(data)
            } catch(error) {
                errorHandler({ error, show: !silent })
            } finally {
                if (!silent) this.loading = false
            }
        },
        emitGlobalTimerSync(action) {
            const payload = {
                entity: 'task',
                entityId: this.task.id,
                action
            }

            eventBus.$emit(`task_update_actions_${this.task.id}`)
            eventBus.$emit('global_timer_sync_required', payload)
            window.dispatchEvent(new CustomEvent('global-timer-sync-required', {
                detail: payload
            }))
        },
        async toggleTimer() {
            if (!this.task?.id || !this.canUseTimer || this.actionLoading) return

            const endpoint = this.isRunning ? 'stop' : 'start'
            const action = this.isRunning ? 'stop_timer' : 'start_timer'
            const payload = {
                duration: Math.max(0, Math.floor(Number(this.durationSeconds) || 0)),
                is_current: !this.isRunning
            }

            try {
                this.actionLoading = true
                const { data } = await this.$http.post(`/tasks/${this.task.id}/time_tracking/${endpoint}/`, payload)
                this.setTimerState(data)
                this.emitGlobalTimerSync(action)
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.actionLoading = false
            }
        },
        handleGlobalTimerSync(payload = {}) {
            if (!this.canUseTimer) return
            if (payload?.entity === 'task' && String(payload?.entityId) === String(this.task?.id)) return

            if (payload?.action === 'start_timer' && this.task?.is_current) {
                this.$set(this.task, 'is_current', false)
                this.stopLocalTimer()
                this.durationSeconds = 0
            }
        }
    }
}
</script>

<style scoped lang="scss">
.task_timer{
    display: flex;
}

.timer_button_running{
    border-radius: 30px;
}

.timer_button {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.timer_text {
    text-align: left;
}
</style>
