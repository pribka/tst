<template>
    <div 
        class="deadline_card whitespace-nowrap" 
        :class="checkResponse && 'responsive'">
        <template v-if="checkDates">
            <span v-if="task.date_start_plan">
                {{$moment(task.date_start_plan).format('DD.MM.YYYY')}} <span class="d_time">{{$moment(task.date_start_plan).format('HH:mm')}}</span>
            </span>
            <span 
                v-if="checkAllDates" 
                class="l">
                -
            </span>
            <span 
                v-if="task.dead_line"
                :class="chechDate">
                {{$moment(task.dead_line).format('DD.MM.YYYY')}} <span class="d_time">{{$moment(task.dead_line).format('HH:mm')}}</span>
            </span>
        </template>
        <span 
            v-else 
            class="no_date">
            {{$t('task.no_time_limit')}}
        </span>
    </div>
</template>

<script>
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        responsive: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        checkResponse() {
            if(this.responsive && this.checkAllDates) {
                return true
            }
            return false
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        checkAllDates() {
            return this.task.dead_line && this.task.date_start_plan ? true : false
        },
        checkDates() {
            return this.task.dead_line || this.task.date_start_plan ? true : false
        },
        chechDate() {
            if(this.task.status?.code === 'completed')
                return 'soon'
            else {
                if(this.$moment().diff(this.task.dead_line, 'minute') <= 1) {

                    let current = this.$moment(),
                        taskDate = this.$moment(this.task.dead_line),
                        days = taskDate.diff(current, 'days')

                    if(days < 3 )
                        return 'today'
                    else
                        return 'soon'
                } else
                    return 'expired'
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.deadline_card{
    font-size: 13px;
    .l{
        margin-left: 0.06rem;
        margin-right: 0.06rem;
    }
    .today{
        color: #fba140;
    }
    .expired{
        color: #f63f48;
    }
    .no_date{
        font-size: 12px;
        background: #eff2f5;
        border-radius: var(--borderRadius);
        padding: 2px 8px;
        line-height: 20px;
    }
    /* my css with @apply */
    &.responsive{
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        width: 100%;
        padding-right: 5px;
        container: response / inline-size;
        @container response (max-width: 220px) {
            .d_time{
                display: none;
            }
        }
    }
}
</style>