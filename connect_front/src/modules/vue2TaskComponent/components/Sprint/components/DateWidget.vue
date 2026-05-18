<template>
    <div class="deadline_tag">
        <template v-if="date">
            <a-tag class="m-0" v-if="!noColor && chechDate === 'expired'" color="#f63f48">
                <span class="flex items-center">
                    <a-icon  type="clock-circle" />
                    {{$moment(date).format('D MMMM, HH:mm')}}
                </span>
            </a-tag>
            <a-tag class="m-0" v-if="(!noColor && chechDate === 'today') " color="#fba140">
                <span class="flex items-center">
                    <a-icon  type="clock-circle" />
                    {{$moment(date).format('D MMMM, HH:mm')}}
                </span>
            </a-tag>
            <template class="flex items-center" v-if="(!noColor && chechDate === 'soon') || noColor">
                <a-icon class="mr-1"  type="clock-circle" />
                {{$moment(date).format('D MMMM, HH:mm')}}
            </template>
        </template>
        <template v-else>
            <a-tag>
                <span class="flex items-center">
                    <a-icon type="clock-circle" />
                    {{$t('task.no_time_limit')}}
                </span>
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
        noColor: Boolean
        
    },
    computed: {
        chechDate() {
            
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