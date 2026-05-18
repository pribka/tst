<template>
    <ReportCard>
        <template v-slot:h_title>
            {{ $t('reports_mobule.projects_control') }}
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
                        <div class="all">{{ $t('reports_mobule.project_count') }} {{ statData.projects_count }}</div>
                        <!--<div class="stat_nums">{{ mainStat.work }}/{{ mainStat.other }}</div>-->
                    </div>
                    <div class="stat_wrap__line dummy"></div>
                    <!--
                    <div class="stat_wrap__line">
                        <div class="line" :style="`width: ${mainStat.percent}%;`" :class="mainStat.percent <= 15 && 'stat_rg'">
                            <span>{{ mainStat.percent }}%</span>
                        </div>
                    </div>-->
                </div>
                <!--
                <div class="trend_btn o_green ml-2">
                    <i class="fi fi-rr-angle-small-up" />
                </div>-->
            </div>
            <div v-for="item in statData.organizations"  :key="item.id" class="item_card">
                <div>
                    <div class="title" :title="item.name">{{ item.name }}</div>
                    <div v-if="item.director" class="user">{{ item.director.full_name }}</div>
                </div>
                <div class="flex items-center">
                    <div class="count">{{ item.projects_count }}</div>
                    <div class="percent_count">
                        <div class="percent">{{ projectPercent(item) }}%</div>
                        <a-progress 
                            :percent="projectPercent(item)" 
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
    data() {
        return {
            value: []
        }
    },
    methods: {
        projectPercent(item) {
            if (!this.statData || this.statData.projects_count === 0)
                return 0
            return Math.round((item.projects_count / this.statData.projects_count) * 100)
        }
    }
}
</script>

<style lang="scss" scoped>
@import "./card_style.scss";
</style>
