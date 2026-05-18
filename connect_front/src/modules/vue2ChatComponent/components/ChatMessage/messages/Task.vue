<template>
    <div
        class="task_share_preview mt-2 mb-2"
        @click="openTask(taskItem)">
        <div class="task_share_preview__title mb-1">
            {{ $t('chat.task3') }}:
        </div>
        <KanbanItem
            :item="taskItem"
            :activeMobile="true"
            :useActions="false"
            :showStatus="true"
            :reloadTask="openTask" />
    </div>
</template>

<script>
import KanbanItem from '@/modules/vue2TaskComponent/components/Kanban/Item.vue'

export default {
    components: {
        KanbanItem
    },
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    computed: {
        taskItem() {
            return {
                ...this.messageItem.share,
                task_type: this.messageItem?.share?.task_type || 'task'
            }
        }
    },
    methods: {
        openTask(task = this.taskItem) {
            const query = JSON.parse(JSON.stringify(this.$route.query))

            if ((query.task && Number(query.task) !== task.id) || !query.task) {
                query.task = task.id
                this.$router.push({ query })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.task_share_preview{
    width: 100%;
    cursor: pointer;
}

.task_share_preview__title{
    font-size: 14px;
    font-weight: 500;
    color: #6f7785;
}

.task_share_preview ::v-deep .kanban-card{
    min-width: 0;
    cursor: pointer;
    user-select: auto;
    border: 1px solid #e3e8f2;
}

.task_share_preview ::v-deep .card_title{
    cursor: pointer;
}
</style>
