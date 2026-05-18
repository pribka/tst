<template>
    <div>
        {{ rangesText }}
    </div>
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда-то помимо страницы задач, тут нужно false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        // можно передавать массив готовых диапазонов вместо record.vacation_dates (опционально)
        text: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        rangesText() {
            const items = Array.isArray(this.text) && this.text.length
                ? this.text
                : (Array.isArray(this.record?.vacation_dates) ? this.record.vacation_dates : [])

            if (!items.length) return ''

            const currentYear = this.$moment().year()

            const fmt = (d) => {
                if (!d) return null
                const m = this.$moment(d)
                if (!m.isValid()) return null
                return m.year() === currentYear ? m.format('DD.MM') : m.format('DD.MM.YYYY')
            }

            const formatRange = ({ start_date, end_date }) => {
                const s = fmt(start_date)
                const e = fmt(end_date)
                if (s && e) {
                    // если один и тот же день — выводим один раз
                    const sameDay = this.$moment(start_date).isSame(this.$moment(end_date), 'day')
                    return sameDay ? s : `${s} - ${e}`
                }
                if (s) return s
                if (e) return e
                return ''
            }

            return items
                .map(formatRange)
                .filter(Boolean)
                .join(', ')
        }
    }
}
</script>