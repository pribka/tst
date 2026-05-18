<template>
    <a-drawer
        :width="width"
        class="task_show_drawer emded_drawer"
        :visible="visible"
        :closable="false"
        :zIndex="taskDrawerZIndex"
        :key="visible"
        :mask="mask"
        :getContainer="container"
        :wrap-style="wrapStyle"
        :afterVisibleChange="afterVisibleChange"
        @close="closeDrawer()">
        <div class="flex items-center justify-between head_wrapper">
            <div
                v-if="task"
                class="text-base font-semibold truncate label">
                {{task.name}} - {{task.counter}}
            </div>
            <a-skeleton
                v-else
                active
                :paragraph="{ rows: 1 }" />
            <a-button
                type="link"
                class="ml-2 text-current"
                icon="close"
                @click="closeDrawer()" />
        </div>
        <div class="tab_wrapper">
            <a-tabs 
                v-if="task"
                v-model="tab"
                @change="changeTab">
                <a-tab-pane
                    v-for="tab in task.tabs"
                    :key="tab.code">
                    <template #tab>
                        <div class="flex">
                            <span>{{ tab.name }}</span>
                            <a-badge 
                                v-if="tab.code === 'comments' && tab.counter" 
                                class="ml-1" 
                                :count="commentsCount" />
                        </div>
                    </template>
                </a-tab-pane>
            </a-tabs>
        </div>
        <div class="body_wrapper task_body_wrap">
            <component 
                v-if="task"
                :is="taskStep"
                :task="task"
                :isAuthor="isAuthor" />

            <a-row :gutter="50">
                <a-col
                    v-if="showAsideHeader && columnMobile && showAside && isMobile"
                    class="mb-6">
                    <TaskAsideHeader 
                        :task="task" 
                        :closeDrawer="closeDrawer" />
                </a-col>
                <a-col 
                    :sm="24" 
                    :lg="!showAside || isMobile ? 24 : 16">
                    <template v-if="task">
                        <a-tabs
                            :activeKey="tab" 
                            class="body_tab">
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
                                    :checkRole="checkRole"
                                    :reloadTask="reloadTask"
                                    :getCommentsCount="getCommentsCount"
                                    :edit="edit"
                                    :isAuthor="isAuthor"
                                    :hideDeliveryMap="hideDeliveryMap"
                                    :openTask="openTask"
                                    :isOperator="isOperator"
                                    :isMobile="isMobile" />
                            </a-tab-pane>
                        </a-tabs>
                    </template>
                    <template v-else>
                        <a-skeleton
                            active
                            :paragraph="{ rows: 6 }" />
                    </template>
                </a-col>
                <a-col
                    v-if="columnMobile && showAside && !isMobile"
                    class="mt-6 mb:mt-0 lg:mt-0"
                    :sm="24"
                    :lg="8">
                    <TaskAside 
                        :task="task" 
                        :closeDrawer="closeDrawer"
                        :isMobile="isMobile" />
                </a-col>
            </a-row>
        </div>
        <div class="flex items-center footer_wrapper">
            <template v-if="task">
                <TaskActions 
                    :ref="`${task.id}_task_actions`"
                    :item="task"
                    :editFull="edit"
                    :getPopupContainer="getPopupContainer"
                    :copyFunc="copy"
                    :deleteFunc="deleteTask"
                    :addSubtaskFunc="addSubtask"
                    :dropTrigger="['hover']" />
            </template>
            <a-skeleton 
                v-else 
                active 
                :paragraph="{ rows: 1 }" />
            <a-button 
                v-if="isMobile"
                type="default"
                block 
                @click="closeDrawer()">
                {{ $t('close') }}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState, mapGetters } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        TaskAside: () => import('./TaskAside.vue'),
        TaskAsideHeader: () => import('./TaskAsideHeader.vue'),
        TabSwitch: () => import('./TabWidgets/TabSwitch.vue'),
        TaskActions: () => import('../TaskActions/Drawer.vue'),
        StatusList: () => import('./StatusList.vue')
    },
    props: {
        width: {
            type: Number,
            required: true
        },
        mask: {
            type: Boolean,
            default: false
        },
        wrapStyle: {
            type: Object,
            default: () => { position: 'absolute' }
        },
        mobile: {
            type: Boolean,
            default: true
        },
        container: {
            type: Function,
            default: () => {}
        },
        taskType: {
            type: String,
            default: ''
        },
        hideDeliveryMap: {
            type: Boolean,
            default: true
        },
        showAsideHeader: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            loading: true,
            commentsCount: 0,
            btn1Loading: false,
            btn2Loading: false,
            editStatus: false,
            tab: 'task',
            conference: {},
            taskId: null
        }
    },
    computed: {
        ...mapState({
            task: state => state.task.task,
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            taskDrawerZIndex: state => state.task.taskDrawerZIndex
        }),
        ...mapGetters({
            taskActions: 'task/taskActions'
        }),
        taskStep() {
            if(this.task.show_step)
                return () => import('./StatusList.vue')
            else
                return null
        },
        dropActions() {
            const actions = this.taskActions(this.task.task_type)
            if(actions)
                return actions.actions
            else
                return null
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
                return this.$store.state.task.emdedTaskShow
            },
            set(val) {
                this.$store.commit('task/CHANGE_EMDED_TASK_SHOW', val)
            }
        },
        drawerWidth() {
            if(this.windowWidth > 1300)
                return 1300
            else if(this.windowWidth < 1300 && this.windowWidth > 500)
                return this.windowWidth - 30
            else
                return this.windowWidth
        },
        isOperator() {
            if(this.user.id === this.task.operator.id 
            )
                return true
            else
                return false
        },
        myTaskProcessed() {
            if(this.user && this.user.id === this.task.owner.id || this.user.id === this.task.operator.id 
            )
                return true
            else
                return false
        },
        isAuthor() {
            if(this.user?.id === this.task.owner.id)
                return true
            else
                return false
        },
        myTask() {
            if(this.user && this.user.id === this.task.owner.id || this.user.id === this.task.operator.id || this.task.workgroup?.author === this.user?.id || this.task.project?.author === this.user?.id)
                return true
            else
                return false
        },
        isMobile() {
            if(typeof this.mobile === 'boolean')
                return this.mobile
            else
                return this.$store.state.isMobile
        },
    },
    created () {
        this.$socket.client.emit("tasks")
    },
    watch: {
        '$route.name'() {
            this.visible = false
        },
        visible(val) {
            if(val) {
                if(this.editStatus)
                    this.editStatus = false
                this.getTask()
            } else {
                if(!this.editStatus)
                    this.close()
            }
        }
    },
    sockets: {
        task_update({data}) {
            if(data) {
                this.$store.commit('task/UPDATE_SHOW_TASK', data)
                this.$store.dispatch('task/getStatusList', {
                    task_type: this.taskType
                })

                this.$nextTick(() => {
                    if(this.$refs[`${this.task.id}_task_actions`]) {
                        console.log(this.$refs[`${this.task.id}_task_actions`], 'this.$refs[`${this.task.id}_task_actions`]')
                        this.$refs[`${this.task.id}_task_actions`].getTaskActions()
                    }
                })
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis) {
                this.taskId = null
                this.$store.commit('task/SET_TASK_DRAWER_OPTIONS', null)
            }
        },
        closeDrawer() {
            this.visible = false
        },
        checkRole(actions) {
            const all = actions.roles.find(f => f === 'all')

            if(all)
                return true
            else {
                const operator = actions.roles.find(f => f === 'operator')
                if(operator)
                    return this.myTask

                const owner = actions.roles.find(f => f === 'owner')
                if(owner)
                    return this.isAuthor
            }
        },
        getPopupContainer() {
            return document.querySelector('.task_body_wrap')
        },
        changeTab(val) {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            query.stab = val
            this.$router.push({query})
        },
        openSprint(id){
            if(!this.$route.query.sprint){
                let query = Object.assign({}, this.$route.query, )
                this.$store.commit('task/SET_SPRINT_DRAWER_ZINDEX', 1100)
                query.sprint = id
                this.$router.replace({query: {}})
                this.$router.push({query})
            }
        },
        async deleteTask() {
            try {
                this.btn1Loading = true
                const res = await this.$store.dispatch('task/deleteTask', this.task)
                if(res) {
                    this.$message.success(this.$t('task.task_deleted'))
                    this.visible = false
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.btn1Loading = false
            }
        },
        async openTask() {
            let query = Object.assign({}, this.$route.query)
            delete query.task
            await this.$router.push({query})
            this.reloadTask(this.task.parent)
        },
        reloadTask(item) {
            this.$store.commit('task/SET_TASK', null)
            let query = Object.assign({}, this.$route.query)
            query.task = item.id
            this.$router.push({query})
            this.getTask()
        },
        addSubtask() {
            this.visible = false
            eventBus.$emit('ADD_WATCH', {key: 'parent', data: this.task})
        },
        copy() {
            this.visible = false
            eventBus.$emit('ADD_WATCH', {type: 'copy', data: this.task})
        },
        edit() {
            this.visible = false
            this.editStatus = true
            eventBus.$emit('EDIT_TASK', {back: true})
        },
        close() {
            let query = Object.assign({}, this.$route.query)
            if(query.task) {
                if(query.stab)
                    delete query.stab
                delete query.task
                this.$router.push({query})
            }

            if(this.task?.tabs?.length)
                this.tab = this.task.tabs[0].code
            else
                this.tab = 'task'

            eventBus.$emit(`CLOSE_TASK_DRAWER_${this.taskType}`)
            this.$store.commit('task/SET_TASK', null)
        },
        async getTask() {
            let {task} = this.taskId ? {task: this.taskId} : Object.assign({}, this.$route.query)
            try {
                await this.$store.dispatch('task/getFullTask', task)
                await this.getCommentsCount()

                const query = JSON.parse(JSON.stringify(this.$route.query))
                if(query.stab)
                    this.tab = query.stab
                else {
                    if(this.task?.tabs?.length)
                        this.tab = this.task.tabs[0].code
                    else
                        this.tab = 'task'
                }
            } catch(error) {
                if(error && error.detail && error.detail === 'Не найдено.') {
                    this.$message.warning(this.$t('task.task_not_found'))
                    this.close()
                    this.visible = false
                } else if(error && error.detail && error.detail === 'Страница не найдена.') {
                    this.$message.warning(this.$t('task.task_not_found'))
                    this.close()
                    this.visible = false
                } else {
                    this.$message.error(this.$t('task.error'))
                }
            }
        },
        async getCommentsCount(){
            let {task} = this.taskId ? {task: this.taskId} : Object.assign({}, this.$route.query)
            let {data} = await this.$http('comments/count/', {params: {related_object: task}})
            this.commentsCount = Number(data) 
        },
        openTaskDrawer() {
            if(this.$route.query?.viewGroup || this.$route.query?.viewProject)
                this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1010)
            
            this.visible = true
        }
    },
    mounted() {
        eventBus.$on('OPEN_TASK', id => {
            this.taskId = id
            if(this.task) {
                if(this.task.id !== id) {
                    if(this.task?.tabs?.length)
                        this.tab = this.task.tabs[0].code
                    else
                        this.tab = 'task'

                    this.$store.commit('task/SET_TASK', null)
                    this.getTask()
                }
            } else {
                this.openTaskDrawer()
            }
        })
        eventBus.$on(`TOGGLE_TASK_DRAWER_${this.taskType}`, () => {
            this.closeDrawer()
        })
        eventBus.$on('UPDATE_TASK_DRAWER', () => {
            if(this.visible) {
                this.$store.commit('task/SET_TASK', null)
                this.getTask()
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('OPEN_TASK')
        eventBus.$off(`CLOSE_TASK_DRAWER_${this.taskType}`)
        eventBus.$off(`TOGGLE_TASK_DRAWER_${this.taskType}`)
        eventBus.$off('UPDATE_TASK_DRAWER')

        if(this.visible) {
            this.$store.commit('task/SET_TASK', null)
            this.visible = false
        }
    }
}
</script>

<style lang="scss">
.task_show_drawer{
    .task_sidebar{
        padding: 15px;
        background: #fafafa;
    }
    .ant-drawer-body,
    .ant-drawer-content{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: 100%;
    }
    .tab_wrapper{
        // will-change: transform;
        height: 40px;
        @media (min-width: 765px) {
            padding-left: 30px;
            padding-right: 30px;
        }
        border-bottom: 1px solid var(--borderColor);
        .ant-tabs-bar{
            border: 0px;
        }
        .ant-tabs-tab{
            padding: 10px 16px;
        }
    }
    .head_wrapper{
    
        height: 40px;
        border-bottom: 1px solid var(--borderColor);
        padding: 10px 30px;
        background: var(--bgColor);
        .ant-skeleton-paragraph{
            display: none;
        }
        .ant-skeleton-content{
            .ant-skeleton-title{
                width: 90%!important;
                margin: 0px;
                height: 20px;
            }
        }
    }
    .body_wrapper{
        .parent_task{
            padding-top: 20px;
            border-top: 1px solid var(--borderColor);
        }
        .body_tab{
            & > .ant-tabs-bar{
                display: none;
            }
        }
        .sidebar_item{
            &:not(:last-child){
                border-bottom: 1px solid var(--borderColor);
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
    }
    .footer_wrapper{
        // will-change: transform;

        height: 40px;
        padding: 10px 30px;
        background: var(--bgColor);
        border-top: 1px solid var(--borderColor);
        .ant-skeleton-paragraph{
            display: none;
        }
        .ant-skeleton-content{
            .ant-skeleton-title{
                width: 90%!important;
                margin: 0px;
                height: 20px;
            }
        }
    }

    .body_contractor{
        width: 40%;
    }
}
.task_mobile_drawer {
    .body_wrapper {
        padding: 15px;
        overflow-x: hidden;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        // will-change: transform;

    }
    .head_wrapper {
        padding: 10px 15px;
    }
    .footer_wrapper {
        padding: 10px 15px;
    }
}
</style>
