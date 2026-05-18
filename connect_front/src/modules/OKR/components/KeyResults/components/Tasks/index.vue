<template>
    <a-spin :spinning="loading" class="tasks-wrapper" ref="tasksWrapper">
        <div v-if="showEmpty" class="no-tasks-alert">
            <a-alert :message="$t('okr.noTasksForKeyResult')" type="info" banner/>
        </div>
        <div v-else class="tasks-list" ref="objList">
            <div v-for="t in tasks" :key="t.id" class="tasks-item">
                <a-popover title="" :mouseEnterDelay="1">
                    <template slot="content">
                        {{ $t('okr.initiative') }}
                    </template>
                    <div class="type rounded t-type">{{ $t('okr.i') }}</div>
                </a-popover>
                <a-popover title="" :mouseEnterDelay="1">
                    <template slot="content">
                        {{ `${t.counter ? `#${t.counter }` : ''}${t.name}` }}
                    </template>
                    <div
                        v-if="t.has_view_permission"
                        class="name can-be-opened"
                        @click="openTask(t.id)">
                        {{ `${t.counter ? `#${t.counter }` : ''}${t.name}` }}
                    </div>
                    <div v-else class="name">{{ `${t.counter ? `#${t.counter }` : ''}${t.name}` }}</div>
                </a-popover>
                <div class="operator">
                    <Profiler
                        :avatarSize="20"
                        nameClass="okr-operator-profiler"
                        :popoverText="$t('okr.operator')"
                        :showUserName="true"
                        :user="t.operator" />
                </div>
                <div class="dead-line">
                    <div v-if="t?.dead_line">{{ $moment(t.dead_line).format(dateFormat) }}</div>
                    <div v-else class='text-gray-300'>{{ $t('okr.deadlineNotSpecified') }}</div>
                </div>
                <div class="status" ref="tStatus">
                    <a-tag :color="t.status.color" class="h-[28px]">
                        {{ t.status.name }}
                    </a-tag>
                    <TaskActions
                        :key="`actions_button_${t.id}`"
                        shape="default"
                        :getPopupContainer="getPopupContainer"
                        :item="t"
                        :disabled="!t.has_view_permission" />
                    <a-popconfirm
                        v-if="isEditAvailable"
                        prefixCls="delete-task-confirm ant-popover"
                        :title="$t('okr.confirmRemoveTaskFromInitiative')"
                        :ok-text="$t('okr.delete')"
                        :cancel-text="$t('okr.cancel')"
                        :getPopupContainer="getPopupContainer"
                        placement="topRight"
                        @confirm="removeTask(t)">
                        <a-button
                            v-tippy="{ content: $t('okr.delete') }"
                            class="delete-button"
                            type="ui"
                            ghost
                            icon="fi-rr-trash"
                            flaticon />
                    </a-popconfirm>
                </div>
            </div>
        </div>
        <div v-if="isAddTaskAvailable" class="add-task">
            <div @click="open">{{ $t('okr.addTaskButton') }}</div>
        </div>
        <a-modal
            v-model="visible"
            :title="$t('okr.selectOrCreateTask')"
            :afterClose="afterClose">
            <AddTask
                ref="addInitiative"/>
            <template #footer>
                <div class="w-full flex justify-between">
                    <div class="flex gap-1 items-center">
                        <a-button type="primary" size="large" :loading="loading" @click="submit">
                            {{ $t('okr.addButton') }}
                        </a-button>
                        <a-button type="ui" ghost size="large" @click="close()">
                            {{ $t('okr.cancel') }}
                        </a-button>
                    </div>
                </div>
            </template>
        </a-modal>
    </a-spin>
</template>
<script>
import AddTask from './components/AddTask.vue'
import TaskActions from '@apps/vue2TaskComponent/components/TaskActions/List.vue'
import { mapMutations } from 'vuex'
export default {
    name: 'Tasks',
    components: {
        AddTask,
        TaskActions
    },
    props: {
        keyResult: {
            type: Object,
            required: true
        },
        tasks: {
            type: Array,
            default: () => []
        },
        viewOnly: {
            type: Boolean,
            default: true
        },
    },
    computed: {
        showEmpty() {
            return this.tasks.length === 0
        },
        isEditAvailable() {
            if (this.viewOnly) {
                return false
            } else {
                return this.keyResult?.actions ? this.keyResult?.actions.edit : false
            }
        },
        isAddTaskAvailable() {
            return !this.viewOnly
        }
    },
    data() {
        return {
            loading: false,
            krLoading: false,
            visible: false,
            dateFormat: 'DD.MM.YYYY'
        }
    },
    methods: {
        ...mapMutations({
            ADD_TASK: 'okr/ADD_TASK',
            REMOVE_TASK: 'okr/REMOVE_TASK',
        }),
        getPopupContainer() {
            return this.$refs.tasksWrapper.$el
        },
        setLoading(value) {
            this.krLoading = value
        },
        setInitiatives(value) {
            this.tasks = value
        },
        close() {
            this.visible = false
        },
        open() {
            this.visible = true
        },
        afterClose(vis) {
            if (!vis) {
                this.$nextTick(() => {
                    const el = this.$refs.addInitiative || null
                    if (el) el.resetForm()
                })
            }
        },
        submit() {
            this.$refs.addInitiative.$refs.initiative_form.validate(async valid => {
                if (valid) {
                    const payload = {
                        task: this.$refs.addInitiative.form.task.id
                    }
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/okr/key_results/${this.keyResult.id}/add_task/`, payload)
                        if(data) {
                            this.$message.success(this.$t('okr.taskAdded'))
                            this.ADD_TASK({ keyResult: this.keyResult.id, task: data })
                            this.close()
                        }
                    } catch(error) {
                        console.log(error)
                        if (error?.length) this.$message.error(error.join(", "))
                        else this.$message.error(this.$t("okr.error"))
                    } finally {
                        this.loading = false
                    }
                } else {
                    return false
                }
            })
        },
        async removeTask(task) {
            this.loading = true
            const payload = {
                task: task.id
            }
            try {
                await this.$http.post(`/okr/key_results/${this.keyResult.id}/remove_task/`, payload)
                this.$message.success(this.$t('okr.taskRemovedFromInitiative'))
                this.REMOVE_TASK({ keyResultID: this.keyResult.id, taskID: task.id })
            } catch(error) {
                console.log(error)
                if (error?.length) this.$message.error(error.join(", "))
                else this.$message.error(this.$t("okr.error"))
            } finally {
                this.loading = false
            }
        },
        openTask(taskID) {
            let query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== taskID || !query.task) {
                query.task = taskID
                this.$router.push({query})
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.tasks-wrapper {
    min-height: 20px;
    width: 100%;
    .no-tasks-alert {
        padding-left: 40px;
        height: 60px;
        display: flex;
        align-items: center;
    }
    .tasks-list {
        display: flex;
        flex-direction: column;
        .tasks-item {
            min-width: 1038px;
            display: grid;
            grid-template-columns: 46px 1fr 140px 70px 588px;
            grid-template-rows: 60px;
            column-gap: 8px;
            align-items: center;
            padding-right: 8px;
            .name, .operator, .dead-line {
                padding: 8px 4px;
                font-size: 12px;
                color: #2D2D2D;
            }
            .name {
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                line-height: 1.5;
                max-height: calc(3 * 1.5em);
                word-break: break-word;
                padding-top: 0;
                padding-bottom: 0;
            }
            .can-be-opened {
                cursor: pointer;
                    color: #4777FF;
                    &:hover {
                        text-decoration: underline;
                    }
            }
            .status {
                display: flex;
                justify-content: space-between;
                align-items: center;
                justify-self: end;
                gap: 8px;
            }
            &:not(:last-child){
                border-bottom: 1px solid #DADADA;
            }
            .delete-button {
                color: red;
                font-size: 12px;
            }
            .type {
                justify-self: center;
            }
            .rounded {
                height: 20px;
                width: 20px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .t-type {
                background-color: #E8EDFA;
                color: #4777FF;
            }
        }
    }
    .add-task {
        height: 60px;
        padding-left: 40px;
        padding-right: 0;
        display: flex;
        align-items: center;
        cursor: pointer;
        color: #4777FF;
        border-top: 1px solid #DADADA;
    }
}
</style>