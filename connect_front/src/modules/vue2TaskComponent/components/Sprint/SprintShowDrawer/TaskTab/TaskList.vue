<template>
    <div>
        <TaskCard 
            v-for="task in tasks.results" 
            :item="task" 
            activeMobile
            showStatus
            :myTaskEnabled="false"
            :key="task.id" />
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
import InfiniteLoading from 'vue-infinite-loading'
import TaskCard from '../../../Kanban/Item.vue'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading,
        TaskCard
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
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
                    const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/tasks_list/`, {
                        params: {
                            page: this.page,
                            page_size: this.page_size,
                            page_name: this.page_name,
                            task_type: 'task,stage'
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
                } catch(e) {
                    console.log(e)
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