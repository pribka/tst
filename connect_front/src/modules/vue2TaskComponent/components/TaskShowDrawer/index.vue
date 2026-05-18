<template>
    <DrawerTemplate 
        ref="drawerTemplate"
        :width="drawerWidth"
        class="task_show_drawer"
        v-model="visible"
        :closable="false"
        useCopyLink
        useOpenLink
        usePrint
        useShare
        :loading="taskLoading"
        :shareObject="
            task ? {
                model: 'tasks.TaskModel',
                shareId: task.id,
                object: task,
                shareTitle: `${this.$t(`task.${task.task_type}`)} - ${task.name}`,
            } : null
        "
        :link="{
            task: task ? task.id : null,
            stab: tab
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="w-full flex items-center justify-between" :title="taskTitle">
                <div
                    v-if="task"
                    class="text-base font-semibold truncate label"
                    :data-guide-id="task.task_type === 'interest' ? 'interest-detail-title' : null">
                    <span v-if="task.counter" style="color:#888888;">#{{task.counter}}</span> {{task.name}}
                </div>
                <div class="flex items-center">
                    <a-button
                        v-if="task && dropActions && dropActions.edit && task.editable && !task.is_sign_task"
                        type="ui"
                        ghost
                        flaticon
                        v-tippy
                        :content="$t('task.edit')"
                        shape="circle"
                        icon="fi-rr-edit"
                        class="ml-2"
                        @click="edit()" />
                </div>
            </div>
        </template>
        <template #aside>
            <div
                v-if="columnMobile && showAside && !isMobile"
                class="mt-6 mb:mt-0 lg:mt-0"
                :sm="24"
                :lg="8">
                <TaskAside 
                    :task="task" 
                    :closeDrawer="closeDrawer"
                    :closeDrawerHan="closeDrawerHan"
                    :dropActions="dropActions"
                    :isMobile="isMobile" />
            </div>
        </template>
        <template #tabs>
            <div class="">
                <a-tabs 
                    v-if="task"
                    v-model="tab"
                    :data-guide-id="task.task_type === 'interest' ? 'interest-detail-tabs' : null"
                    @change="changeTab">
                    <a-tab-pane
                        v-for="tab in task.tabs"
                        :key="tab.code">
                        <template #tab>
                            <div class="flex items-center">
                                <span>{{ tab.name }}</span>
                                <a-badge    
                                    v-if="tab.code === 'files' && fileCount" 
                                    class="ml-1" 
                                    :count="fileCount"
                                    :overflow-count="99" />
                            </div>
                        </template>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </template>
        <div 
            class="body_wrapper task_body_wrap h-full" 
            ref="bodyWrap"
            :class="[!disabledWrapper ? '' : 'body_wrapper__full']">
            <component 
                v-if="task"
                :is="taskStep"
                :task="task"
                :isAuthor="isAuthor" />

            <div class="h-full">
                <template v-if="task">
                    <a-tabs
                        :activeKey="tab" 
                        class="body_tab"
                        :class="isMobile && 'mobile'">
                        <a-tab-pane
                            v-for="tab in task.tabs"
                            :key="tab.code" 
                            :tab="tab.name">
                            <TabSwitch
                                :tab="tab"
                                :task="task" 
                                :myTask="myTask"
                                :code="tab.code"
                                :dropActions="dropActions"
                                :reloadTask="reloadTask"
                                :edit="edit"
                                :bodyWrap="taskContainer"
                                :openTask="openTask"
                                :isOperator="isOperator"
                                :isAuthor="isAuthor"
                                :isMobile="isMobile"
                                :parentZIndex="drawerZIndex"
                                :closeDrawer="closeDrawer" />
                        </a-tab-pane>
                    </a-tabs>
                </template>
            </div>
        </div>
        <template #footer>
            <div class="w-full flex items-center">
                <template v-if="task">
                    <TaskActions 
                        v-if="!task.is_sign_task"
                        isFull
                        :item="task"
                        :editFull="edit"
                        :getPopupContainer="getPopupContainer"
                        :copyFunc="copy"
                        :closeDrawer="closeDrawer"
                        :deleteFunc="deleteTask"
                        :addSubtaskFunc="addSubtask"
                        :addTaskFunc="addTask"
                        :dropTrigger="['click']" />
                    <TaskTimer
                        v-if="!isMobile && !task.is_sign_task"
                        :task="task"
                        :dropActions="dropActions"
                        variant="footer" />
                </template>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState, mapGetters } from 'vuex'
