<template>
    <div class="w-full truncate flex">
        <div 
            class="ant-input ant-input-lg w-full cursor-pointer task_select_input truncate" 
            :title="value ? value.name : ''" 
            :disabled="disabled"
            :class="disabled && 'ant-input-disabled'"
            @click="openDrawer()">
            <span v-if="value" class="truncate">
                <template v-if="value.counter">#{{ value.counter }} </template>{{ value.name }}
            </span>
            <span v-else class="truncate plc">
                {{ placeholder }}
            </span>
        </div>
        <a-modal
            :title="$t('task.select_task')"
            class="task_select_drawer"
            :dialog-style="{ top: '20px' }"
            :width="isMobile ? '100%' : 560"
            @afterVisibleChange="afterVisibleChange"
            destroyOnClose
            v-model="taskDrawer"
            @close="closeDrawer()">
            <div class="drawer_select_filter pb-2">
                <PageFilter 
                    :model="pageModel"
                    :key="page_name"
                    size="large"
                    :zIndex="999999"
                    ref="pageFilter"
                    initInputFocus
                    autoAdjustOverflow
                    class="modal_filter"
                    transitionName=""
                    placement="bottom"
                    :getPopupContainer="getPopupContainer"
                    :page_name="page_name" />
            </div>
            <div class="drawer_select_list">
                <div class="max-w-full">
                    <div
                        class="flex items-center" 
                        v-for="item in taskList" 
                        :key="item.id">
                        <WorkplanItem 
                            :item="item" 
                            :selectingSubtask="checkActive(item)"
                            class="w-full task_card"
                            :selectFunction="selectTask"
                            :isScrolling="false"
                            :myTaskEnabled="false"
                            :useActions="false"
                            :showStatus="true" /> 
                    </div>
                </div>
                <infinite-loading 
                    ref="taskInfinite" 
                    :identifier="identifier"
                    @infinite="getTaskList" 
                    v-bind:distance="10">
                    <div slot="spinner">
                        <a-spin class="w-full" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <template #footer>
                <a-button
                    block
                    type="ui_ghost"
                    ghost
                    class="px-8"
                    @click="closeDrawer()">
                    {{$t('task.close')}}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus"
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        WorkplanItem: () => import('@apps/vue2TaskComponent/components/Kanban/WorkplanItem.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        value: {
            type: Object
        },
        filters: {
            type: Object,
            default: null
        },
        toogleTaskEdit: {
            type: Function,
            default: () => {}
        },
        placeholder: {
            type: String,
            default: ""
        },
        disabled: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            searchLoading: false,
            taskList: [],
            search: '',
            scrollStatus: true,
            page: 0,
            identifier: Date.now(),
            loading: false,
            taskDrawer: false,
            page_name: 'page_list_work_plan_task.TaskModel',
            pageModel: 'tasks.TaskModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    if(this.$refs.pageFilter)
                        this.$refs.pageFilter.searchFocus()
                })
            } else {
                this.toogleTaskEdit(false)
            }
        },
        checkActive(item) {
            if(this.value?.id === item?.id)
                return false
            return true
        },  
        closeDrawer() {
            this.taskDrawer = false
            this.toogleTaskEdit(false)
        },
        openDrawer() {
            if(!this.disabled) {
                this.toogleTaskEdit(true)
                this.taskDrawer = true
            }
        },
        getPopupContainer() {
            return document.querySelector('.task_select_drawer')
        },
        selectTask(item) {
            const taskItem = {
                id: item.id,
                name: item.name,
                counter: item.counter
            }
            this.$emit('input', taskItem)
            this.$emit('change', taskItem)
            this.closeDrawer()
        },
        reloadList() {
            this.page = 0
            this.taskList = []
            this.loading = false
            this.scrollStatus = true
            this.$nextTick(() => {
                if(this.$refs?.taskInfinite)
                    this.$refs.taskInfinite.stateChanger.reset()
            })
        },
        async getTaskList($state = null) {
            if(!this.loading && this.scrollStatus && this.taskDrawer) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 8,
                        page: this.page,
                        page_name: this.page_name,
                        only_participant: 1,
                        task_type: 'task',
                        parent: 'all',
                        ordering: 'status,-created_at',
                        ...this.filters
                    }
                    const {data} = await this.$http.get('/tasks/task/list/', {params})
                    if(data && data.results.length) {
                        const existingIds = new Set(this.taskList.map(task => task.id))
                        const newTasks = data.results.filter(task => !existingIds.has(task.id))
                        this.taskList = this.taskList.concat(newTasks)
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.reloadList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`)
    }
}
</script>

<style lang="scss" scoped>
.task_card{
    &::v-deep{
        .kanban-card{
            cursor: default;
        }
    }
}
.modal_filter{
    &::v-deep{
        .filter_input{
            border-radius: 8px;
            background: #f7f9fc;
            border-color: #f7f9fc !important;
            box-shadow: initial !important;
            color: var(--text);
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}
.drawer_select_list{
    &::v-deep{
        .kanban-card{
            background: #fff;
        }
    }
}
.task_select_input{
    .plc{
        color: #bebebe;
    }
}
.drawer_select_filter{
    &::v-deep{
        .filter_pop_wrapper{
            max-width: 100%;
            min-width: 100%;
        }
    }
}
</style>