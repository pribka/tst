<template>
    <span 
        v-if="hasDate || !hideNoDates"
        class="deadline_card font-light flex items-center leading-none whitespace-nowrap">
        <template v-if="hasDate">
            <span class="mr-1">
                <i class="fi fi-rr-clock-five"></i>
            </span>
            <span v-if="onlyStartDate" class="mr-1">{{ $t('task.date_start_plan') }}:</span>
            <span v-if="task.date_start_plan">
                {{ prettyDate(task.date_start_plan) }}
            </span>

            <template v-if="hasAllDates" >
                <span class="mx-1">-</span>
            </template>
            
            <span v-if="onlyDeadline" class="mr-1">{{ $t('task.dead_line') }}:</span>
            <span 
                v-if="task.dead_line"
                :class="colorClass">
                {{ prettyDate(task.dead_line) }}
            </span>
        </template>
        <template v-else-if="!hideNoDates">
            <span class="no_date">
                {{$t('task.no_time_limit')}}
            </span>
        </template>
    </span>
</template>

<script>
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        hideNoDates: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        hasAllDates() {
            return this.task.dead_line && this.task.date_start_plan
        },
        hasDate() {
            return this.task.dead_line || this.task.date_start_plan
        },
        onlyStartDate() {
            return this.task.date_start_plan && !this.task.dead_line
        },
        onlyDeadline() {
            return this.task.dead_line && !this.task.date_start_plan
        },
        colorClass() {
            if(this.task.status?.code === 'completed')
                return 'soon'
            else {
                if(this.$moment().diff(this.task.dead_line, 'minute') <= 1) {
                    const current = this.$moment(),
                        taskDate = this.$moment(this.task.dead_line),
                        days = taskDate.diff(current, 'days')

                    if(days < 3 )
                        return 'today'
                    else
                        return 'soon'
                } else
                    return 'expired'
            }
        },
    },
    methods: {
        notCurrentYear(date) {
            const currentDate = this.$moment()
            const taskDate = this.$moment(date)
            const yearsDifference = taskDate.diff(currentDate, 'years')
            return Boolean(yearsDifference)
        },
        prettyDate(date) {
            if(this.notCurrentYear(date))
                return this.$moment(date).format('lll')
            return this.$moment(date).format('D MMM HH:mm')
        }
    }
}
</script>

<style lang="scss" scoped>
.deadline_card{
    .today{
        color: #fba140;
    }
    .expired{
        color: #f63f48;
    }
    .no_date{
        background: #eff2f5;
        border-radius: var(--borderRadius);
        padding: 4px 8px;
        // Нужно, чтобы текст казался ровнее
        padding-bottom: 6px;
    }
}
</style>