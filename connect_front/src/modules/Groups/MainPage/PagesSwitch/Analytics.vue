<template>
    <div class="analytics_page">
        <div 
            v-if="loading" 
            class="text-center">
            <a-spin />
        </div>
        <div v-if="allStat && taskCount > 0">
            <div class="grid md:grid-cols-2 2xl:grid-cols-3 gap-4">
                <StatChart :stat="allStat" />
                <StatMyTaskChart 
                    :id="id"
                    :is_project="is_project" />
                <StatCompletedChart :stat="allStat" />
                <StatBudget :id="id" />
                <StatDifficulty :id="id" />
            </div>
            <Analytics 
                v-if="!isMobile"
                class="mt-4"
                :queryParams="queryParams"
                :requestData="requestData"
                :page_name="`analytics_table_${id}`" />
        </div>
        <div v-if="empty">
            <a-result :title="$t('wgr.stat_empty')">
                <template #icon>
                    <a-icon 
                        type="fund"
                        theme="twoTone" />
                </template>
            </a-result>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        StatChart: () => import('../modules/StatChart.vue'),
        StatCompletedChart: () => import('../modules/StatCompletedChart.vue'),
        StatMyTaskChart: () => import('../modules/StatMyTaskChart.vue'),
        StatBudget: () => import('../modules/StatBudget.vue'),
        StatDifficulty: () => import('../modules/StatDifficulty.vue'),
        Analytics: () => import('@apps/vue2TaskComponent/components/Analytics')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        is_project: {
            type: Boolean,
            default: false
        },
        requestData: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        pageName() {
            return `tasks.stat_groups_and_project_${this.id}`
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            allStat: null,
            taskCount: 0,
            loading: false,
            empty: false,
            queryParams: null
        }
    },
    created() {
        if(this.is_project) {
            this.queryParams = { filters: { project: this.id } }
        } else {
            this.queryParams = { filters: { workgroup: this.id } }
        }

        this.getTask()
    },
    methods: {
        async getStat() {
            try {
                let params = {
                    parent: 'all',
                    page_name: this.pageName
                }

                if(this.is_project)
                    params['filters'] = { project: this.id }
                else
                    params['filters'] = { workgroup: this.id }

                const {data} = await this.$http.get('tasks/task_kanban/status_count/', {params})
                if(data) {
                    this.allStat = {
                        ...data,
                        new_percent: parseInt(((data.new / this.taskCount) * 100).toFixed(2)),
                        in_work_percent: parseInt(((data.in_work / this.taskCount) * 100).toFixed(2)),
                        on_pause_percent: parseInt(((data.on_pause / this.taskCount) * 100).toFixed(2)),
                        on_check_percent: parseInt(((data.on_check / this.taskCount) * 100).toFixed(2)),
                        on_rework_percent: parseInt(((data.on_rework / this.taskCount) * 100).toFixed(2)),
                        completed_percent: parseInt(((data.completed / this.taskCount) * 100).toFixed(2))
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async getTask() {
            try{
                this.loading = true
                let params = {
                    parent: 'all',
                    page_name: this.pageName,
                    page_size: 1
                }

                if(this.is_project)
                    params['filters'] = { project: this.id }
                else
                    params['filters'] = { workgroup: this.id }

                const {data} = await this.$http.get('/tasks/task/list/', {params})
                if(data?.count) {
                    this.taskCount = data.count
                    this.getStat()
                } else {
                    this.empty = true
                    this.loading = false
                }
            } catch(e) {
                this.loading = false
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss">
.group_stat_card{
    border: 1px solid var(--border2);
    padding: 15px;
    border-radius: 8px;
    h2{
        font-size: 17px;
        font-weight: bold;
        margin-bottom: 15px;
    }
}
</style>