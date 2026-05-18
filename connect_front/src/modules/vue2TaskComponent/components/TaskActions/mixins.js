import eventBus from '@/utils/eventBus'
import { mapState, mapGetters } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        disabled: {
            type: Boolean,
            default: false
        },
        isFull: {
            type: Boolean,
            default: false
        },
        item: {
            type: Object,
            required: true
        },
        model: {
            type: String,
            default: 'tasks.TaskModel'
        },
        dropTrigger: {
            type: Array,
            default: () => ['click']
        },
        editFull: {
            type: Function,
            default: () => {}
        },
        copyFunc: {
            type: Function,
            default: () => {}
        },
        addSubtaskFunc: {
            type: Function,
            default: () => {}
        },
        addTaskFunc: {
            type: Function,
            default: () => {}
        },
        deleteFunc: {
            type: Function,
            default: () => {}
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        },
        showStatus: {
            type: Boolean,
            default: true
        },
        showButton: {
            type: Boolean,
            default: true
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            statusList: state => state.task.statusList,
            statusLoader: state => state.task.statusLoader
        }),
        ...mapGetters({
            taskActions: 'task/taskActions'
        }),

        actionButtons() {
            let buttons = []
            if(this.isMobile) {
                buttons = [
                    {
                        key: 'add_subtask',
                        visible: this.dropActions.add_subtask && this.item.level < 3,
                        handler: this.addSubtask,
                        icon: 'fi-rr-folder-tree',
                        label: this.$t('task.add_subtask'),
                    },
                    /*{
                        key: 'add_to_work_plan',
                        visible: this.dropActions.add_to_work_plan,
                        handler: this.addToMyWorkPlan,
                        icon: 'fi-rr-calendar-plus',
                        label: 'Добавить в план дня',
                    },*/
                    {
                        key: 'set_sprint',
                        visible: this.dropActions.set_sprint,
                        handler: this.addToSprint,
                        icon: 'fi-rr-arrow-turn-down-right',
                        label: this.$t('task.add_to_sprint')
                    },
                    {
                        key: 'unset_sprint',
                        visible: this.dropActions.unset_sprint,
                        handler: this.removeToSprint,
                        icon: 'fi-rr-cross-circle',
                        label: this.$t('task.remove_from_sprint')
                    },

                    {
                        key: 'update_operator',
                        visible: this.dropActions?.update_operator?.availability,
                        handler: this.updateOperator,
                        icon: 'fi-rr-refresh',
                        label: this.$t('task.change_person')
                    },
                    {
                        key: 'update_owner',
                        visible: this.dropActions?.update_owner?.availability,
                        handler: this.updateOwner,
                        icon: 'fi-rr-user-add',
                        label: this.$t('task.delegate_task')
                    },

                    {
                        key: 'share',
                        visible: this.dropActions.share,
                        handler: this.share,
                        icon: 'fi-rr-share',
                        label: this.$t('task.share_to_chat'),
                    },
                    {
                        key: 'edit',
                        visible: this.dropActions.edit,
                        handler: this.edit,
                        icon: 'fi-rr-edit',
                        label: this.$t('task.edit'),
                    },
                    {
                        key: 'copy',
                        visible: this.dropActions.copy,
                        handler: this.copy,
                        icon: 'fi-rr-copy-alt',
                        label: this.$t('task.copy'),
                    },
                ]
            } else {
                buttons = [
                    {
                        key: 'add_subtask',
                        visible: this.dropActions.add_subtask && this.item.level < 3,
                        handler: this.addSubtask,
                        icon: 'fi-rr-folder-tree',
                        label: this.$t('task.add_subtask'),
                    },
                    {
                        key: 'set_sprint',
                        visible: this.dropActions.set_sprint,
                        handler: this.addToSprint,
                        icon: 'fi-rr-arrow-turn-down-right',
                        label: this.$t('task.add_to_sprint')
                    },
                    {
                        key: 'unset_sprint',
                        visible: this.dropActions.unset_sprint,
                        handler: this.removeToSprint,
                        icon: 'fi-rr-cross-circle',
                        label: this.$t('task.remove_from_sprint')
                    },

                    {
                        key: 'update_operator',
                        visible: this.dropActions?.update_operator?.availability,
                        handler: this.updateOperator,
                        icon: 'fi-rr-refresh',
                        label: this.$t('task.change_person')
                    },
                    {
                        key: 'update_owner',
                        visible: this.dropActions?.update_owner?.availability,
                        handler: this.updateOwner,
                        icon: 'fi-rr-user-add',
                        label: this.$t('task.delegate_task')
                    },

                    {
                        key: 'share',
                        visible: this.dropActions.share,
                        handler: this.share,
                        icon: 'fi-rr-share',
                        label: this.$t('task.share_to_chat'),
                    },
                    {
                        key: 'edit',
                        visible: this.dropActions.edit,
                        handler: this.edit,
                        icon: 'fi-rr-edit',
                        label: this.$t('task.edit'),
                    },
                    {
                        key: 'copy',
                        visible: this.dropActions.copy,
                        handler: this.copy,
                        icon: 'fi-rr-copy-alt',
                        label: this.$t('task.copy'),
                    },
                ]
            }

            return buttons.filter(button => button.visible)
        },
        dropActions() {
            const actions = this.taskActions(this.item.task_type, this.item.id)
            if(actions)
                return actions.actions
            return null
        },
        filteredList() {
            if(this.statusList?.[this.item.task_type]?.length)
                return this.statusList[this.item.task_type]
            return []
        },
        myTask() {
            if (!this.user?.id) { return }
            return [
                this.item.owner?.id,
                this.item.workgroup?.author,
                this.item.sprint?.author,
                this.item.project?.author,
            ].includes(this.user.id)
        },
        isAuthor() {
            if (!this.user?.id) { return }
            return [
                this.item.owner?.id,
                this.item.workgroup?.author,
                this.item.sprint?.author,
                this.item.project?.author,
            ].includes(this.user.id)
        },
        isOperator() {
            return this.user?.id === this.item.operator?.id
        },
        isLogistic() {
            return this.item?.task_type === 'logistic'
        }
    },
    data() {
        return{
            loading: false,
            actionLoading: false,
            changinField: null
        }
    },
    methods: {
        updateOwner() {
            this.changinField = 'owner'
            this.$refs?.changeUserRef?.open()
        },
        updateOperator() {
            this.changinField = 'operator'
            this.$refs?.changeUserRef?.open()
        },
        changeUser(user) {
            const payload = {
                [this.changinField]: user.id
            }
            const url = this.changinField === 'owner' ?
                `/tasks/task/${this.item.id}/update_owner/` :
                this.changinField === 'operator' ?
                `/tasks/task/${this.item.id}/update_operator/` : null
               
            this.$http.put(url, payload)
                .then(({ data }) => {
                    this.$store.commit('task/TASK_CHANGE_FIELD', { key: this.changinField, value: data[this.changinField], task: this.item})
                    //eventBus.$emit('update_task_handler') 
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: data,
                            list: 'taskList'
                        })
                    }
                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'update',
                        row: data
                    })
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        addToSprint() {
            eventBus.$emit('task_add_sprint', this.item)
        },
        addToMyWorkPlan() {
            eventBus.$emit('add_task_in_my_work_plan', this.item)
        },
        async removeToSprint() {
            try {
                this.loading = true
                const { data } = await this.$http.put(`tasks/task/${this.item.id}/set_sprint/`, {
                    sprint: null
                })
                if(data) {
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: this.item,
                            list: 'taskList'
                        })
                    }
                    if(this.isFull)
                        await this.getTaskActions()
                    this.$message.success(this.$t('task.removed_from_sprint'))
                    eventBus.$emit('update_sprint_detail')
                    eventBus.$emit('sprint_update_table_reload')
                    //eventBus.$emit('update_task_handler')
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        checkRole(actions) {
            const all = actions.roles.find(f => f === 'all')

            if(all) { return true }
            const operator = actions.roles.find(f => f === 'operator')
            if(operator)
                return this.myTask

            const owner = actions.roles.find(f => f === 'owner')
            if(owner)
                return this.isAuthor
        },
        visibleChange(visible) {
            if(visible) {
                this.getTaskActions()
            } else {
                this.clearActions()
            }
        },
        clearActions() {
            this.$store.commit('task/CLEAR_TASK_ACTIONS', {
                task_type: this.item.task_type,
                id: this.item.id
            })
        },
        async getTaskActions() {
            try {
                this.actionLoading = true
                await this.$store.dispatch('task/getTaskActions', {
                    task_type: this.item.task_type,
                    id: this.item.id
                })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.actionLoading = false
            }
        },
        changeStatus(status) {
            const cooperator = this.item?.cooperators?.find(cooperator => cooperator.user.id === this.user.id)
            if (cooperator && !(this.isAuthor || this.isOperator)) {
                return this.changeCooperatorStatus(status, cooperator.id)
            }
            return this.changeTaskStatus(status)
        },
        async changeTaskStatus(status) {
            try {
                this.loading = true
                const data = await this.$store.dispatch('task/changeStatus', {
                    task: this.item, 
                    status
                })

                await this.$store.dispatch('task/getTaskActions', { 
                    task_type: data.task_type, 
                    id: data.id 
                })

                const pageName = this.pageName || this.$store.state.task.pageName
                eventBus.$emit(`table_row_${pageName}`, {
                    action: 'update',
                    row: data
                })
                if (this.$store.hasModule('workplan')) {
                    this.$store.dispatch('workplan/updateItem', {
                        item: this.item,
                        list: 'taskList'
                    })
                }
                //eventBus.$emit('update_task_handler')
                eventBus.$emit('update_task_data')
                eventBus.$emit('update_task_data_inject')
                eventBus.$emit('update_task_data_detail')
                eventBus.$emit('update_task_data_detail_inject')
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        changeCooperatorStatus(status, cooperatorId) {
            this.loading = true
            const payload = {
                id: cooperatorId,
                status: status.code
            }
            const url = `tasks/task/${this.item.id}/cooperator_status/`
            this.$http.put(url, payload)
                .then(({ data }) => {
                    if (this.$store.state.task.task) {
                        const cooperator = this.$store.state.task.task.cooperators.find(cooperator => cooperator.id === data.id)
                        cooperator.status.code = data.status
                        if (this.$store.hasModule('workplan')) {
                            this.$store.dispatch('workplan/updateItem', {
                                item: this.item,
                                list: 'taskList'
                            })
                        }
                        //eventBus.$emit('update_task_handler')
                    }
                })
                .catch(error => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.loading = false
                })

        },
        share() {
            const shareParams = {
                model: this.model,
                shareId: this.item.id,
                object: this.item,
                shareUrl: `${window.location.origin}/?task=${this.item.id}`,
                shareTitle: `${this.$t(`task.${this.item.task_type}`)} - ${this.item.name}`,
            }
            try {
                this.$store.commit('share/SET_SHARE_PARAMS', shareParams)
            } catch(error) {
                this.$message.error(this.$t('task.file_share_error'))
                console.error(error)
            }
        
        },
        async deleteTask() {
            this.$confirm({
                title: this.$t('task.task_remove_message', { name: this.item.name }),
                okText: this.$t('remove'),
                cancelText: this.$t('cancel'),
                onOk: async () => {
                    try {
                        this.loading = true
                        const res = await this.$store.dispatch('task/deleteTask', this.item)
        
                        if(res) {
                            if (this.item.project) {
                                this.$store.commit('projects/DELETE_TABLE_ROW', { record: this.item, tableKey: 'project_tasks' })
                            }
                            if (this.$store.hasModule('workplan')) {
                                this.$store.dispatch('workplan/deleteItem', {
                                    item: this.item,
                                    list: 'taskList'
                                })
                            }
                            this.$message.success(this.$t('task.task_deleted'))
                            const pageName = this.pageName || this.$store.state.task.pageName
                            eventBus.$emit(`update_filter_${pageName}`)
                            //eventBus.$emit('update_task_handler')
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        async edit() {
            try {
                this.loading = true
                const res = await this.$store.dispatch('task/getFullTask', this.item.id)
                const pageName = this.pageName || this.$store.state.task.pageName
                this.$store.commit('task/SET_PAGE_NAME', {
                    pageName
                })
                if(res)
                    eventBus.$emit('EDIT_TASK', {
                        back: false,
                        task_type: this.item.task_type || 'task'
                    })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        addSubtask() {
            const pageName = this.pageName || this.$store.state.task.pageName
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'subtask', data: this.item})
        },
        async copy() {
            try {
                this.loading = true
                const res = await this.$store.dispatch('task/getFullTask', this.item.id)
                if(res) {
                    const pageName = this.pageName || this.$store.state.task.pageName
                    this.$store.commit('task/SET_PAGE_NAME', {
                        pageName
                    })
                    eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'copy', data: res}) 
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        eventBus.$on(`task_update_actions_${this.item.id}`, () => {
            this.getTaskActions()
        })
    },
    beforeDestroy() {
        eventBus.$off(`task_update_actions_${this.item.id}`)
    }
}
