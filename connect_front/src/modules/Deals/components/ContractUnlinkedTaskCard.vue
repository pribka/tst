<template>
    <div class="contract_unlinked_task" :class="{ 'is-selected': selected }" @click="$emit('toggle', task.id)">
        <a-card
            size="small"
            :bordered="false"
            class="kanban-card">
            <div class="card_title flex items-start justify-between truncate mb-2">
                <div class="flex truncate">
                    <a-checkbox
                        class="contract_unlinked_task__checkbox"
                        :checked="selected"
                        @click.stop
                        @change="$emit('toggle', task.id)" />
                    <span
                        v-if="task.priority === 3"
                        class="priority priority_large"
                        :title="$t('task.large_priority')">
                        <i class="fi fi-rr-bolt" />
                    </span>
                    <span
                        v-if="task.priority === 4"
                        class="priority priority_very_large"
                        :title="$t('task.very_large_priority')">
                        <i class="fi fi-rr-flame" />
                    </span>
                    <span
                        v-if="task.priority === 0"
                        class="priority priority_low"
                        :title="$t('task.very_low_priority')">
                        <i class="fi fi-rr-hourglass-start" />
                    </span>
                    <span class="blue_color card_name truncate font-medium" @click.stop="$emit('open', task.id)">
                        #{{ task.counter || '-' }} {{ task.name || '-' }}
                    </span>
                </div>
            </div>

            <div v-if="projectName" class="task_project truncate">
                {{ projectName }}
            </div>

            <div class="flex items-center justify-between mt-1">
                <DeadAndStart :task="task" responsive />

                <div class="flex items-center">
                    <TaskStatus
                        v-if="task.status"
                        class="mr-2"
                        :status="task.status" />

                    <div class="users_info flex items-center" :ref="`kanban_card_${task.id}`">
                        <div v-if="task.owner" class="flex">
                            <Profiler
                                :user="task.owner"
                                :showUserName="false"
                                :avatarSize="22"
                                :getPopupContainer="getPopupContainer" />
                        </div>
                        <template v-if="task.operator && task.operator.id != 0">
                            <i class="fi fi-rr-angle-small-right mx-1 text-xs" />
                            <div class="flex">
                                <Profiler
                                    :user="task.operator"
                                    :showUserName="false"
                                    :avatarSize="22"
                                    :getPopupContainer="getPopupContainer" />
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </a-card>
    </div>
</template>

<script>
export default {
    name: 'ContractUnlinkedTaskCard',
    components: {
        DeadAndStart: () => import('@/modules/vue2TaskComponent/components/DeadAndStart.vue'),
        TaskStatus: () => import('@/modules/vue2TaskComponent/components/TaskStatus.vue'),
    },
    props: {
        task: {
            type: Object,
            required: true,
        },
        selected: {
            type: Boolean,
            default: false,
        },
    },
    computed: {
        projectName() {
            return this.task?.project?.name || this.task?.workgroup?.name || ''
        },
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`kanban_card_${this.task.id}`] || this.$el
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_unlinked_task {
    border: 1px solid transparent;
    border-radius: var(--borderRadius);
    cursor: pointer;
    transition: border-color .2s ease, box-shadow .2s ease;

    &.is-selected {
        border-color: #2f5ff5;
        box-shadow: 0 6px 16px rgba(47, 95, 245, 0.12);
    }
}

.kanban-card {
    min-width: 270px;
    user-select: none;
    background: #f7f9fc;
    box-shadow: initial !important;
    border: 0;
    border-radius: var(--borderRadius);

    &::v-deep {
        .ant-card-body {
            padding: 12px;
        }
    }

    .card_title {
        cursor: default;
    }

    .card_name {
        cursor: pointer;
    }

    .task_project {
        font-size: 13px;
        color: #656565;
        line-height: 15px;
    }

    .priority {
        display: block;
        min-width: 14px;
        min-height: 14px;
        margin-right: 5px;

        &.priority_very_large {
            color: rgb(255, 92, 92);
        }

        &.priority_large {
            color: rgb(255, 154, 1);
        }

        &.priority_low {
            color: rgb(68, 70, 72);
        }
    }
}

.contract_unlinked_task__checkbox {
    flex-shrink: 0;
    margin-right: 8px;
}
</style>
