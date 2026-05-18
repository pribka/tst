<template>
    <div 
        v-if="data" 
        class="group_stat_card">
        <h2>
            {{ $t('wgr.all_difficulty') }}
        </h2>
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
                        {{ $t('wgr.overall_rating') }}
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
import { priceFormatter } from '@/utils'
export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        getAsideStat() {
            return this.stData
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
            loading: false,
            stData: null
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        chartColor(index) {
            switch (index) {
            case 0:
                return '#80c6ff'
                break;
            case 1:
                return '#c2d88e'
                break;
            case 2:
                return '#ca97ca'
                break;
            case 3:
                return '#ffc618'
                break;
            case 4:
                return '#88c240'
                break;
            case 5:
                return '#008ffb'
                break;
            default:
                return '#816bf8'
            }
        },
        async getInfo() {
            if(!this.data) {
                try {
                    this.loading = true
                    const { data } = await this.$http('/tasks/difficulty/aggregate/', {
                        params: {
                            obj: this.id
                        }
                    })
                    if(data) {
                        this.stData = data
                    }
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
.group_stat_card{
    border: 1px solid var(--borderColor);
    border-radius: var(--borderRadius);
    .list{
        .item{
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
    }
}
</style>