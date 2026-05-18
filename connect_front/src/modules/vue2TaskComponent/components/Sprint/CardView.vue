<template>
    <a-card 
        class="cardView"
        :class="isMobile && 'cardView_Mobile'">
        <a-button 
            v-if="sprint.status !== 'completed'"
            type="primary"
            :block="isMobile"
            size="large"
            class="mb-4"
            @click="changeStatus(sprint, allData)">
            {{sprint.status === "new" ? $t('task.to_work') : $t('task.to_completed') }}
        </a-button>
        <div class="">
            <span class=" font-semibold">
                {{ $t('sprint.spirnt_target') }}: 
            </span>
            <span>
                {{sprint.target}}
            </span>
        </div>
        <div class="flex mt-4">
            <span class="font-semibold">
                {{ $t('task.dead_line') }}: 
            </span>
                   
            <DateWidget class="ml-2" :date="sprint.dead_line" /> 
               
        </div>
        <div class="flex mt-4">
            <span class="font-semibold">
                {{ $t('task.task_duration') }}: 
            </span>
                   
            <span class="ml-2">{{getTimeInterval(sprint.time_interval)}}</span>
        </div>
        <div class="flex mt-4">
            <span class="font-semibold">
                {{ $t('task.task-list-page') }}:
            </span>
                   
            <TasksCount class="ml-2"  :record="sprint" />
        </div>
        <div class="flex mt-4">
            <span class="font-semibold mr-2">
                {{ $t('task.status') }}: 
            </span>
            <SprintStatus :sprint="sprint" />
           
        </div>
        <div class="mt-4" v-if="sprint.expected_result && sprint.expected_result.length">
            <span class="font-semibold">
                {{ $t('sprint.expected_result') }}:
            </span>
            <a-list bordered :data-source="sprint.expected_result">
                <a-list-item class="mt-1" slot="renderItem" slot-scope="item">
                    {{ item }}
                </a-list-item>
            </a-list> 
        </div>
    </a-card>
</template>

<script>
import DateWidget from './components/DateWidget.vue'
import actions from './actions'
import TasksCount from './components/TasksCount.vue'
import SprintStatus from './components/SprintStatus.vue'
export default {
    components: {DateWidget, TasksCount, SprintStatus},
    mixins: [actions],
    props: {
        sprint: Object,
        allData: Array
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style scoped lang="scss">
.cardView{
    min-width: 350px;
    max-width: 350px;
    // height: 100%;
    scroll-snap-align: start;
    flex-grow: 0;
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    flex-shrink: 0;
    // padding-bottom: 5px;
    overflow: hidden;
    
}
.cardView_Mobile {
    min-width: auto;
    max-width: 100%;
}
</style>
<style lang="scss">
.cardView .ant-list-item{
    padding-left: 12px;
    padding-right: 12px;
}
</style>