import { clearTabQuery } from '@/utils/routerUtils.js'
import { socketEmitJoin, socketEmitLeave } from '@/utils/socketUtils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'TaskShowDrawer',
    components: {
        TaskAside: () => import('./TaskAside.vue'),
        TaskAsideHeader: () => import('./TaskAsideHeader.vue'),
        TaskTimer: () => import('./TaskTimer.vue'),
        TabSwitch: () => import('./TabWidgets/TabSwitch.vue'),
        TaskActions: () => import('../TaskActions/Drawer.vue'),
        StatusList: () => import('./StatusList.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    data() {
        return {
            taskLoading: false,
            loading: true,
            btn1Loading: false,
            btn2Loading: false,
            editStatus: false,
            tab: '',
            conference: {},
            fileCount: 0,
            closeQuery: null
        }
    },
    computed: {
        ...mapState({
            task: state => state.task.task,
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            taskTypeActiveTab: state => state.task.taskTypeActiveTab,
            taskDrawerZIndex: state => state.task.taskDrawerZIndex
        }),
        ...mapGetters({
            taskActions: 'task/taskActions'
        }),
        taskTabsSet() {
            if (!this.task || !this.task.tabs) return new Set()
            return new Set(this.task.tabs.map(item => String(item.code)))
        },
        drawerZIndex() {
            return this.$refs?.drawerTemplate?.zIndex
        },
        taskStep() {
            if(this.task?.show_step && !this.isMobile)
                return () => import('./StatusList.vue')
            else
                return null
        },
        dropActions() {
            if (!this.task) return null
            const actions = this.taskActions(this.task.task_type, this.task.id)
            if(actions)
                return actions.actions
            else
                return null
        },
        taskTitle() {
            if (!this.task) return ''
            return `${this.task.counter ? `#${this.task.counter} ` : ''}${this.task.name || ''}`.trim()
        },
        activeTab() {
            if(this.task?.tabs?.length) {
                const find = this.task.tabs.find(f => f.code === this.tab)
                if(find)
                    return find
                else
                    return null
            } else
                return null
        },
        showAside() {
            if(this.activeTab?.showAside)
                return true
            else
                return false
        },
        disabledWrapper() {
            if(this.activeTab?.disabledWrapper)
                return true
            else {
                return false
            }  
        },
        columnMobile() {
            if(this.windowWidth > 764 && !this.isMobile)
                return true
            else {
                if(this.tab === 'task')
                    return true
                else
                    return false
            }
        },
        visible: {
            get() {
                return this.$store.state.task.taskShow
            },
            set(val) {
                this.$store.commit('task/CHANGE_TASK_SHOW', val)
            }
        },
        drawerWidth() {
            if(this.windowWidth > 1300)
                return 1300
            if(this.windowWidth < 1300 && this.windowWidth > 500)
                return this.windowWidth - 30
            return this.windowWidth
        },
        isOperator() {
            return this.user?.id === this.task?.operator?.id
        },
        myTaskProcessed() {
            return this.user?.id === this.task?.owner?.id || this.user?.id === this.task?.operator?.id
        },
        isAuthor() {
            return this.user?.id === this.task?.owner?.id
        },
        myTask() {
            return this.user?.id === this.task?.owner?.id
                || this.user?.id === this.task?.operator?.id
                || this.task?.workgroup?.author === this.user?.id
                || this.task?.project?.author === this.user?.id
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        '$route.name'() {
            this.visible = false
        },
        '$route.query': {
            handler: function (val, oldVal) {
                if(val?.task && this.task && val?.task !== oldVal?.task) {
                    this.reloadTask({ id: val.task }, false)
                }
                if(val?.task) {
                    this.openTaskDrawer()
                }
            },
            deep: true
        },
        visible(val) {
            if(val) {
                if(this.editStatus)
                    this.editStatus = false
                this.getTask()
            }
        }
    },
    sockets: {
        task_update({data}) {
            if(this.task?.id === data?.id)
                this.$store.commit('task/UPDATE_SHOW_TASK_SOCKET', data)
        }
    },
    methods: {
        taskContainer() {
            return this.$refs.bodyWrap
        },
        visibleClose() {
            if(!this.editStatus)
                this.close()
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.$store.commit('task/SET_TASK_DRAWER_OPTIONS', null)
                eventBus.$emit('close_show_drawer_task')
                this.fileCount = null
                this.visibleClose()
                this.closeDrawer()
                // this.$store.commit('task/SET_PAGE_NAME', {
                //     pageName: null
                // })
            } else {
                if(!this.taskLoading)
                    this.getTask()
                this.$message.destroy()
            }
        },
        closeDrawerHan() {
            this.visible = false
        },
        closeDrawer(query = null) {
            this.closeQuery = query
            this.$store.commit('task/SET_TASK_POINT_LIST', [])
            if(this.visible)
                this.visible = false
        },
        getPopupContainer() {
            return document.querySelector('.task_body_wrap')
        },
        changeTab(val) {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            query.stab = val
            this.$router.push({query})
        },
        async deleteTask() {
            this.$confirm({
                title: this.$t('task.task_remove_message', { name: this.task.name }),
                okText: this.$t('remove'),
                cancelText: this.$t('cancel'),
                onOk: async () => {
                    try {
                        this.btn1Loading = true
                        const res = await this.$store.dispatch('task/deleteTask', this.task)
                        if(res) {
                            this.$message.success(this.$t('task.task_deleted'))
                            this.visible = false
                            const pageName = this.$store.state.task.pageName
                            eventBus.$emit('update_task_handler')
                            eventBus.$emit(`table_row_${pageName}`, {
                                action: 'delete',
                                row: this.task
                            })

                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.btn1Loading = false
                    }
                }
            })
        },
        async openTask() {
            const dTask = JSON.parse(JSON.stringify(this.task))
            const query = JSON.parse(JSON.stringify(this.$route.query))
            delete query.task
            await this.$router.replace({query})
            this.reloadTask(dTask.parent)
        },
        async openTaskById(id) {
            let query = Object.assign({}, this.$route.query)
            delete query.task
            if (this.$route.query.task) {
                await this.$router.push({query})
            }
            this.reloadTask({ id: id })
        },
        async reloadTask(item, changeQuery = true) {
            if (this.task) {
                socketEmitLeave(`detail_${this.task.id}`)
                this.$store.commit('task/CLEAR_TASK_ACTIONS', {
                    task_type: this.task.task_type,
                    id: this.task.id
                })
            }
            this.$store.commit('task/SET_TASK', null)
            if(changeQuery) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.task = item.id
                await this.$router.push({query})
            }
            this.getTask()
        },
        addSubtask() { 
            //eventBus.$emit('ADD_WATCH', {type: 'subtask', data: this.task})
            this.visible = false
            socketEmitLeave(`detail_${this.task.id}`)
            const pageName = this.$store.state.task.pageName
            this.$store.commit('task/SET_TASK_TYPE', 'task')
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'subtask', data: this.task})
        },
        addTask() {
            this.visible = false
            socketEmitLeave(`detail_${this.task.id}`)
            this.$store.commit('task/SET_TASK_TYPE', 'task')
            eventBus.$emit('ADD_WATCH', {type: 'subtask', data: this.task})
        },
        copy() { 
            this.visible = false
            socketEmitLeave(`detail_${this.task.id}`)
            const pageName = this.$store.state.task.pageName
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName
            })
            this.$store.commit('task/SET_TASK_TYPE', this.task.task_type)
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'copy', data: this.task}) 
        },
        edit() {
            this.visible = false
            this.editStatus = true
            socketEmitLeave(`detail_${this.task.id}`)
            eventBus.$emit('EDIT_TASK', {
                back: true,
                task_type: this.task.task_type || 'task'
            })
            eventBus.$emit('OPEN_EDIT_TASK')
        },
        close() {
            const hadTask = Boolean(this.$route.query?.task)
            let query = clearTabQuery({
                ...this.$route.query,
                task: undefined,
                stab: undefined,
                comment: undefined
            })
            if(hadTask) {
                if(this.closeQuery) {
                    this.$router.replace({ query })
                    query = JSON.parse(JSON.stringify(this.closeQuery))
                    this.closeQuery = null
                    setTimeout(() => {
                        this.$nextTick(() => {
                            this.$router.replace({ query })
                        })
                    }, 200)
                } else {
                    this.$router.replace({ query })
                }
            }

            if(this.task?.tabs?.length)
                this.tab = this.task.tabs[0].code
            else
                this.tab = 'task'

            if(this.task) {
                socketEmitLeave(`detail_${this.task.id}`)
                this.$store.commit('task/CLEAR_TASK_ACTIONS', {
                    task_type: this.task.task_type,
                    id: this.task.id
                })
            }
            this.$store.commit('task/SET_TASK', null)
        },
        async getTask() {
            let {task} = JSON.parse(JSON.stringify(this.$route.query))

            if(!task)
                task = this.task?.id

            if(!task)
                return

            try {
                this.taskLoading = true
                socketEmitJoin(`detail_${task}`)
                await this.$store.dispatch('task/getFullTask', task)
                await this.getFileCount(task)
                const query = JSON.parse(JSON.stringify(this.$route.query))
                if(query.stab && this.taskTabsSet.has(query.stab))
                    this.tab = query.stab
                else {
                    if(this.task?.tabs?.length) {
                        this.tab = this.task.tabs[0].code
                    } else {
                        this.tab = 'task'
                    }
                }
            } catch(error) {
                errorHandler({error})
                this.close()
                this.visible = false
            } finally {
                this.taskLoading = false
            }
        },
        async getFileCount(taskId) {
            const attachmentsCount = await this.$http(
                `attachments/${ taskId }/aggregate/`)
            this.fileCount = attachmentsCount.data.files
        },
        openTaskDrawer() {
            this.visible = true
        }
    },
    mounted() {
        if(this.$route.query?.task)
            this.openTaskDrawer()

        eventBus.$on('CLOSE_SHOW_TASK_DRAWER', () => {
            this.closeDrawer()
        })
        eventBus.$on('UPDATE_TASK_DRAWER', () => {
            if(this.visible) {
                this.$store.commit('task/SET_TASK', null)
                this.getTask()
            }
        }),
        eventBus.$on('OPEN_TASK_DRAWER', taskId => {
            this.openTaskById(taskId)
        })
    },
    beforeDestroy() {
        eventBus.$off('CLOSE_SHOW_TASK_DRAWER')
        eventBus.$off('UPDATE_TASK_DRAWER')
        eventBus.$off('OPEN_TASK_DRAWER')
        this.close()
        this.closeDrawer()
        this.$store.commit('task/SET_TASK_DRAWER_OPTIONS', null)
    }
}
</script>

