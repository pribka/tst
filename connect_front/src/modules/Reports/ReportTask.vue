<template>
    <ReportCard>
        <template v-slot:h_title>
            {{ $t('reports_mobule.task_control') }}
        </template>
        <!--<template v-slot:h_range>
            <a-range-picker 
                separator="-" 
                v-model="value"
                :allowClear="false"
                :placeholder="['Начало', 'Конец']"
                :showTime="false"
                format="DD MMMM"
                valueFormat="YYYY-MM-DD"
                size="small">
                <template slot="suffixIcon">
                    <i class="fi fi-rr-calendar-lines blue_color" />
                </template>
            </a-range-picker>
        </template>-->
        <template v-if="statData">
            <div class="main_stat flex items-end mb-5">
                <div class="stat_wrap w-full">
                    <div class="stat_wrap__header flex items-center justify-between mb-2">
                        <div class="all">{{ $t('reports_mobule.task_count') }} {{ statData.tasks_count }}</div>
                        <div class="stat_nums">{{ statData.tasks_overdue_count }}/{{ taskOtherCount }}</div>
                    </div>
                    <div class="stat_wrap__line">
                        <div class="line" :style="`width: ${tasksCompletionRate}%;`" :class="tasksCompletionRate <= 15 && 'stat_rg'">
                            <span>{{ tasksCompletionRate }}%</span>
                        </div>
                    </div>
                </div>
                <!--<div class="trend_btn o_green ml-2">
                    <i class="fi fi-rr-angle-small-up" />
                </div>-->
            </div>
            <div v-for="item in statData.organizations" :key="item.id" class="item_card">
                <div>
                    <div class="title" :title="item.name">{{ item.name }}</div>
                    <div v-if="item.director" class="user">{{ item.director.full_name }}</div>
                </div>
                <div class="flex items-center">
                    <div class="count">{{ item.tasks_count }}</div>
                    <div class="percent_count">
                        <div class="percent">{{ tasksCompletePercent(item) }}%</div>
                        <a-progress 
                            :percent="tasksCompletePercent(item)" 
                            :strokeWidth="10"
                            class="percent_progress"
                            strokeColor="#67dd9f"
                            :show-info="false" />
                    </div>
                    <!--<div class="trend_btn o_green ml-3">
                        <i class="fi fi-rr-angle-small-up" />
                    </div>-->
                </div>
            </div>
        </template>
        <template v-else>
            <CardLoader />
        </template>
    </ReportCard>
</template>

<script>
export default {
    components: {
        ReportCard: () => import('./ReportCard.vue'),
        CardLoader: () => import('./CardLoader.vue')
    },
    props: {
        statData: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        tasksCompletionRate() {
            if (!this.statData || this.statData.tasks_count === 0)
                return 0
            const nonOverdueTasks = this.statData.tasks_count - this.statData.tasks_overdue_count
            return Math.round((nonOverdueTasks / this.statData.tasks_count) * 100)
        },
        taskOtherCount() {
            return this.statData.tasks_count - this.statData.tasks_overdue_count
        }
    },
    data() {
        return {
            value: [],
            mainStat: {
                count: 743,
                work: 123,
                other: 500,
                percent: 10
            }
        }
    },
    methods: {
        tasksCompletePercent(item) {
            if (!item || item.tasks_count === 0)
                return 0
            const nonOverdueTasks = item.tasks_count - item.tasks_overdue_count
            return Math.round((nonOverdueTasks /item.tasks_count) * 100)
        }
    }
}
</script>

<style lang="scss" scoped>
@import "./card_style.scss";
</style>
