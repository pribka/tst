<template>
    <div>
        <div class="analytics_layout grid gap-3">
            <!-- Левый сайдбар с аналитикой по спринту -->
            <div class="panel-ui">
                <p class="text-base mb-4">
                    {{ $t('sprint.sprint_analytics') }}
                </p>
                <a-skeleton v-if="loading" :paragraph="{ rows: 6 }" />
                <template v-else>
                    <div 
                        class="px-2.5 py-3 rounded-lg"
                        :class="sprint.goal_achieved ? 'text-on-success bg-light-success' : 'text-danger bg-danger'">
                        {{ sprint.goal_achieved ? $t('sprint.goal_achieved') : $t('sprint.goal_not_achieved') }} 
                    </div>
                    <div 
                        v-for="item, index in analyticTable"
                        :key="index">
                        <div :class="index === 0 ? 'mt-3' : 'mt-6'">
                            <p class="mb-3">
                                {{ item.name }}
                            </p>
                            <div 
                                v-for="valueItem, valueIndex in item.value"
                                :key="valueIndex"
                                class="mt-3 flex items-center justify-between">
                                <p class="text-muted">{{ valueItem.name }}</p>
                                <p class="ml-2 text-right">{{ valueItem.value }}</p>                    
                            </div>
                        </div>
                    </div>          
                </template>
            </div>
            <!-- Плашки со статистикой -->
            <div class="analytics_content">
                <div class="analytics_stats grid gap-3">
                    <div class="px-5 py-3 rounded-lg flex flex-row bg-success">
                        <div class="font-semibold text-xl leading-none text-success">{{ sprint.completed_task_count }}</div>
                        <div class="ml-3 leading-[1.3]">{{ $t('sprint.completed_tasks')}}</div>
                    </div>
                    <div class="px-5 py-3 rounded-lg flex flex-row bg-danger">
                        <div class="font-semibold text-xl leading-none text-danger">{{ openetTasks }}</div>
                        <div class="ml-3 leading-[1.3]">{{ $t('sprint.open_tasks')}}</div>
                    </div>
                    <div class="px-5 py-3 rounded-lg flex flex-row bg-primary">
                        <div class="font-semibold text-xl leading-none text-primary">{{ sprint.wasted_time || 0 }}</div>
                        <div class="ml-3 leading-[1.3]">{{ $t('sprint.time_spent')}}</div>
                    </div>
                    <div class="px-5 py-3 rounded-lg flex flex-row bg-primary">
                        <div class="font-semibold text-xl leading-none text-primary">{{ sprint.member_count || 0 }}</div>
                        <div class="ml-3 leading-[1.3]">{{  $t('sprint.employees') }}</div>
                    </div>
                </div>
                <div class="analytics_charts mt-3 grid gap-3 items-start">
                    <div class="panel-ui">
                        <p>
                            {{ $t('sprint.sprint_rating') }}
                        </p>
                        <div 
                            v-if="loading"
                            class="w-full flex justify-center items-center py-8">
                            <a-spin />
                        </div>
                        <SemiCircleGauge 
                            v-else
                            ref="tasks" 
                            :sprint="sprint"
                            :chartData="sprintScore" />
                    </div>
                    <div class="panel-ui">
                        <p>
                            {{ $t('Tasks') }}
                        </p>
                        
                        <div 
                            v-if="loading"
                            class="w-full flex justify-center items-center py-8">
                            <a-spin />
                        </div>
                        <Tasks 
                            v-else
                            ref="tasks" 
                            :sprint="sprint" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        Tasks: () => import('./Charts/Tasks.vue'),
        SemiCircleGauge: () => import('./Charts/SemiCircleGauge.vue')
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
        }
    },
    data() {
        return {
            model: 'tasks.TaskModel',
            userSelected: null,
            userProfile: null,
            analyticTable: [],
            sprintScore: { score: 0, },
            tasksAnalytics: [],
            loading: false,

            
        }
    },
    computed: {
        taskListWidget() {
            if(this.isMobile)
                return () => import('./TaskList.vue')
            else    
                return () => import('./TaskTable.vue')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        openetTasks() {
            return this.sprint.in_work_task_count+this.sprint.new_task_count
        },
        aPageName() {
            return `analytics_${this.page_name}`
        }
    },
    mounted() {
        this.getAnalytics()
        this.getTasksAnalytics()
    },
    methods: {
        getTasksAnalytics() {
            this.loading = true
            const url = `/tasks/sprint/${this.sprint.id}/tasks_count/`
            this.$http.get(url)
                .then(({ data }) => {
                    this.tasksAnalytics = data
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        getAnalytics() {
            this.loading = true
            const url = `tasks/sprint/${this.sprint.id}/analytics`
            this.$http.get(url)
                .then(({ data }) => {
                    this.analyticTable = data.table
                    this.sprintScore = data.score
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        taskSetFilter(item = null) {
            const author = item?.customData?.author || null
            if (this.userSelected === author) {
                this.userSelected = null
                this.$nextTick(() => this.$refs.taskTable.clearTaskFilter())
            } else {
                this.userSelected = author

                if (author) {
                    const url = `/users/${author}/`
                    this.$http.get(url)
                        .then(({ data }) => {
                            this.userProfile = data
                        })
                }
                
                this.$nextTick(() => {
                    if (author) {
                        this.$refs.taskTable.taskSetFilter(item)
                    } else {
                        this.$refs.taskTable.clearTaskFilter()
                    }
                })
            }
        },
        analyticsUpdate() {
            this.$nextTick(() => {
                if(this.$refs.loadingResources)
                    this.$refs.loadingResources.getStat()
                if(this.$refs.taskTable)
                    this.$refs.taskTable.reloadTableData()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.panel-ui {
    min-width: 0;
    padding: 20px;
    background-color: #F8F9FD;
    border-radius: 12px;
}

.analytics_layout,
.analytics_stats,
.analytics_charts {
    grid-template-columns: minmax(0, 1fr);
}

.analytics_content {
    min-width: 0;
}

.analytics_stats > div {
    min-width: 0;
    word-break: break-word;
}

@media (min-width: 768px) {
    .analytics_stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (min-width: 1200px) {
    .analytics_layout {
        grid-template-columns: minmax(220px, 1fr) minmax(0, 2fr);
    }

    .analytics_stats {
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .analytics_charts {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}



.graph_grid{
    @media (max-width: 1399.98px) {
        &::v-deep{
            .chart_block{
                &:not(:last-child){
                    margin-bottom: 0.75rem;
                }
            }
        }
    }
    @media (min-width: 1400px) {
        display: grid;
        grid-template-columns: 1fr 400px;
    }
}
.chart_row{
    &::v-deep{
        .chart_block{
            background: #FAFAFA;
            border-radius: 12px;
            padding: 15px;
            &__label{
                color: #000;
                font-weight: 400;
                font-size: 18px;
                line-height: 18px;
                margin-bottom: 10px;
            }
            &__header{
                margin-bottom: 10px;
                @media (min-width: 768px) {
                    display: flex;
                    align-items: center;
                }
                &--label{
                    color: #000;
                    font-weight: 400;
                    font-size: 18px;
                    line-height: 18px;
                    @media (max-width: 767.98px) {
                        &:not(:last-child){
                            margin-bottom: 8px;
                        }
                    }
                }
            }
            &.donut_chart{
                .apexcharts-legend{
                    .apexcharts-legend-series{
                        display: flex;
                        align-items: center;
                        &:not(:last-child){
                            margin-right: 10px!important;
                        }
                        .apexcharts-legend-marker{
                            top: 0px!important;
                        }
                        .apexcharts-legend-text{
                            padding-left: 20px;
                        }
                    }
                }
            }
        }
    }
}
.analytics_blocks{
    &__item{
        padding: 25px 15px;
        border-radius: 8px;
        color: #000;
        display: flex;
        flex-direction: column;
        .stat_value{
            font-weight: 400;
            font-size: 24px;
            line-height: 24px;
            margin-bottom: 8px;
            flex-grow: 1;
        }
        .stat_label{
            font-weight: 400;
            font-size: 16px;
            line-height: 16px;
        }
        &.b_green{
            background: #F0F7EA;
        }
        &.b_red{
            background: #FFEDED;
        }
        &.b_blue{
            background: #E8EDFA;
        }
        &.b_purple{ 
            background: #c1c8fd;
        }
        &.b_yellow{
            background: #f0fdbd;
        }
    }
}

.bg-success {
    background-color: var(--functional-background-success-level-1);
}
.bg-danger {
    background-color: var(--functional-background-danger-level-1);
}
.bg-primary {
    background-color: var(--functional-label-primary-background);
}
.bg-light-success {
    background-color: var(--functional-label-success-background);
}

.text-success {
    color: var(--functional-label-success-text);
}
.text-danger {
    color: var(--functional-label-danger-text);
}
.text-primary {
    color: var(--functional-label-primary-text);
}
.text-on-success {
    color: var(--functional-text-on-success);
}
.text-muted {
    color: var(--functional-text-muted);
}
</style>
