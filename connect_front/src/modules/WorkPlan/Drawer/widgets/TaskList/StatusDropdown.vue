<template>
    <div class="mr-2">
        <template v-if="isActive">
            <template v-if="isMobile">
                <a-spin :spinning="statusLoading" size="small" @click.stop="visible = true">
                    <a-tag :color="task.status.color" class="task_status flex items-center cursor-pointer">
                        {{ task.status.name }}
                        <i class="fi fi-rr-angle-small-down ml-1" />
                    </a-tag>
                </a-spin>
                <ActivityDrawer 
                    v-model="visible" 
                    @afterVisibleChange="visibleChange">
                    <ActivityItem
                        v-if="loading"
                        key="menu_loader">
                        <div class="w-full flex justify-center">
                            <a-spin size="small" />
                        </div>
                    </ActivityItem>
                    <ActivityItem
                        v-for="status in cStatusFiltered"
                        :key="status.code"
                        @click="changeStatus(status)">
                        <div v-if="status.color !== 'default'"  class="mob_badge">
                            <a-badge :color="status.color" />
                        </div>
                        {{ status.btn_title ? status.btn_title : status.name }}
                    </ActivityItem>
                </ActivityDrawer>
            </template>
            <a-dropdown 
                v-else
                :getPopupContainer="popupContainer"
                :trigger="['click']" 
                :disabled="statusLoading"
                @visibleChange="visibleChange">
                <a-spin :spinning="statusLoading" size="small" @click.stop="() => {}">
                    <a-tag :color="task.status.color" class="task_status flex items-center cursor-pointer">
                        {{ task.status.name }}
                        <i class="fi fi-rr-angle-small-down ml-1" />
                    </a-tag>
                </a-spin>
                <a-menu slot="overlay">
                    <a-menu-item v-if="loading" key="loading" class="flex justify-center">
                        <a-spin :spinning="loading" size="small" />
                    </a-menu-item>
                    <a-menu-item 
                        v-for="status in cStatusFiltered"
                        :key="status.code"
                        class="flex items-center"
                        @click="changeStatus(status)">
                        <a-badge 
                            v-if="status.color !== 'default'" 
                            :color="status.color" />
                        {{ status.btn_title ? status.btn_title : status.name }}
                    </a-menu-item>
                </a-menu>
            </a-dropdown>
        </template>
        <a-tag v-else :color="task.status.color" class="task_status cursor-pointer">
            {{ task.status.name }}
        </a-tag>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        popupContainer: {
            type: Function,
            default: () => document.body
        }
    },
    components: {
        ActivityItem,
        ActivityDrawer
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() { 
            return this.$store.state.isMobile
        },
        isActive() {
            return this.task.is_executor || this.task.is_owner
        },
        isAuthor() {
            if (!this.user?.id) { return }
            return [
                this.fullTask.owner?.id,
                this.fullTask.workgroup?.author,
                this.fullTask.sprint?.author,
                this.fullTask.project?.author,
            ].includes(this.user.id)
        },
        isOperator() {
            return this.user?.id === this.fullTask.operator?.id
        },
        cStatusFiltered() {
            const changeCooperatorStatuses = this.actionsInfo?.change_cooperator_status?.available_statuses
            const onlyCooperator = this.actionsInfo?.change_cooperator_status?.only_coop
            if (onlyCooperator && changeCooperatorStatuses?.length)
                return changeCooperatorStatuses.filter(f => f.code !== this.task.status?.code)
            const availableStatuses = this.actionsInfo?.change_status?.available_statuses
            if (availableStatuses?.length)
                return availableStatuses.filter(f => f.code !== this.task.status?.code)
            return []
        },
    },
    data() {
        return {
            loading: false,
            statusLoading: false,
            actionsInfo: null,
            fullTask: null,
            visible: false
        }
    },
    methods: {
        async changeTaskStatus(status) {
            try {
                this.statusLoading = true
                const data = await this.$store.dispatch('task/changeStatus', {
                    task: this.fullTask, 
                    status
                })

                await this.$store.dispatch('task/getTaskActions', { 
                    task_type: data.task_type, 
                    id: data.id 
                })

                const pageName = this.$store.state.task.pageName
                eventBus.$emit(`table_row_${pageName}`, {
                    action: 'update',
                    row: data
                })
                if (this.$store.hasModule('workplan')) {
                    this.$store.dispatch('workplan/updateItem', {
                        item: this.fullTask,
                        list: 'taskList'
                    })
                }
                eventBus.$emit('update_task_data')
                eventBus.$emit('update_task_data_inject')
                eventBus.$emit('update_task_data_detail')
                eventBus.$emit('update_task_data_detail_inject')
            } catch(error) {
                errorHandler({error})
            } finally {
                this.statusLoading = false
            }
        },
        changeCooperatorStatus(status, cooperatorId) {
            this.statusLoading = true
            this.$http.put(`tasks/task/${this.task.id}/cooperator_status/`, {
                id: cooperatorId,
                status: status.code
            })
                .then(({}) => {
                    if (this.$store.state.task.task) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: this.task,
                            list: 'taskList'
                        })
                    }
                })
                .catch(error => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.statusLoading = false
                })
        },
        changeStatus(status) {
            const cooperator = this.fullTask?.cooperators?.find(cooperator => cooperator.user.id === this.user.id)
            if (cooperator && !(this.isAuthor || this.isOperator))
                return this.changeCooperatorStatus(status, cooperator.id)
            return this.changeTaskStatus(status)
        },
        visibleChange(vis) {
            if(vis) {
                if(!this.actionsInfo)
                    this.getStatusList()
            }
        },
        async getTask() {
            try {
                const { data } = await this.$http.get(`/tasks/task/${this.task.id}/`)
                if(data) {
                    this.fullTask = data
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getStatusList() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/tasks/${this.task.id}/action_info/`)
                if(data?.actions) {
                    await this.getTask()
                    this.actionsInfo = data.actions
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.task_status{
    line-height: 24px;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 30px;
    font-size: 13px;
}
</style>