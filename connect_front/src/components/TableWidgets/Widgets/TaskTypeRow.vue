<template>
    <div 
        v-if="taskType" class="stage_badge" 
        v-tippy
        :content="taskType.label"
        :style="`background: ${taskType.bgColor};color: ${taskType.textColor};`">
        {{ taskType.smallLabel }}
    </div>
</template>
<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array]
        },
        record: {
            type: Object
        },
    },
    data() {
        return {
            taskTypeOptions: [
                { value: 'stage', label: this.$t('Stage'), smallLabel: this.$t('Stage_small'), bgColor: '#fef8eb', textColor: '#ff9a01' },
                { value: 'task', label: this.$t('Task'), smallLabel: this.$t('Task_small'), bgColor: '#e8ecfa', textColor: '#4776fe' },
                { value: 'milestone', label: this.$t('Milestone'), smallLabel: this.$t('Milestone_small'), bgColor: '#e6efe3', textColor: '#378326' },
            ],
        }
    },
    computed: {
        taskType() {
            const find = this.taskTypeOptions.find(f => f.value === this.record.task_type)
            return find || null
        }
    }
}
</script>

<style lang="scss" scoped>
.stage_badge{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-transform: uppercase;
    font-size: 12px;
    line-height: 12px;
}
</style>