<template>
    <div class="completed_banner">
        <div class="completed_banner__wrapper">
            <a-spin :spinning="durationLoading" size="small">
                <div v-if="duration !== null" class="mb-1 font-semibold">
                    {{ formattedDuration }}
                </div>
            </a-spin>
            <div>{{ $t('helpdesk.execution_result') }}: {{ ticket.execution_result }}</div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        ticket: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            duration: null, // секунды
            durationLoading: true
        }
    },
    computed: {
        formattedDuration() {
            const s = Number(this.duration || 0)
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
    },
    methods: {
        plural(n, one, few, many) {
            const n10 = n % 10
            const n100 = n % 100
            if (n10 === 1 && n100 !== 11) return one
            if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few
            return many
        },
        async getTimer() {
            try {
                const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                if (data) {
                    this.duration = data.duration
                }
            } catch(e) {
                console.log(e)
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
}
</style>