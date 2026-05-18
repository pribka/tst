<template>
    <transition name="global-timer-slide">
        <a-popover
            v-if="hasTimer"
            v-model="popoverVisible"
            trigger="click"
            placement="bottom"
            transitionName=""
            overlayClassName="global-timer-popover"
            @visibleChange="visibleChange">
            <template #content>
                <div class="global-timer-card">
                    <a-spin :spinning="loading || actionLoading" size="small">
                    <div
                        class="global-timer-card__link"
                        @click="openCurrentEntity">
                        {{ entityTitle }}
                    </div>

                    <a-button
                        type="flat_primary"
                        size="large"
                        class="global-timer-card__stop"
                        :loading="actionLoading"
                        @click="toggleTimer">
                        <i class="fi mr-1" :class="actionIcon" />
                        {{ actionLabel }}
                    </a-button>
                </a-spin>
            </div>
        </template>

            <a-spin
                size="small"
                :spinning="loading || actionLoading"
                class="global-timer mr-6">
                <div
                    class="global-timer__trigger"
                    v-tippy
                    :content="$t('task.global_timer')"
                    @click="noop">
                    <i class="fi fi-rr-clock-three global-timer__icon" />
                    <span class="global-timer__value">{{ timerDisplayValue }}</span>
                </div>
            </a-spin>
        </a-popover>
    </transition>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'HeaderGlobalTimer',
    sockets: {
        notify({data}) {
            if(data?.event_type === 'update_current_work')
                this.fetchTimer({ silent: true })
        }
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            popoverVisible: false,
            timerData: null,
            durationSeconds: 0,
            runTimerId: null
        }
    },
    computed: {
        hasTimer() {
            return Boolean(this.timerData && (this.timerData.task || this.timerData.ticket))
        },
        entityType() {
            if (this.timerData?.task?.id) return 'task'
            if (this.timerData?.ticket?.id) return 'ticket'
            return null
        },
        entityData() {
            if (this.entityType === 'task') return this.timerData?.task || null
            if (this.entityType === 'ticket') return this.timerData?.ticket || null
            return null
        },
        entityTitle() {
            if (!this.entityData) return ''
            const number = this.entityType === 'ticket'
                ? this.entityData.number
                : this.entityData.counter
            return `#${number} ${this.entityData.name}`
        },
        timerDisplayValue() {
            if (Number(this.timerData?.incomplete_duration || 0) === 0 && Number(this.durationSeconds || 0) === 0) {
                return '00:00'
            }

            return this.formattedDuration
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
        },
        actionLabel() {
            return this.timerData?.is_current
                ? this.$t('task.stop_timer')
                : this.$t('task.start_timer')
        },
        actionIcon() {
            return this.timerData?.is_current ? 'fi-rr-pause' : 'fi-rr-play'
        }
    },
    methods: {
        noop() {},
        pad(value) {
            return String(value).padStart(2, '0')
        },
        visibleChange(visible) {
            this.popoverVisible = visible
            if (visible) {
                this.fetchTimer({ silent: true })
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
        setTimerData(data = null) {
            const hasEntity = Boolean(data?.task?.id || data?.ticket?.id)

            if (!hasEntity) {
                this.timerData = null
                this.durationSeconds = 0
                this.stopLocalTimer()
                return
            }

            this.timerData = data
            this.durationSeconds = Number(data.incomplete_duration ?? data.duration_incomplete ?? 0)

            if (data.is_current) this.startLocalTimer()
            else this.stopLocalTimer()
        },
        async fetchTimer({ silent = false } = {}) {
            try {
                if (!silent) this.loading = true

                const { data } = await this.$http.get('/app_info/timer/')
                this.setTimerData(data)
            } catch(error) {
                errorHandler({ error, show: !silent })
            } finally {
                if (!silent) this.loading = false
            }
        },
        openCurrentEntity() {
            if (!this.entityData?.id) return

            if (this.entityType === 'task') {
                const query = { ...this.$route.query, task: this.entityData.id }
                delete query.ticketView
                delete query.requestView
                this.popoverVisible = false
                this.$router.push({ query }).catch(() => {})
                return
            }

            const query = { ...this.$route.query, ticketView: this.entityData.id }
            delete query.task
            delete query.requestView
            this.popoverVisible = false
            this.$router.push({ query }).catch(() => {})
        },
        async toggleTimer() {
            if (!this.entityData?.id || this.actionLoading) return

            try {
                this.actionLoading = true

                if (this.entityType === 'task') {
                    if (this.timerData?.is_current) {
                        await this.$http.post(`/tasks/${this.entityData.id}/time_tracking/stop/`, {
                            duration: Math.max(0, Math.floor(Number(this.durationSeconds) || 0)),
                            is_current: false
                        })
                    } else {
                        await this.$http.post(`/tasks/${this.entityData.id}/time_tracking/start/`, {
                            duration: Math.max(0, Math.floor(Number(this.durationSeconds) || 0)),
                            is_current: true
                        })
                    }
                } else if (this.entityType === 'ticket') {
                    if (this.timerData?.is_current) {
                        await this.$http.post(`/help_desk/tickets/${this.entityData.id}/work_log/stop/`, {
                            duration_incomplete: Number(this.timerData?.incomplete_duration || 0),
                            description: ''
                        })
                    } else {
                        await this.$http.post(`/help_desk/tickets/${this.entityData.id}/work_log/start/`)
                    }
                }

                await this.fetchTimer({ silent: true })
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.actionLoading = false
            }
        },
    },
    mounted() {
        this.fetchTimer()
    },
    beforeDestroy() {
        this.stopLocalTimer()
    }
}
</script>

<style lang="scss">
.global-timer-popover{
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px!important;
        .ant-popover-arrow{
            display: none;
        }
    }
}
</style>

<style lang="scss" scoped>
.global-timer-slide-enter-active,
.global-timer-slide-leave-active{
    transition: opacity .25s ease, transform .25s ease;
}

.global-timer-slide-enter,
.global-timer-slide-leave-to{
    opacity: 0;
    transform: translateX(20px);
}

.global-timer{
    display: inline-flex;
    margin-left: 10px;
}

.global-timer__trigger{
    color: #1f2937;
    height: 32px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0 10px;
    font-size: 15px;
    font-weight: 600;
    border-radius: 8px;
    line-height: 1;
    cursor: pointer;
    user-select: none;
    background: #fff;
}

.global-timer__icon{
    font-size: 15px;
    color: #64748b;
}

.global-timer-card{
    min-width: 240px;
    max-width: 280px;
}

.global-timer-card__link{
    margin-bottom: 12px;
    color: var(--blue);
    cursor: pointer;
    line-height: 1.35;
    word-break: break-word;
}

.global-timer-card__stop{
    width: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &::v-deep.ant-btn,
    &::v-deep .ant-btn{
        background: #dce7da;
        border-color: #dce7da;
        color: #1f2937;
        border-radius: 8px;
    }

    &::v-deep.ant-btn:hover,
    &::v-deep.ant-btn:focus,
    &::v-deep .ant-btn:hover,
    &::v-deep .ant-btn:focus{
        background: #d6ead8;
        border-color: #d6ead8;
        color: #1f2937;
    }
}
</style>
