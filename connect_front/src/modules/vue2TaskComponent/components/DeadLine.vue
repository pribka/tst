<template>
    <div class="deadline_tag">
        <template v-if="date">
            <span 
                v-if="chechDate === 'expired'"
                class="m-0" 
                style="color: #FF5C5C;white-space: nowrap;">
                <span 
                    class="flex items-center" 
                    :class="wrapperClass">
                    {{$moment(date).format($t('task.date_format'))}}
                </span>
            </span>
            <span 
                v-if="chechDate === 'today'"
                class="m-0"
                style="white-space: nowrap;">
                <span 
                    class="flex items-center" 
                    :class="wrapperClass">
                    {{$moment(date).format($t('task.date_format'))}}
                </span>
            </span>
            <span 
                v-if="chechDate === 'soon'"
                class="flex items-center"
                :class="wrapperClass"
                style="white-space: nowrap;">
                {{$moment(date).format($t('task.date_format'))}}
            </span>
        </template>
        <template v-else>
            <span>
                {{$t('task.no_time_limit')}}
            </span>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        date: {
            type: [String, Number],
            default: null
        },
        taskStatus: {
            type: Object,
            required: true
        },
        wrapperClass: {
            type: String,
            default: ''
        }
    },
    computed: {
        chechDate() {
            if(this.taskStatus?.code === 'completed')
                return 'soon'
            else {
                if(this.$moment().diff(this.date, 'minute') <= 1) {

                    let current = this.$moment(),
                        taskDate = this.$moment(this.date),
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

<style lang="scss">
.deadline_tag{
    display: flex;
    align-items: center;
    i{
        margin-right: 5px;
    }
    .ant-tag{

    }
}
</style>
