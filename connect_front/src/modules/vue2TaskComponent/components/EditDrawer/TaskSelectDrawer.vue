<template>
    <a-modal
        :title="$t('task.select_task')"
        class="task_select_drawer"
        :width="isMobile ? '100%' : 560"
        destroyOnClose
        :dialog-style="isMobile ? { top: '0', paddingBottom: '0' } : { top: '20px' }"
        :visible="taskDrawer"
        :afterVisibleChange="afterVisibleChange"
        @cancel="closeHandler()">
        <div v-if="!isMobile" class="mb-4">
            <PageFilter
                ref="pageFilter"
                :model="model"
                :key="page_name"
                size="large"
                :getPopupContainer="getPopupContainer"
                :page_name="page_name" />
        </div>
        <div 
            class="max-w-full task_select_content"
            ref="subtask_scroll">
            <div
                class="flex items-center" 
                v-for="item in taskList" 
                :key="item.id">
                <KanbanItem 
                    :item="item" 
                    selectingSubtask
                    class="w-full"
                    :selectFunction="selectTask"
                    :isScrolling="false"
                    :myTaskEnabled="false"
                    :showStatus="true" /> 
            </div>
            <infinite-loading 
                ref="userInfinite" 
                @infinite="getTaskList" 
                v-bind:distance="10">
                <div slot="spinner">
                    <a-spin class="w-full" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <div v-if="isMobile" class="float_add">
                <div class="filter_slot">
                    <PageFilter
                        ref="pageFilter"
                        :model="model"
                        :key="page_name"
                        size="large"
                        :getPopupContainer="getPopupContainer"
                        :page_name="page_name" />
                </div>
            </div>
        </div>
        <template #footer>
            <a-button
                block
                type="ui"
                ghost
                class="px-8"
                @click="closeHandler">
                {{$t('task.close')}}
            </a-button>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import TaskSocket from '../../mixins/TaskSocket'
export default {
    mixins: [TaskSocket],
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskInList(data)
            }
        }
    },
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        KanbanItem: () => import('./TaskSelectItem.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        value: {
            type: Object
        },
        taskDrawer: {
            type: Boolean,
            default: false
        },
        closeHandler: {
            type: Function,
            default: () => {}
        },
        filters: {
            type: Object,
            default: null
        },
        selectParentTask: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            taskList: [],
            scrollStatus: true,
            page: 0,
            loading: false,
            model: 'tasks.TaskModel',
            page_name: 'task_select_drawer_task.TaskModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch:{
        filters(){
            this.reloadList()
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    if(this.$refs.pageFilter)
                        this.$refs.pageFilter.searchFocus()
                })
            }
        },
        getPopupContainer() {
            return this.$refs['subtask_scroll']
        },
        reloadList() {
            this.scrollStatus = true
            this.page = 0
            this.taskList = []
            this.$nextTick(() => {
                if(this.$refs.userInfinite)
                    this.$refs.userInfinite.stateChanger.reset()
            })
        },
        updateTaskInList(task) {
            if(!task?.id || !this.taskList?.length)
                return

            const index = this.taskList.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            this.$set(this.taskList, index, {
                ...this.taskList[index],
                ...task
            })
        },
        checkSelected(task) {
            if(this.value) {
                if(task.id === this.value.id)
                    return true
                else
                    return false
            } else
                return false
        },
        selectTask(item) {
            this.$emit('input', item)
            this.closeHandler()
            this.selectParentTask(item)
        },
        async getTaskList($state = null) {
            if(!this.loading && this.scrollStatus && this.taskDrawer) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    const params = {
                        page_size: 15,
                        page: this.page,
                        page_name: this.page_name,
                        task_type: 'task,stage',
                        parent: 'all',
                        ...this.filters
                    }
                    const {data} = await this.$http.get('/tasks/task/list/', {params})
                    if(data && data.results.length)
                        this.taskList = this.taskList.concat(data.results)
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        },
        reloadTask(item) {
            this.$store.commit('task/SET_TASK', null)
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = item.id
            this.$router.push({query})
            this.getTask()
        },
        async getTask() {
            let {task} = JSON.parse(JSON.stringify(this.$route.query))
            try {
                await this.$store.dispatch('task/getFullTask', task)
                await this.getCommentsCount()

                const query = JSON.parse(JSON.stringify(this.$route.query))
                // if(query.stab)
                //     this.tab = query.stab
                // else {
                //     if(this.task?.tabs?.length)
                //         this.tab = this.task.tabs[0].code
                //     else
                //         this.tab = 'task'
                // }
            } catch(error) {
                if(error && error.detail && error.detail === this.$t('task.not_found')) {
                    this.$message.warning(this.$t('task.task_not_found'))
                    this.close()
                    this.visible = false
                } else if(error && error.detail && error.detail === this.$t('task.page_not_found')) {
                    this.$message.warning(this.$t('task.task_not_found'))
                    this.close()
                    this.visible = false
                } else {
                    this.$message.error(this.$t('task.error'))
                }
            }
        },
        async getCommentsCount(){
            let {task} = JSON.parse(JSON.stringify(this.$route.query))
            let {data} = await this.$http('comments/count/', {params: {related_object: task}})
            this.commentsCount = Number(data) 
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, this.reloadList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`, this.reloadList)
    }
}
</script>

<style lang="scss" scoped>
.task_select_content {
    min-height: 100%;
}

::v-deep {
    .item{
        &:not(:last-child){
            border-bottom: 1px solid var(--borderColor);
        }
        &:hover{
            background: var(--hoverBg);
        }
        .name{
            word-break: break-word;
        }
    }
}

@media (max-width: 767px) {
    .task_select_drawer{
        &::v-deep{
            .ant-modal{
                width: 100% !important;
                max-width: 100%;
                margin: 0;
                padding-bottom: 0;
                top: 0;
            }
            .ant-modal-content{
                min-height: 100vh;
                border-radius: 0;
                display: flex;
                flex-direction: column;
            }
            .ant-modal-body{
                flex: 1 1 auto;
                min-height: 0;
                padding: 16px;
            }
            .ant-modal-footer{
                border-radius: 0;
            }
        }
    }
}
</style>
