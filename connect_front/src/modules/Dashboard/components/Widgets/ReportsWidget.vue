<template>
    <WidgetWrapper 
        :widget="widget" 
        :class="isMobile && 'mobile_widget'">
        <div ref="scroller" class="scroller_block">
            <TemplateGrid
                ref="templateGrid"
                useMobile
                :templatesSource="templatesSource"
                class="mt-3" />
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
        TemplateGrid: () => import('@apps/Reports/components/Templates/TemplateGrid.vue')
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
            templatesSource: 'templates',
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
.scroller_block{
    overflow-y: auto;
    height: 100%;
    &::v-deep{
        .template{
            box-shadow: initial!important;
            background: #f7f9fc;
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>