<template>
    <a-card
        style="border-radius: var(--borderRadius);"
        size="small"
        :bordered="false"
        :ref="`task_card_${item.id}`"
        :class="isMobile ? 'mmb mobile_card' : 'mb-2'"
        class="task_sprint_card">
        <div class="card_title flex items-start justify-between truncate mb-2">
            <span
                v-if="!item.rejected"
                class="blue_color card_name truncate font-medium"
                @click="openTask">
                #{{item.counter}} {{ item.name }}
            </span>
            <a-tooltip
                v-else
                destroyTooltipOnHide
                :title="$t('task.problem_task')">
                <span
                    class="cursor-pointer blue_color font-medium"
                    @click="openTask">
                    <span class="counter_rejected"> #{{item.counter}}</span>
                    {{ item.name }}
                </span>
            </a-tooltip>
        </div>
        <div v-if="item.time_tracking.length" class="mb-4">
            <div v-for="(time, index) in item.time_tracking" :key="index" class="worktime_row">
                <div class="worktime_row__item">
                    <div class="label">
                        {{ $t('task.employee') }}
                    </div>
                    <Profiler
                        :user="time.author"
                        :avatarSize="15"
                        :getPopupContainer="getPopupContainer" />
                </div>
                <div class="worktime_row__item">
                    <div class="label">
                        {{ $t('task.role') }}
                    </div>
                    {{ time.role }}
                </div>
                <div class="worktime_row__item">
                    <div class="label">
                        {{ $t('task.time_spent_short') }}
                    </div>
                    {{ time.hours_sum }} {{ $t('task.hours_short') }}
                </div>
            </div>
        </div>
        <div class="flex items-center justify-between">
            <div>
                <a-tag :color="item.status.code === 'completed' ? 'green' : 'red'">
                    {{ item.status.code === 'completed' ? $t('task.completed') : $t('task.returned') }}
                </a-tag>
            </div>
        </div>
    </a-card>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        async openTask() {
            let query = Object.assign({}, this.$route.query)
            query.task = this.item.id
            if(!this.$route.query.task) 
                this.$router.push({query})
        },
        getPopupContainer() {
            return this.$refs[`kanban_card_${this.item.id}`]
        }
    }
}
</script>

<style lang="scss" scoped>
.worktime_row{
    color: #000;
    &:not(:last-child){
        border-bottom: 1px solid var(--borderColor);
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    &__item{
        .label{
            opacity: 0.6;
            margin-bottom: 5px;
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
.task_sprint_card{
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
</style>