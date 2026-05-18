<template>
    <WidgetWrapper 
        :widget="widget" 
        cardColor="#f0f7eb"
        :class="isMobile && 'mobile_widget'">
        <template v-if="has_onboarding_tasks" slot="actions">
            <a-button 
                type="ui"
                ghost
                shape="circle"
                flaticon
                icon="fi-rr-trash"
                v-tippy="{ 
                    content: $t('dashboard.demoTask.text1'), 
                    trigger: 'mouseenter', 
                    hideOnClick: true, 
                    inertia: true, 
                    duration: [200,200], 
                    interactive: false, 
                    placement: 'top'
                }"
                @click="deleteDemoTask()" />
        </template>
        <DynamicScroller
            :items="list.results"
            :min-item-size="54.5"
            class="scroller_block"
            :emit-update="true">
            <template #before>
                <p>{{ $t('dashboard.demoTask.text2') }}</p>
                <a-empty 
                    v-if="empty" 
                    :description="$t('dashboard.tasks_empty')" />
            </template>
            <template #default="{ item, index, active }">
                <DynamicScrollerItem
                    :item="item"
                    :active="active"
                    :size-dependencies="[
                        item.workgroup,
                        item.date_start_plan,
                        item.dead_line,
                        item.project
                    ]"
                    :data-index="index"
                    :data-active="active">
                    <KanbanItem 
                        :item="item" 
                        :isScrolling="false"
                        activeMobile
                        responsiveDeadline
                        :myTaskEnabled="false"
                        showStatus />
                </DynamicScrollerItem>
            </template>
            <template #after>
                <infinite-loading 
                    ref="infiniteLoading"
                    @infinite="getTaskList"
                    :identifier="infiniteId"
                    :distance="10">
                    <div 
                        slot="spinner"
                        class="flex items-center justify-center inf_spinner">
                        <a-spin size="small" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </template>
        </DynamicScroller>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { mapState } from 'vuex'
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
        DynamicScroller,
        DynamicScrollerItem,
        InfiniteLoading: () => import('vue-infinite-loading'),
        KanbanItem: () => import('@apps/vue2TaskComponent/components/Kanban/Item.vue')
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
        }),
        has_onboarding_tasks() {
            return this.user?.has_onboarding_tasks
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            loading: false,
            page: 0,
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
        deleteDemoTask() {
            this.$confirm({
                title: this.$t('dashboard.demoTask.text3'),
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/tasks/onboarding/delete/')
                            .then(() => {
                                this.$message.success(this.$t('dashboard.demoTask.text4'))
                                setTimeout(() => {
                                    window.location.reload()
                                }, 2000)
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            this.$store.commit('task/SET_FORM_DEFAULT', {
                create_handler: this.widget.page_name || this.widget.id,
                task_type: 'task'
            })
            eventBus.$emit('add_task_modal', {
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
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/task/list/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.widget.page_name || this.widget.id,
                            task_type: this.task_type,
                            filters: JSON.stringify({is_onboarding: true}),
                            parent: 'all'
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
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
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
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`)
    }
}
</script>

<style lang="scss" scoped>
p{
    font-size: 14px;
    line-height: 20px;
    margin-bottom: 15px;
    color: #888888;
}
.scroller_block{
    overflow-y: auto;
    height: 100%;
    &::v-deep{
        .kanban-card{
            margin-bottom: 0px;
            background: #fff;
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
