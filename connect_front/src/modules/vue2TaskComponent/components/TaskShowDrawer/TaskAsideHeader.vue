<template>
    <div class="task_sidebar_wrapper">
        <template v-if="task">
            <div class="aside_item flex justify-between items-start">
                <div>
                    <div class="mb-1 text-sm font-semibold">
                        {{$t('task.dead_line')}}
                    </div>
                    <DeadLine :taskStatus="task.status" :date="task.dead_line" />
                </div>
                <TaskStatus :status="task.status" />
            </div>
            <div 
                v-if="asideSetting.date_start_plan && task.date_start_plan" 
                class="aside_item">
                <div class="mb-1 text-sm font-semibold">
                    {{ asideSetting.date_start_plan.label }}
                </div>
                <div>{{$moment(task.date_start_plan).format($t('task.date_format'))}}</div>
            </div>
            <div class="aside_item">
                <div class="mb-1 text-sm font-semibold">
                    {{$t('task.priority')}}
                </div>
                <div class="flex items-center">
                    <a-badge :status="priorityCheck.color" />
                    {{priorityCheck.name}}
                </div>
            </div>
        </template>
        <template v-else>
            <a-skeleton 
                active 
                avatar 
                :paragraph="{ rows: 4 }" />
            <a-skeleton 
                active 
                avatar 
                :paragraph="{ rows: 4 }" />
        </template>
    </div>
</template>

<script>
import {priorityList} from '../../utils'
export default {
    components: {
        DeadLine: () => import('../DeadLine'),
        TaskStatus: () => import('../TaskStatus')
    },
    props: {
        task: {
            type: Object,
            default: () => null
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            priorityList
        }
    },
    computed: {
        asideSetting() {
            return this.task.aside_settings ? this.task.aside_settings : null 
        },
        priorityCheck() {
            const find = this.priorityList.find(item => item.value === this.task.priority)
            if(find)
                return find
            else
                return null
        }
    },
}
</script>

<style lang="scss" scoped>
.aside_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
</style>