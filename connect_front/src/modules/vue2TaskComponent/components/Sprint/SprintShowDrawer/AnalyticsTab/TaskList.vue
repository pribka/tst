<template>
    <div>
        <TaskCard 
            v-for="task in tasks.results" 
            :item="task" 
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
import TaskCard from './TaskCard.vue'
export default {
    components: {
        InfiniteLoading,
        TaskCard
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
        sprint: {
            type: Object,
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
            user: null,
            tasks: {
                next: true,
                results: []
            }
        }
    },
    methods: {
        reloadTableData() {
            this.tableReload()
        },
        clearTaskFilter() {
            this.user = null
            this.tableReload()
        },
        taskSetFilter(item) {
            this.user = item.customData.author
            this.tableReload()
        },
        async getTaskList($state) {
            if(!this.loading && this.tasks.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page: this.page,
                        page_size: this.page_size,
                        page_name: this.page_name
                    }
                    if(this.user)
                        params.user = this.user
                    const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/report/tasks/`, { params })

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
    }
}
</script>