<style lang="scss">
.task_show_drawer{
    .head_wrapper{
    
        height: 40px;
        border-bottom: 1px solid var(--borderColor);
        padding: 10px 30px;
        background: var(--bgColor);
    }
    .body_wrapper{
        // height: calc(100% - 120px);
        // overflow-y: scroll;
        &__padding{
            padding: 15px;
            @media (min-width: 1024px) {
                padding: 30px;
            }
        }
        &__full{
            .ant-tabs-tabpane,
            .ant-tabs-content,
            .body_tab,
            .ant-col,
            .ant-row{
                height: 100%;
            }
        }
        .parent_task{
            padding-top: 20px;
            border-top: 1px solid var(--borderColor);
        }
        .body_tab{
            & > .ant-tabs-bar{
                display: none;
            }
        }
        .body_tab.mobile {
            overflow: visible;
            .ant-collapse-content-box {
                padding-top: 5px;
                padding: 10px 15px;
            }
        }
    }
    .sidebar_item{
        &:not(:last-child){
            border-bottom: 1px solid #E5E7EF;
            padding-bottom: 15px;
        }
        &:not(:first-child){
            padding-top: 15px;
        }
        .visor_item{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
    .footer_wrapper{
        // will-change: transform;

        height: 40px;
        padding: 10px 30px;
        background: var(--bgColor);
        border-top: 1px solid var(--borderColor);
    }

    .body_contractor{
        width: 40%;
    }
}
.task_mobile_drawer {
    .body_wrapper {
        overflow-x: hidden;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        // will-change: transform;
        height: calc(100% - 128px);
    }
    .head_wrapper {
        padding: 10px 15px;
    }
    .footer_wrapper {
        padding: 10px 15px;
        height: 48px;
        .dots_btn{
            width: 55px;
        }
    }
}
</style>
