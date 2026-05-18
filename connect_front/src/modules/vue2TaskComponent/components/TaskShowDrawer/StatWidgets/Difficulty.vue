<template>
    <div 
        v-if="data" 
        class="stat_widget">
        <div class="label text-sm font-semibold">
            {{ stat.title }}
        </div>
        <div class="stat_wrapper">
            <div 
                v-if="statData && statData.length"
                class="w-full flex justify-center mt-2">
                <div style="max-width: 250px;">
                    <apexchart 
                        type="donut" 
                        :options="chartOptions" 
                        :series="series" />
                </div>
            </div>
            <div class="list">
                <div class="item flex items-center justify-between">
                    <span class="flex items-center">
                        <a-badge 
                            color="purple"
                            class="ml-2" />
                        {{ $t('task.overall_rating') }}
                    </span>
                    <span class="text-sm font-semibold pl-2">
                        {{ data.total_avg }}
                    </span>
                </div>
                <template v-if="statData && statData.length">
                    <div 
                        v-for="item in statData"
                        :key="item.criterion.id"
                        class="item flex items-center justify-between">
                        <span class="flex items-center">
                            <a-badge 
                                :color="item.color"
                                class="ml-2" />
                            {{ item.label }}:
                        </span>
                        <span>
                            {{ item.score_avg }}
                        </span>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
import statMixins from './statMixins.js'
import { priceFormatter } from '@/utils'
export default {
    components: {
        apexchart: VueApexCharts
    },
    mixins: [
        statMixins
    ],
    computed: {
        getAsideStat() {
            return this.$store.getters['task/getAsideStat'](this.task.id, this.stat.key)
        },
        data() {
            if(this.getAsideStat?.total_avg)
                return this.getAsideStat
            else
                return null
        },
        percent() {
            return this.data.total_avg * this.data.max_value
        },
        statData() {
            if(this.getAsideStat.detail_avg?.length)
                return this.getAsideStat.detail_avg.map((item, index) => {
                    return {
                        ...item,
                        label: item.criterion.name,
                        color: this.chartColor(index)
                    }
                })
            else
                return []
        },
        series() {
            return this.statData.map(item => item.score_avg)
        },
        chartOptions() {
            return {
                colors: this.statData.map(item => item.color),
                chart: {
                    type: 'pie'
                },
                legend: {
                    show: false
                },
                labels: this.statData.map(item => item.label),
                markers: {
                    colors: ['#F44336', '#E91E63', '#9C27B0']
                }
            }
        }
    },
    data() {
        return {
            loading: false
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        async getInfo() {
            if(!this.data) {
                try {
                    this.loading = true
                    await this.$store.dispatch('task/getAsideStat', {
                        task: this.task,
                        part: this.stat.key
                    })
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.stat_widget{
    border: 1px solid var(--borderColor);
    border-radius: var(--borderRadius);
    .label{
        padding: 10px 15px;
    }
    .list{
        .item{
            &:not(:last-child){
                margin-bottom: 8px;
            }
        }
    }
}
.stat_wrapper{
    padding: 0px 15px 10px 15px;
}
</style>