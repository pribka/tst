<template>
    <div class="completed_banner">
        <div class="completed_banner__wrapper">
            <a-spin :spinning="durationLoading" size="small">
                <div v-if="duration !== null" class="mb-1 font-semibold">
                    {{ formattedDuration }}
                </div>
            </a-spin>

            <div class="mt-2">
                <div class="completed_banner__result_title mb-1">
                    {{ ticket.status.code === 'rejected' ? $t('helpdesk.cancellation_reason') : $t('helpdesk.execution_result') }}
                </div>

                <template v-if="isEditing">
                    <a-textarea
                        v-model="executionResult"
                        :rows="4"
                        :placeholder="$t('helpdesk.describe_execution_result')" />
                </template>

                <template v-else>
                    <div v-if="ticket.execution_result" class="completed_banner__text">
                        {{ ticket.execution_result }}
                    </div>
                    <div v-else class="completed_banner__text completed_banner__text-muted">
                        -
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script> 
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        actions: {
            type: Object,
            default: () => null
        },
        getTicket: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            duration: null, // секунды
            durationLoading: true,
            isEditing: false,
            saveLoading: false,
            executionResult: "",
            saveTimer: null
        }
    },
    computed: {
        canEditExecutionResult() {
            if (this.ticket?.status?.code !== 'completed') {
                return false
            }

            const action = this.actions?.edit_execution_result
            if (typeof action === 'boolean') {
                return action
            }

            return Boolean(action?.availability)
        },
        formattedDuration() {
            const s = Number(this.ticket.work_log_duration || 0)
            if (s < 60) {
                return `${this.$t('helpdesk.work_efforts')}: ${s} ${this.plural(s, this.$t('helpdesk.second'), this.$t('helpdesk.seconds_2_4'), this.$t('helpdesk.seconds_many'))}`
            }
            if (s < 3600) {
                const m = Math.floor(s / 60)
                const sec = s % 60
                return `${this.$t('helpdesk.work_efforts')}: ${m} ${this.plural(m, this.$t('helpdesk.minute'), this.$t('helpdesk.minutes_2_4'), this.$t('helpdesk.minutes_many'))} ${sec} ${this.plural(sec, this.$t('helpdesk.second'), this.$t('helpdesk.seconds_2_4'), this.$t('helpdesk.seconds_many'))}`
            }
            const hours = Math.floor(s / 3600)
            const minutes = Math.floor((s % 3600) / 60)
            const seconds = s % 60
            const pad = n => String(n).padStart(2, '0')
            return `${this.$t('helpdesk.work_efforts')}: ${pad(hours)}:${pad(minutes)}:${pad(seconds)} ${this.$t('helpdesk.hour_short')}`
        }
    },
    created() {
        this.getTimer()
        this.executionResult = this.ticket?.execution_result || ""
    },
    watch: {
        edit: {
            immediate: true,
            handler(value) {
                if (value && this.canEditExecutionResult) {
                    this.executionResult = this.ticket?.execution_result || ""
                    this.isEditing = true
                    return
                }

                this.flushSaveExecutionResult()
                this.isEditing = false
            }
        },
        'ticket.execution_result': {
            immediate: true,
            handler(value) {
                if (!this.isEditing) {
                    this.executionResult = value || ""
                }
            }
        },
        executionResult(value) {
            if (!this.isEditing || !this.canEditExecutionResult) {
                return
            }

            if ((value || "") === (this.ticket?.execution_result || "")) {
                return
            }

            clearTimeout(this.saveTimer)
            this.saveTimer = setTimeout(() => {
                this.saveExecutionResult({ silent: true, reload: false })
            }, 450)
        }
    },
    beforeDestroy() {
        clearTimeout(this.saveTimer)
    },
    methods: {
        plural(n, one, few, many) {
            const n10 = n % 10
            const n100 = n % 100
            if (n10 === 1 && n100 !== 11) return one
            if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few
            return many
        },
        async saveExecutionResult({ silent = false, reload = true } = {}) {
            try {
                const nextValue = this.executionResult || ""
                const currentValue = this.ticket?.execution_result || ""
                if (nextValue === currentValue) {
                    return false
                }

                this.saveLoading = true
                const payload = {
                    execution_result: nextValue
                }
                const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/execution_result/`, payload)

                if (Object.prototype.hasOwnProperty.call(data || {}, 'execution_result')) {
                    this.$set(this.ticket, 'execution_result', data.execution_result || "")
                } else {
                    this.$set(this.ticket, 'execution_result', payload.execution_result)
                }

                if (reload) {
                    await this.getTicket(true, false)
                }
                if (!silent) {
                    this.$message.success(this.$t('Changes saved'))
                }
                return true
            } catch(error) {
                errorHandler({error})
                return false
            } finally {
                this.saveLoading = false
            }
        },
        flushSaveExecutionResult() {
            clearTimeout(this.saveTimer)
            if (!this.isEditing || !this.canEditExecutionResult) {
                return
            }
            if ((this.executionResult || "") !== (this.ticket?.execution_result || "")) {
                this.saveExecutionResult({ silent: true, reload: false })
            }
        },
        async getTimer() {
            try {
                const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                if (data) {
                    this.duration = data.duration
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.durationLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.completed_banner{
    &__wrapper{
        background: #E6EFE3;
        color: var(--text);
        padding: 15px;
        border-radius: 12px;
        word-break: break-word;
    }

    &__result_title{
        font-weight: 600;
    }

    &__text{
        white-space: pre-wrap;
    }

    &__text-muted{
        opacity: 0.7;
    }
}
</style>
