<template>
    <div>
        {{ formattedText }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number], // секунды
            default: null
        },
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        formattedText() {
            const s = Number(this.text || 0)
            if (s < 60) {
                return `${s} ${this.plural(s, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`
            }
            if (s < 3600) {
                const m = Math.floor(s / 60)
                const sec = s % 60
                return `${m} ${this.plural(m, this.$t('helpdesk.minute1'), this.$t('helpdesk.minute2'), this.$t('helpdesk.minute3'))} ${sec} ${this.plural(sec, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`
            }
            const hours = Math.floor(s / 3600)
            const minutes = Math.floor((s % 3600) / 60)
            const seconds = s % 60
            const pad = n => String(n).padStart(2, '0')
            return `${pad(hours)}:${pad(minutes)}:${pad(seconds)} ч`
        }
    },
    methods: {
        plural(n, one, few, many) {
            const n10 = n % 10
            const n100 = n % 100
            if (n10 === 1 && n100 !== 11) return one
            if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few
            return many
        }
    }
}
</script>