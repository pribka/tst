<template>
    <div class="analytics_page">
        <div 
            v-if="loading" 
            class="text-center">
            <a-spin />
        </div>
        <div v-if="allStat && taskCount > 0">
            <div class="grid md:grid-cols-1 xl:grid-cols-2 gap-4">
                <div class="panel" v-if="statistics.tasks.labels">
                    <p class="text-xl mb-6">{{ $t('Tasks')}}</p>
                    <DonutChart :statistics="statistics.tasks" />
                </div>
                <div class="panel">
                    <p class="text-xl mb-6">{{ $t('Time for tasks')}}</p>
                    <div class="panel__bar-wrap">
                        <BarChart class="panel__bar" :statistics="statistics.time" />
                    </div>
                </div>

                <div class="panel xl:col-span-2">
                    <p class="text-xl mb-6">{{ $t('Stages')}}</p>
                    <div class="flex xl:items-center justify-between flex-col xl:flex-row">
                        <DonutChart :statistics="statistics.stages" />
                        <TableChart :statistics="statistics.stages?.table" class="mt-6 xl:mt-0 xl:ml-10" />
                    </div>
                </div>

                <div class="panel xl:col-span-2">
                    <p class="text-xl mb-6">{{ $t('Milestones')}}</p>
                    <div class="flex xl:items-center justify-between flex-col xl:flex-row">
                        <DonutChart :statistics="statistics.milestones" />
                        <TableChart :statistics="statistics.milestones?.table" class="mt-6 xl:mt-0 xl:ml-10" />
                    </div>
                </div>

                <div class="panel">
                    <p class="text-xl mb-6">{{ $t('Schedule')}}</p>
                    <div class="panel__bar-wrap">
                        <RangeBarChart class="panel__bar" :statistics="statistics.progress" />
                    </div>
                </div>

                <div class="panel">
                    <p class="text-xl mb-6 shrink-0">{{ $t('Cost, thousand')}}</p>
                    <div class="panel__bar-wrap">
                        <BarChart class="panel__bar" :statistics="statistics.funds" />
                    </div>
                </div>
            </div>
        </div>
        <div v-if="empty">
            <a-result :title="$t('project.stat_empty')">
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
        DonutChart: () => import('../../components/Statistic/DonutChart.vue'),
        BarChart: () => import('../../components/Statistic/BarChart.vue'),
        TableChart: () => import('../../components/Statistic/TableChart.vue'),
        RangeBarChart: () => import('../../components/Statistic/RangeBarChart.vue')
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
            queryParams: null,
            statistics: {
                tasks: {},
                time: {},
                stages: {},
                milestones: {},
                funds: {},
                progress: {}
            },
            stages: []
        }
    },
    created() {
        if(this.is_project) {
            this.queryParams = { filters: { project: this.id } }
        } else {
            this.queryParams = { filters: { workgroup: this.id } }
        }

        this.getTask()

        this.getTasksStatistics()
        this.getStagesStatistics()
        this.getFundsStatistics()
        this.getProgressStatistics()
        this.getMilestonesStatistics()

    },
    methods: {
        getFundsStatistics() {
            this.$http(`/work_groups/workgroups/${this.id}/about/funds/`)
                .then(({ data }) => {
                    this.statistics.funds.series = data.funds.map(fund => ({
                        y: fund.value,
                        x: fund.label
                    }))
                    this.statistics.funds.seriesUnit = this.$t('Thousand')
                })

        },
        getProgressStatistics() {
            this.$http(`/work_groups/workgroups/${this.id}/about/progress/`)
                .then(({ data }) => {
                    this.statistics.progress.seriesUnit = this.$t('Percent')
                    this.statistics.progress.series = data.progress.map(item => ({
                        y: [0, item.value],
                        x: '',
                        label: item.label
                    }))

                })
        },
        getTasksStatistics() {
            this.$http(`/work_groups/workgroups/${this.id}/about/task_count/`)
                .then(({ data }) => {
                    const series = []
                    const labels = []
                    for (const key in data.status_count) {
                        series.push(data.status_count[key])
                        labels.push(data.labels[key])
                    }
                    this.statistics.tasks.series = series
                    this.statistics.tasks.labels = labels
                    this.statistics.tasks.totalLabel = this.$t('Total tasks')
                    
                    this.statistics.time.series = data.time.map(item => ({
                        y: item.value,
                        x: item.label
                    }))

                    this.statistics.time.seriesUnit = this.$t('Hours')

                })
        },
        getStagesStatistics() {
            this.$http(`/work_groups/workgroups/${this.id}/about/stages/`)
                .then(({ data }) => {
                    const series = []
                    const labels = []
                    for (const key in data.status_count) {
                        series.push(data.status_count[key])
                        labels.push(data.labels[key])
                    }
                    this.statistics.stages.series = series
                    this.statistics.stages.labels = labels
                    this.statistics.stages.totalLabel = this.$t('Total stages')

                    this.statistics.stages.table = data.stages	
                    
                })
        },
        getMilestonesStatistics() {
            this.$http(`/work_groups/workgroups/${this.id}/about/milestones/`)
                .then(({ data }) => {
                    console.log(data)
                    const series = []
                    const labels = []
                    for (const key in data.status_count) {
                        series.push(data.status_count[key])
                        labels.push(data.labels[key])
                    }
                    this.statistics.milestones.series = series
                    this.statistics.milestones.labels = labels
                    this.statistics.milestones.totalLabel = this.$t('Total tasks')

                    this.statistics.milestones.table = data.milestones
                })
        },
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
        },
        async getStages() {
            try{
                this.loading = true
                let params = {
                    parent: 'all',
                    page_name: this.pageName,
                    project: this.id,
                    task_type: 'stage',
                    page_size: 1
                }

                const { data } = await this.$http.get('/tasks/task/list/', {params})
                this.stages = data.results
                this.$http(`/work_groups/workgroups/${this.id}/about/milestones/`)
                    .then(({ data }) => {
                        const series = []
                        const labels = []
                        for (const key in data.status_count) {
                            series.push(data.status_count[key])
                            labels.push(key)
                        }
                        this.statistics.projectMilestones.series = series
                        this.statistics.projectMilestones.labels = labels
                    })
            } catch(e) {
                this.loading = false
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss">
$md: 768px;
$xl: 1280px;
.panel {
    min-width: 0;
    max-width: 100%;
    padding: 20px 15px;
    background-color: #FAFAFA;
    border-radius: 12px;
    @media (min-width: $md) {
        padding: 30px 25px;
    }
    @media (min-width: $xl) {
        max-height: 400px;    
    }
}
.panel__bar-wrap {
    min-width: 0;
    overflow-x: auto;
}

.panel__bar {
    min-width: 400px;
}
</style>