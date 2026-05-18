<template>
    <div style="min-height: 90vh;">
        <div v-if="empty && !loading" class="flex justify-center mb-2">
            <a-empty :description="$t('no_data')" />
        </div>
        <TaskCard 
            v-for="item in listData.results"
            :key="item.id"
            activeMobile
            bgInvert
            :showStatus="true"
            :item="item" />
        <infinite-loading
            ref="infiniteLoading"
            @infinite="infiniteHandler"
            :identifier="infiniteId"
            :distance="10">
            <div slot="spinner" class="flex items-center justify-center inf_spinner pb-2">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import TaskSocket from '@apps/vue2TaskComponent/mixins/TaskSocket'
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
        InfiniteLoading: () => import("vue-infinite-loading"),
        TaskCard: () => import('@apps/vue2TaskComponent/components/Kanban/Item.vue')
    },
    props: {
        model: {
            type: String,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        ticket: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            listData: {
                count: 0,
                next: true,
                results: []
            },
            page: 0,
            empty: false,
            loading: false,
            page_size: 10,
            infiniteId: new Date()
        }
    },
    methods: {
        async infiniteHandler($state) {
            if(!this.loading && this.listData.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/task/list/', {
                        params: {
                            page: this.page,
                            page_size: this.page_size,
                            page_name: this.page_name,
                            model: this.model,
                            task_type: "task",
                            filters: JSON.stringify({reason: this.ticket.id})
                        }
                    })
                    if(data) {
                        this.listData.count = data.count
                        this.listData.next = data.next
                    }

                    if(data?.results?.length)
                        this.listData.results = this.listData.results.concat(data.results)

                    if(this.page === 1 && !this.listData.results.length) {
                        this.empty = true
                    }  
                    if(this.listData.next)
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
        reloadList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.listData = {
                    count: 0,
                    next: true,
                    results: []
                }
                if(this.$refs['infiniteLoading'])
                    this.$refs['infiniteLoading'].stateChanger.reset()
            })
        },
        updateTaskInList(task) {
            if(!task?.id || !this.listData?.results?.length)
                return

            const index = this.listData.results.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            this.$set(this.listData.results, index, {
                ...this.listData.results[index],
                ...task
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => this.reloadList())
        eventBus.$on(`update_filter_${this.page_name}`, () => this.reloadList())
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off(`update_filter_${this.page_name}`)
    }
}
</script>
