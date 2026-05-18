<template>
    <div>
        <a-button
            v-if="showStopButton"
            type="green"
            flaticon
            v-tippy
            :content="$t('helpdesk.stop_timer')"
            class="timer_button timer_button_running"
            :loading="statusLoader || durationLoading"
            @click.stop="openFinishModal({ status: 'on_pause' })">
            <div v-if="!statusLoader && !durationLoading" class="flex items-center">
                <i class="fi fi-rr-pause mr-2" />
                <span class="timer_text">{{ formattedTimer }}</span>
            </div>
        </a-button>

        <a-button
            v-else-if="showStartButton && mobile"
            type="flat_primary"
            flaticon
            class="timer_button timer_button_mobile"
            :loading="statusLoader"
            @click.stop="startTimer()">
            <i class="fi fi-rr-play" />
        </a-button>

        <a-button
            v-else-if="showStartButton"
            type="flat_primary"
            flaticon
            shape="circle"
            icon="fi-rr-play"
            v-tippy
            :content="$t('helpdesk.start_execution')"
            class="timer_button"
            :loading="statusLoader"
            @click.stop="startTimer()" />

        <a-modal
            v-model="finishModalVisible"
            :footer="null"
            @afterClose="finishModalAfterClose"
            @afterVisibleChange="afterVisibleChange"
            @cancel="finishModalVisible = false">
            <template #title>
                {{ $t('helpdesk.on_pause') }}
            </template>

            <div class="mt-5">
                <a-skeleton v-if="getIncompleteDurationLoading" />
                <template v-else>
                    <div class="grid md:grid-cols-3 gap-2">
                        <div class="item_block">
                            <div class="mb-1">{{ $t('helpdesk.hours') }}</div>
                            <a-input-number
                                v-model="customDuration.hours"
                                size="large"
                                class="w-full"
                                :min="0"
                                :precision="0"
                                :placeholder="$t('helpdesk.hours_placeholder')" />
                        </div>
                        <div class="item_block">
                            <div class="mb-1">{{ $t('helpdesk.minutes') }}</div>
                            <a-input-number
                                v-model="customDuration.minutes"
                                size="large"
                                class="w-full"
                                :min="0"
                                :max="59"
                                :precision="0"
                                :placeholder="$t('helpdesk.minutes_placeholder')" />
                        </div>
                        <div class="item_block">
                            <div class="mb-1">{{ $t('helpdesk.seconds') }}</div>
                            <a-input-number
                                v-model="customDuration.seconds"
                                size="large"
                                class="w-full"
                                :min="0"
                                :max="59"
                                :precision="0"
                                :placeholder="$t('helpdesk.seconds_placeholder')" />
                        </div>
                    </div>

                    <div class="mt-3 text-right">
                        <span class="text-muted mr-2">{{ $t('helpdesk.total_by_ticket') }}:</span>
                        <span>{{ formattedTimer }}</span>
                    </div>

                    <div class="mt-3">
                        <div class="execution_result__label mb-1">{{ $t('helpdesk.description') }}</div>
                        <a-textarea
                            v-model="description"
                            inputType="bg"
                            :placeholder="$t('helpdesk.print_description')"
                            :auto-size="{ minRows: 3, maxRows: 5 }" />
                    </div>

                    <template v-if="!ticket.started_timer">
                        <div ref="calendarWrapRef" class="mt-4">
                            <a-date-picker
                                v-model="accountingDate"
                                :getCalendarContainer="() => $refs.calendarWrapRef"
                                format="DD.MM.YYYY"
                                class="w-full"
                                size="large" />
                        </div>
                    </template>

                    <div class="mt-4 grid md:grid-cols-1 gap-2">
                        <a-button
                            type="primary"
                            block
                            :loading="statusLoader"
                            @click="stopTimerWithTime()">
                            {{ $t('helpdesk.confirm_action') }}
                        </a-button>
                    </div>
                </template>
            </div>
        </a-modal>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        listType: {
            type: String,
            default: 'ticketList'
        },
        isActiveTab: {
            type: Boolean,
            default: false
        },
        mobile: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ticketListState() {
            return this.$store.state.workplan.ticketList?.[this.storeKey]?.results || []
        },
        ticketOtherListState() {
            return this.$store.state.workplan.ticketOtherList?.[this.storeKey]?.results || []
        },
        isRunning() {
            return !!this.ticket?.is_current
        },
        canUseTimer() {
            return !!this.ticket?.id
        },
        showStartButton() {
            return !this.isRunning && this.canUseTimer
        },
        showStopButton() {
            return this.isRunning && this.canUseTimer
        },
        formattedTimer() {
            const total = Math.max(0, this.timerStop ? this.stoppedValue : this.elapsedSeconds)
            const h = Math.floor(total / 3600)
            const m = Math.floor((total % 3600) / 60)
            const s = Math.floor(total % 60)
            const pad = n => String(n).padStart(2, '0')
            return (h > 0 ? `${pad(h)}:` : '') + `${pad(m)}:${pad(s)}`
        }
    },
    watch: {
        isActiveTab: {
            async handler(value) {
                if (!value) {
                    this.stopLocalTimer()
                    return
                }
                await this.syncTimerState()
            }
        },
        'ticket.id': {
            immediate: true,
            async handler() {
                this.stopLocalTimer()
                this.duration = 0
                this.elapsedSeconds = 0
                if (!this.isActiveTab) return
                await this.syncTimerState()
            }
        },
        'ticket.is_current': {
            immediate: true,
            async handler(value) {
                if (!this.isActiveTab) return
                if (!this.canUseTimer) return
                if (this.skipNextCurrentWatcher) {
                    this.skipNextCurrentWatcher = false
                    return
                }
                if (value) {
                    await this.getTimer()
                    this.startLocalTimer()
                } else {
                    this.stopLocalTimer()
                    this.timerStop = false
                }
            }
        }
    },
    data() {
        return {
            durationLoading: false,
            duration: 0,
            elapsedSeconds: 0,
            runTimerId: null,
            timerRequestPromise: null,
            skipNextCurrentWatcher: false,
            statusLoader: false,
            finishModalVisible: false,
            getIncompleteDurationLoading: false,
            customDuration: {
                hours: 0,
                minutes: 0,
                seconds: 0
            },
            description: '',
            accountingDate: null,
            timerStop: false,
            stoppedValue: 0
        }
    },
    mounted() {
        eventBus.$on('global_timer_sync_required', this.handleGlobalTimerSync)
        window.addEventListener('global-timer-sync-required', this.handleWindowGlobalTimerSync)
    },
    beforeDestroy() {
        eventBus.$off('global_timer_sync_required', this.handleGlobalTimerSync)
        window.removeEventListener('global-timer-sync-required', this.handleWindowGlobalTimerSync)
        this.stopLocalTimer()
    },
    methods: {
        getOtherRunningTicketIds() {
            const all = [...this.ticketListState, ...this.ticketOtherListState]
            const uniq = new Set()
            for (const item of all) {
                if (!item?.id || item.id === this.ticket.id) continue
                if (item.is_current) uniq.add(item.id)
            }
            return Array.from(uniq)
        },
        async syncOtherRunningTickets() {
            const ids = this.getOtherRunningTicketIds()
            if (!ids.length) return

            const details = await Promise.allSettled(
                ids.map(id => this.$http.get(`/help_desk/tickets/${id}/`))
            )

            const updates = []
            for (const res of details) {
                if (res.status !== 'fulfilled') continue
                const detail = res.value?.data
                if (!detail?.id) continue
                updates.push({
                    ...detail,
                    is_current: false
                })
            }

            await Promise.all(
                updates.map(item => this.$store.dispatch('workplan/updateItem', {
                    list: 'ticketList',
                    item,
                    notAllReload: true
                }))
            )
        },
        async syncTimerState() {
            if (this.isRunning) {
                await this.getTimer()
                this.startLocalTimer()
            } else {
                this.stopLocalTimer()
            }
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            return {
                hours: Math.floor(t / 3600),
                minutes: Math.floor((t % 3600) / 60),
                seconds: t % 60
            }
        },
        HMSToSeconds(HMS) {
            const { hours, minutes, seconds } = HMS
            return (hours * 3600) + (minutes * 60) + seconds
        },
        startLocalTimer() {
            this.stopLocalTimer()
            this.runTimerId = setInterval(() => {
                this.elapsedSeconds += 1
            }, 1000)
        },
        stopLocalTimer() {
            if (this.runTimerId) {
                clearInterval(this.runTimerId)
                this.runTimerId = null
            }
        },
        async getTimer() {
            if (this.timerRequestPromise) {
                return this.timerRequestPromise
            }

            try {
                this.durationLoading = true
                this.timerRequestPromise = this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)

                const { data } = await this.timerRequestPromise
                if (data) {
                    this.duration = data.duration
                    this.elapsedSeconds = Boolean(data.is_current)
                        ? Math.max(0, Math.floor(Number(data.duration_incomplete || 0)))
                        : 0
                }
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.timerRequestPromise = null
                this.durationLoading = false
            }
        },
        async syncTicketState({ silent = true } = {}) {
            if (!this.ticket?.id) return

            try {
                if (!silent) {
                    this.durationLoading = true
                }

                const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/`)

                if (!data) return

                this.$set(this.ticket, 'is_current', !!data.is_current)
                this.$set(this.ticket, 'started_timer', !!data.started_timer)
                this.$set(this.ticket, 'duration_incomplete', Number(data.duration_incomplete || 0))

                if (data.status) {
                    this.$set(this.ticket, 'status', data.status)
                }

                if (data.is_current) {
                    await this.getTimer()
                    this.startLocalTimer()
                } else {
                    this.stopLocalTimer()
                    this.timerStop = false
                    this.elapsedSeconds = 0
                }
            } catch(error) {
                errorHandler({ error, show: !silent })
            } finally {
                if (!silent) {
                    this.durationLoading = false
                }
            }
        },
        afterVisibleChange(vis) {
            if (!vis) {
                this.timerStop = false
                this.description = ''
            }
        },
        finishModalAfterClose() {
            this.customDuration = {
                hours: 0,
                minutes: 0,
                seconds: 0
            }
            this.accountingDate = null
            this.description = ''
        },
        async openFinishModal({ status = null }) {
            if (status !== 'on_pause') {
                return
            }
            this.finishModalVisible = true
            if (!this.ticket.started_timer) {
                this.accountingDate = this.$moment()
            }
            this.getIncompleteDurationLoading = true
            try {
                const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                this.timerStop = true
                this.stoppedValue = Math.max(0, this.elapsedSeconds)
                this.customDuration = this.secondsToHMS(data.duration_incomplete)
            } catch(error) {
                this.timerStop = false
                errorHandler({ error })
            } finally {
                this.getIncompleteDurationLoading = false
            }
        },
        async toggleTimer(status, startedTimerSnapshot = null) {
            const wasStartedTimer = startedTimerSnapshot === null
                ? !!this.ticket.started_timer || !!this.ticket.is_current
                : !!startedTimerSnapshot

            if (status === 'in_work') {
                const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/start/`)
                if (data) {
                    this.duration = data.duration
                    this.elapsedSeconds = Boolean(data.is_current)
                        ? Math.max(0, Math.floor(Number(data.duration_incomplete || 0)))
                        : 0
                    this.startLocalTimer()
                }
            }

            if (status === 'on_pause') {
                if (wasStartedTimer) {
                    const payload = {
                        duration_incomplete: this.HMSToSeconds(this.customDuration),
                        description: this.description
                    }
                    const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/stop/`, payload)
                    if (data) {
                        this.duration = data.duration
                        this.elapsedSeconds = Boolean(data.is_current)
                            ? Math.max(0, Math.floor(Number(data.duration_incomplete || 0)))
                            : 0
                        this.stopLocalTimer()
                    }
                } else {
                    if (!this.accountingDate) this.accountingDate = this.$moment()
                    const payload = {
                        duration: this.HMSToSeconds(this.customDuration),
                        date: this.accountingDate.format('YYYY-MM-DD'),
                        description: this.description
                    }
                    await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/create/`, payload)
                }
            }
        },
        async changeStatus(status) {
            try {
                this.statusLoader = true
                const startedTimerSnapshot = !!this.ticket?.started_timer || !!this.ticket?.is_current
                const shouldUpdateStatus = this.ticket?.status?.code !== status
                let data = null

                if (shouldUpdateStatus) {
                    const response = await this.$http.put(`/help_desk/tickets/${this.ticket.id}/status/`, { status })
                    data = response?.data || null
                }

                await this.toggleTimer(status, startedTimerSnapshot)

                const updateItem = {
                    ...(shouldUpdateStatus ? (data || {}) : this.ticket),
                    id: this.ticket.id
                }
                if (status === 'in_work') updateItem.is_current = true
                if (status === 'on_pause') updateItem.is_current = false
                this.skipNextCurrentWatcher = true
                this.$set(this.ticket, 'is_current', status === 'in_work')

                await this.$store.dispatch('workplan/updateItem', {
                    list: 'ticketList',
                    item: updateItem,
                    notAllReload: true
                })

                if (status === 'in_work') {
                    await this.syncOtherRunningTickets()
                }

                eventBus.$emit('global_timer_sync_required', {
                    entity: 'ticket',
                    entityId: this.ticket.id,
                    action: status === 'in_work' ? 'start_timer' : 'stop_timer'
                })
                this.finishModalVisible = false
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.statusLoader = false
            }
        },
        async startTimer() {
            if (!this.isActiveTab) return
            if (!this.canUseTimer) return
            await this.changeStatus('in_work')
        },
        async stopTimerWithTime() {
            if (!this.isActiveTab) return
            if (!this.canUseTimer) return
            await this.changeStatus('on_pause')
        },
        handleGlobalTimerSync(payload = {}) {
            if (payload?.entity === 'ticket' && String(payload?.entityId) === String(this.ticket?.id)) return

            if (payload?.entity === 'task' && payload?.action === 'start_timer') {
                this.$set(this.ticket, 'is_current', false)
                this.$set(this.ticket, 'started_timer', false)
                this.stopLocalTimer()
                this.timerStop = false
                return
            }
        },
        handleWindowGlobalTimerSync(event) {
            this.handleGlobalTimerSync(event?.detail || {})
        }
    }
}
</script>

<style scoped lang="scss">
.timer_button_running{
    border-radius: 30px;
}
.timer_button {
    display: flex;
    align-items: center;
    justify-content: center;
}

.timer_button_mobile {
    min-width: 36px;
    width: 36px;
    height: 36px;
    padding: 0;
    border-radius: 999px;
}

.timer_text {
    text-align: left;
}
</style>
