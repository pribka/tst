<template>
    <div>
        <TaskCard 
            v-for="task in tasks.results" 
            :item="task" 
            activeMobile
            showStatus
            :myTaskEnabled="false"
            :key="task.id"
            @rowSelected="rowSelected" />
        <infinite-loading 
            ref="infiniteLoading"
            @infinite="getTaskList"
            :identifier="infiniteId"
            :distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div 
            v-if="showEmpty" 
            class="pt-8">
            <a-empty>
                <template #description>
                    {{ $t('task.task_empty') }}
                </template>
            </a-empty>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import TaskSocket from '../../../mixins/TaskSocket'
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
        TaskCard: () => import('./TaskSelectedCard.vue')
    },
    props: {
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        queryParams: {
            type: Object,
            default: () => {}
        },
        rowSelected: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            showEmpty: false,
            page_size: 10,
            loading: false,
            page: 0,
            tasks: {
                next: true,
                results: []
            }
        }
    },
    methods: {
        async getTaskList($state) {
            if(!this.loading && this.tasks.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/sprint/task/list/', {
                        params: {
                            page: this.page,
                            task_type: 'task',
                            page_size: this.page_size,
                            page_name: this.page_name,
                            ...this.queryParams
                        }
                    })

                    if(data) {
                        this.tasks.count = data.count
                        this.tasks.next = data.next
                    }

                    if(data?.results?.length)
                        this.tasks.results = this.tasks.results.concat(data.results)

                    if(this.page === 1 && !this.tasks.results.length) {
                        this.showEmpty = true
                    }  
                    if(this.tasks.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            }
        },
        tableReload() {
            this.page = 0
            this.tasks = {
                next: true,
                results: []
            }
            this.showEmpty = false
            this.infiniteId = new Date()
            this.$nextTick(()=>{
                if(this.$refs.infiniteLoading) {
                    this.$refs.infiniteLoading.stateChanger.reset()
                }
            })
        },
        updateTaskInList(task) {
            if(!task?.id || !this.tasks?.results?.length)
                return

            const index = this.tasks.results.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            this.$set(this.tasks.results, index, {
                ...this.tasks.results[index],
                ...task
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.tableReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
    }
}
</script>
