<template>
    <div :class="cls">
        {{ formattedDiff }}
    </div>
</template>

<script>
export default {
    props: {
        main: {
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String]
        }
    },
    computed: {
        diffSeconds() {
            const planHours = this.toNum(this.record?.duration_plan)
            const factSeconds = this.toNum(this.record?.duration_fact)

            if (planHours == null || factSeconds == null) return null

            const planSeconds = planHours * 3600
            return planSeconds - factSeconds
        },

        formattedDiff() {
            if (this.diffSeconds == null) return '—'

            const sign = this.diffSeconds > 0 ? '+' : this.diffSeconds < 0 ? '−' : ''
            const abs = Math.abs(this.diffSeconds)

            const hours = Math.floor(abs / 3600)
            const minutes = Math.floor((abs % 3600) / 60)
            const seconds = abs % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            let result = ''

            if (hours > 0) {
                result += `${hours} ${plural(hours, this.$t('helpdesk.hour1'), this.$t('helpdesk.hour2'), this.$t('helpdesk.hour3'))}`
            }

            if (minutes > 0) {
                if (result) result += ' '
                result += `${minutes} ${plural(minutes, this.$t('helpdesk.minute1'), this.$t('helpdesk.minute2'), this.$t('helpdesk.minute3'))}`
            }

            if (!result) {
                result = `${seconds} ${plural(seconds, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`
            }

            return `${sign}${result}`
        },

        cls() {
            if (this.diffSeconds == null) return ''
            if (this.diffSeconds > 0) return 'diff-pos'
            if (this.diffSeconds < 0) return 'diff-neg'
            return 'diff-zero'
        }
    },
    methods: {
        toNum(v) {
            if (v === null || v === undefined || v === '') return null
            const n = typeof v === 'string' ? Number(v.replace(',', '.')) : Number(v)
            return Number.isFinite(n) ? n : null
        }
    }
}
</script>

<style scoped>
.diff-pos { color: #368225; }
.diff-neg { color: #FF5C5C; }
</style>
