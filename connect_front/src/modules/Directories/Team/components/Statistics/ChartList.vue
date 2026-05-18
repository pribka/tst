<template>
    <div class="">
        <div class="w-full stat_card__list" :class="adaptiveChart && 'adaptive'">
            <div v-if="!visibleСharts.length || visibleСharts.includes('all')" class="stat_card__col">
                <div class="stat_card">
                    <div class="stat_card__header mb-3">
                        <div class="label">{{ $t('All tasks') }}</div>
                    </div>
                    <div class="stat_card__body">
                        <div class="stat_card__chart">
                            <ChartAllTasks
                                height="180"
                                width="180"
                                :taskStatistics="taskStatistics"
                                :allTasks="allTasks"
                                :labels="allTasksLabels"
                                :series="allTasksSeries" />
                        </div>
                        <div class="stat_card__legend pr-20 h-full overflow-y-auto">
                            <div 
                                v-for="status in allTasks" 
                                :key="status.code" 
                                class="flex items-center whitespace-nowrap text-base my-1">
                                <a-badge :color="status.color" />
                                {{ status.name }} - {{ status.value }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="!visibleСharts.length || visibleСharts.includes('completed')" class="stat_card__col">
                <div class="stat_card">
                    <div class="stat_card__header mb-3">
                        <div class="label">{{ $t('Completed tasks') }}</div>
                    </div>
                    <div class="stat_card__body">
                        <div class="stat_card__chart">
                            <ChartCompletedTasks
                                height="238"
                                width="238"
                                :series="[completedPercent]" />
                        </div>
                        <div class="stat_card__legend">
                            <div class="mb-2 text-base whitespace-nowrap">
                                <div class="text-lg">{{ total }}</div>
                                <div>{{ $t('Total tasks' )}}</div>
                            </div>
                            <div class="text-base whitespace-nowrap">
                                <div class="text-lg">{{ completed }}</div>
                                <div>{{ $t('Done')}}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="!visibleСharts.length || visibleСharts.includes('overdue')" class="stat_card__col">
                <div class="stat_card">
                    <div class="stat_card__header mb-3">
                        <div class="label">{{ $t('Overdue tasks') }}</div>
                    </div>
                    <div class="stat_card__body">
                        <div class="stat_card__chart">
                            <ChartOverdueTasks
                                height="238"
                                width="238"
                                :series="[overduePercent]" />
                        </div>
                        <div class="stat_card__legend">
                            <div class="mb-2 text-base whitespace-nowrap">
                                <div class="text-lg">{{ total }}</div>
                                <div>{{ $t('Total tasks' )}}</div>
                            </div>
                            <div class="text-base whitespace-nowrap">
                                <div class="text-lg">{{ overdue }}</div>
                                <div>{{ $t('Overdue')}}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from 'vue'
export default {
    components: {
        ChartCompletedTasks: () => import('./SmallChartCompletedTasks.vue'),
        ChartOverdueTasks: () => import('./SmallChartOverdueTasks.vue'),
        ChartAllTasks: () => import('./SmallChartAllTasks.vue')
    },
    props: {
        taskStatistics: {
            type: Object,
            default: () => {}
        },
        visibleСharts: {
            type: Array,
            default: () => []
        },
        adaptiveChart: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            statusesTransltations: {},
            statuses: [],
        }
    },
    computed: {
        allTasks() {
            const tasks = []
            for (const key in this.taskStatistics) {
                if (this.statuses[key]) {
                    tasks.push({
                        code: key,
                        value: this.taskStatistics[key],
                        ...this.statuses?.[key]
                    })
                }
            }
            return tasks
        },
        total() {
            let total = 0
            for (const key in this.taskStatistics) {
                total += this.taskStatistics[key]
            }
            total -= this.taskStatistics?.overdue
            return total
        },
        completed() {
            return this.taskStatistics?.completed || 0
        },
        overdue() {
            return this.taskStatistics?.overdue || 0
        },
        allTasksSeries() {
            if (!this.taskStatistics) { return [0] }
            const { overdue, ...statistics } = this.taskStatistics;
            return Object.values(statistics);
        },
        allTasksLabels() {
            return this.allTasks.map(status => status.name)
        },
        completedPercent() {
            return parseInt(((this.completed / this.total) * 100).toFixed(2)) || 0
        },
        overduePercent() {
            return parseInt(((this.overdue / this.total) * 100).toFixed(2)) || 0
        },
    },
    created() {
        this.getTaskStatusesTranslations()
    },
    methods: {
        getTaskStatusesTranslations() {
            const url = '/tasks/task_status/?task_type=task'
            this.$http(url)
                .then(({ data }) => {
                    data.forEach(status => {
                        Vue.set(this.statuses, [status.code], status)
                    })
                    
                })
                .catch(error => {
                    this.$message.error(this.$t('team.failed_to_get_status_translations'))
                    console.error(error)
                })
        }
    }
}
</script>


<style lang="scss" scoped>
.stat_card__list {
    display: flex;
    margin: -15px;
}
.adaptive.stat_card__list {
    flex-wrap: wrap;
}

.stat_card__col {
    padding: 15px;
}

.stat_card{
    min-width: 400px;
    background: #fff;
    box-shadow: 0px 4px 8px 0px #0000000F;
    border-radius: 6px;
    padding: 15px 20px;
    color: #000;
    &__header{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        .user{
            opacity: 0.6;
            font-size: 14px;
            word-break: break-word;
        }
        .label{
            font-size: 16px;
            line-height: 24px;
            word-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .rate{
            margin-left: 20px;
            font-size: 14px;
            line-height: 14px;
            opacity: 0.6;
        }
    }
    .adaptive & {
        min-width: auto;

        flex-grow: 1;
    }
}

.stat_card__body {
    display: flex;
    align-items: center;
    height: 180px;
    .adaptive & {
        @media (max-width: 480px) {
            flex-direction: column;
            height: auto;
        }
    }
}

.stat_card__chart {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 180px;
    height: 180px;
    .adaptive & {
        @media (max-width: 480px) {
            margin-bottom: 16px;        
        }
    }
}

.stat_card__legend {
    margin-left: 16px;
}
</style>