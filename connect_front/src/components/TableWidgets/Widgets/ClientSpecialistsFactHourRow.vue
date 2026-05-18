<template>
    <div>
        {{ humanizedText }}
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
        humanizedText() {
            const totalSeconds = Number(this.text)

            if (!totalSeconds || isNaN(totalSeconds)) return this.text

            const hours = Math.floor(totalSeconds / 3600)
            const minutes = Math.floor((totalSeconds % 3600) / 60)
            const seconds = totalSeconds % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            if (hours > 0) {
                let result = `${hours} ${plural(
                    hours,
                    this.$t('helpdesk.hour1'),
                    this.$t('helpdesk.hour2'),
                    this.$t('helpdesk.hour3')
                )}`

                if (minutes > 0) {
                    result += ` ${minutes} ${plural(
                        minutes,
                        this.$t('helpdesk.minute1'),
                        this.$t('helpdesk.minute2'),
                        this.$t('helpdesk.minute3')
                    )}`
                }

                return result
            }

            if (minutes > 0) {
                return `${minutes} ${plural(
                    minutes,
                    this.$t('helpdesk.minute1'),
                    this.$t('helpdesk.minute2'),
                    this.$t('helpdesk.minute3')
                )}`
            }

            return `${seconds} ${plural(
                seconds,
                this.$t('helpdesk.second1'),
                this.$t('helpdesk.second2'),
                this.$t('helpdesk.second3')
            )}`
        }
    }
}
</script>