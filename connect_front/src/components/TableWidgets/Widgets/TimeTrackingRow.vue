<template>
    <div>
        <span v-if="isDurations" :title="formattedDuration">
            {{ formattedDuration }}
        </span>
        <template v-else>
            <span v-if="record.measure_unit" :title="`${record.hours} ${record.measure_unit.name}`">
                {{ record.hours }} {{ record.measure_unit.name }}
            </span>
            <span v-else :title="record.hours">
                {{ record.hours }}
            </span>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        isDurations() {
            return this.record?.measure_unit?.code === 'hours' && this.record?.duration
        },

        formattedDuration() {
            const sec = Number(this.record.duration)
            if (!sec || !Number.isFinite(sec)) return '0 секунд'

            const hours = Math.floor(sec / 3600)
            const minutes = Math.floor((sec % 3600) / 60)
            const seconds = sec % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            let res = ''

            if (hours > 0)
                res += `${hours} ${plural(hours, this.$t('helpdesk.hour1'), this.$t('helpdesk.hour2'), this.$t('helpdesk.hour3'))}`

            if (minutes > 0) {
                if (res) res += ' '
                res += `${minutes} ${plural(minutes, this.$t('helpdesk.minute1'), this.$t('helpdesk.minute2'), this.$t('helpdesk.minute3'))}`
            }

            if (!res)
                res = `${seconds} ${plural(seconds, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`

            return res
        }
    }
}
</script>