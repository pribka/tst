<template>
    <WidgetWrapper 
        :widget="widget" 
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <a-button
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-plus"
                @click="addTask()" />
        </template>
        <div ref="scroller" class="scroller_block">
            <a-empty 
                v-if="empty" 
                :description="$t('dashboard.tasks_empty')" />

            <KanbanItem 
                v-for="item in list.results"
                :key="item.id"
                :item="item" 
                :isScrolling="false"
                activeMobile
                responsiveDeadline
                :myTaskEnabled="false"
                showStatus />

            <infinite-loading
                v-if="loadingRun"
                ref="infiniteLoading"
                @infinite="getTaskList"
                :identifier="infiniteId"
                :immediate-check="false"
                :check-scrollbar="false"
                :distance="100">
                <div slot="spinner" class="flex items-center justify-center">
                    <a-spin size="small" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <template v-else>
                <div v-if="loading" class="flex items-center justify-center">
                    <a-spin size="small" />
                </div>
            </template>
        </div>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        KanbanItem: () => import('@apps/vue2TaskComponent/components/Kanban/Item.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        scrollerWrapper() {
            return this.$refs.scroller
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            loading: false,
            page: 0,
            loadingRun: true,
            empty: false,
            task_type: 'task',
            model: 'tasks.TaskModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    sockets: {
        task_update({ data }) {
            if(data)
                this.updateTaskInList(data)
        }
    },
    methods: {
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            this.$store.commit('task/SET_FORM_DEFAULT', {
                create_handler: this.widget.page_name || this.widget.id,
                task_type: 'task'
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal', {
                create_handler: this.widget.page_name || this.widget.id,
                task_type: 'task'
            })
            /*this.$store.dispatch('task/sidebarOpen', {
                task_type: this.task_type,
                create_handler: this.widget.page_name || this.widget.id
            })*/
        },
        resetList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        async getTaskList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loadingRun = false
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/task/list/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.widget.page_name || this.widget.id,
                            task_type: this.task_type
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()

                    setTimeout(() => {
                        this.$nextTick(() => {
                            this.loadingRun = true
                        })
                    }, 200)
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            } else
                $state.complete()
        },
        updateTaskInList(task) {
            if(!task?.id || !this.list?.results?.length)
                return

            const index = this.list.results.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            this.$set(this.list.results, index, {
                ...this.list.results[index],
                ...task
            })
        },
        removeTaskFromList(task) {
            const taskId = task?.id || task
            if(!taskId || !this.list?.results?.length)
                return

            const index = this.list.results.findIndex(item => item.id === taskId)
            if(index === -1)
                return

            this.list.results.splice(index, 1)
            if(typeof this.list.count === 'number')
                this.list.count = Math.max(0, this.list.count - 1)
            this.empty = !this.list.results.length
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on('TASK_WIDGET_DELETE', this.removeTaskFromList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off('TASK_WIDGET_DELETE', this.removeTaskFromList)
    }
}
</script>

<style lang="scss" scoped>
.scroller_block{
    overflow-y: auto;
    height: 100%;
    &::v-deep{
        .kanban-card{
            margin-bottom: 0px;
        }
        .active_task{
            padding-bottom: 8px;
        }
    }
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>
