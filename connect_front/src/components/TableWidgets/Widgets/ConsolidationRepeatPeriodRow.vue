<template>
    <div>{{ repeatPeriod }}</div>
</template>

<script>
export default {
    props: {
        text: {
            type: String
        },
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        repeatPeriod() {
            return this.periods[this.record.repeat_period]
        }
    },
    data() {
        return {
            periods: {
                'WEEKLY': 'Еженедельно',
                'MONTHLY': 'Ежемесячно',
                'YEARLY': 'Ежегодно',
            }
        }
    }
}
</script>