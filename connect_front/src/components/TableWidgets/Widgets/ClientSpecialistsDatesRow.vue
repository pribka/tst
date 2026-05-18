<template>
    <div>
        {{ formattedDate }}
    </div>
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда-то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        }
    },
    computed: {
        formattedDate() {
            const nowYear = this.$moment().year()
            const start = this.record.start_date ? this.$moment(this.record.start_date) : null
            const end = this.record.end_date ? this.$moment(this.record.end_date) : null

            const formatDate = (date) => {
                if (!date) return null
                return date.format('DD.MM.YYYY')
            }

            const startStr = formatDate(start)
            const endStr = formatDate(end)

            if (startStr && endStr) {
                return `${startStr} - ${endStr}`
            } else if (startStr) {
                return startStr
            } else if (endStr) {
                return endStr
            } else {
                return ''
            }
        }
    }
}
</script>
