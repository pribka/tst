<template>
    <div class="contract_project_tasks_mobile">
        <div v-if="empty && !loading" class="flex justify-center mb-2">
            <a-empty :description="$t('deals_contracts.tasks_linked_empty')" />
        </div>
        <TaskCard
            v-for="item in list.results"
            :key="item.id"
            activeMobile
            bgInvert
            :showStatus="true"
            :item="item" />
        <infinite-loading
            ref="infiniteLoading"
            :identifier="infiniteId"
            :distance="10"
            @infinite="infiniteHandler">
            <div slot="spinner" class="flex items-center justify-center inf_spinner pb-2">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import TaskSocket from '@apps/vue2TaskComponent/mixins/TaskSocket'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ContractProjectTasksListView',
    mixins: [TaskSocket],
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskItem(data)
            }
        },
    },
    components: {
        InfiniteLoading,
        TaskCard: () => import('@apps/vue2TaskComponent/components/Kanban/Item.vue'),
    },
    props: {
        projectId: {
            type: [String, Number],
            required: true,
        },
        contractId: {
            type: String,
            required: true,
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    data() {
        return {
            list: {
                count: 0,
                next: true,
                results: [],
            },
            page: 0,
            pageSize: 15,
            empty: false,
            loading: false,
            infiniteId: Date.now(),
        }
    },
    computed: {
        normalizedPageName() {
            return this.pageName || `deals.contract_project_tasks_${this.contractId}_${this.projectId}`
        },
    },
    watch: {
        projectId() {
            this.loadData()
        },
        contractId() {
            this.loadData()
        },
    },
    methods: {
        loadData() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    count: 0,
                    next: true,
                    results: [],
                }
                this.infiniteId = Date.now()
                this.$refs.infiniteLoading?.stateChanger?.reset()
            })
        },
        async infiniteHandler($state) {
            if (this.loading || !this.list.next) return
            if (!this.contractId || !this.projectId) {
                this.empty = true
                this.list.next = false
                $state.complete()
                return
            }
            try {
                this.loading = true
                this.page += 1
                const { data } = await this.$http.get('/tasks/task/list/', {
                    params: {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.normalizedPageName,
                        model: 'tasks.TaskModel',
                        task_type: 'task,stage,milestone',
                        filters: JSON.stringify({
                            project: this.projectId,
                            parent: null,
                            contract: this.contractId,
                        }),
                    },
                })
                const results = Array.isArray(data?.results) ? data.results : []
                this.list.count = data?.count || results.length
                this.list.next = Boolean(data?.next)
                if (results.length) {
                    this.list.results = this.list.results.concat(results)
                }
                if (this.page === 1 && !this.list.results.length) {
                    this.empty = true
                }
                if (this.list.next) $state.loaded()
                else $state.complete()
            } catch (error) {
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.loading = false
            }
        },
        updateTaskItem(task) {
            const index = this.list.results.findIndex(item => item.id === task.id)
            if (index !== -1) {
                this.$set(this.list.results, index, task)
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_project_tasks_mobile {
    min-height: 70vh;
}
</style>
