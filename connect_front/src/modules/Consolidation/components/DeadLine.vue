<template>
    <div class="deadline_tag">
        <template v-if="date">
            <a-tag 
                v-if="checkDate === 'expired'"
                class="m-0" 
                color="#f63f48">
                <span 
                    class="flex items-center" 
                    :class="wrapperClass">
                    <i class="fi fi-rr-clock-nine"></i>
                    {{$moment(date).format('DD.MM.YYYY')}}
                </span>
            </a-tag>
            <a-tag 
                v-if="checkDate === 'today'"
                class="m-0" 
                color="#fba140">
                <span 
                    class="flex items-center" 
                    :class="wrapperClass">
                    <i class="fi fi-rr-clock-nine"></i>
                    {{$moment(date).format('DD.MM.YYYY')}}
                </span>
            </a-tag>
            <span 
                v-if="checkDate === 'soon'"
                class="flex items-center"
                :class="wrapperClass">
                <i class="fi fi-rr-clock-nine"></i>
                {{$moment(date).format('DD.MM.YYYY')}}
            </span>
        </template>
        <template v-else>
            <a-tag>
                {{$t('task.no_time_limit')}}
            </a-tag>
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
        status: {
            type: Object,
            required: true
        },
        wrapperClass: {
            type: String,
            default: ''
        }
    },
    computed: {
        checkDate() {
            if(this.status.code !== 'completed') {
                let current = this.$moment(),
                    deadLine = this.$moment(this.date),
                    diff = deadLine.diff(current, 'hours')
                
                if(diff < -24 )
                    return 'expired'
                if(diff <=  0)
                    return 'today'
                else
                    return 'soon'
            } else {
                return 'soon'
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
