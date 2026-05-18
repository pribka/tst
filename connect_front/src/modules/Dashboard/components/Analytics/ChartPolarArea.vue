<template>
    <apexchart 
        type="polarArea" 
        class="chart"
        :options="chartOptions" 
        :width="width"
        :series="series" />
</template>

<script>
import VueApexCharts from 'vue-apexcharts'

export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {

        analytics: {
            type: Array,
            default: () => []            
        },
        // series: {
        //     type: Array,
        //     default: () => []
        // },
        taskStatistics: {
            type: Object,
            default: () => {}
        },
        legendPosition: {
            type: String,
            default: 'bottom'
        },
        legendWidth: {
            type: String,
            default: '100%'
        },
        height: {
            type: String,
            default: '100%'
        },
        width: {
            type: String,
            default: '100%'
        },
        // labels: {
        //     type: Array,
        //     default: () => []
        // }
    },
    computed: {
        series() {
            return this.getSeries(this.analytics) || []
        },
        labels() {
            return this.getLabels(this.analytics) || []
        },
        totalValue() {
            if(this.taskStatistics) {
                const processed = JSON.parse(JSON.stringify(this.taskStatistics))
                delete processed.completed
                delete processed.new
                let resultCount = 0
                for(const key in processed) {
                    resultCount += processed[key]
                }
                return resultCount
            }
            return 0
        },
        chartOptions() {
            return {
                legend: {
                    show: false,
                    position: this.legendPosition,
                    fontSize: '14px',
                    offsetX: 0,
                    width: this.legendWidth,
                },
                colors: [
                    '#067fd8',
                    '#fa9800',
                    '#9641e5',
                    '#d341ee',
                    '#00aeab',
                    '#c2d88e',
                    '#f7636f'
                ],
                chart: {
                    type: 'polarArea',
                },
                stroke: { 
                    // Должно быть и быть пустым
                },
                fill: {
                    opacity: 0.5
                },
                yaxis: {
                    labels: {
                        formatter: (value) => { return value.toFixed(0) },
                    },
                },
                labels: this.labels
            }
        }
        
    },
    data() {
        return {

        }
    },
    methods: {
        getLabels() {
            return this.analytics.map(analyticsItem => analyticsItem.name)
        },
        getSeries() {
            return this.analytics.map(analyticsItem => analyticsItem.value)
        },
    }
}
</script>

<style lang="scss" scoped>
.chart::v-deep {
    .apexcharts-text {
        font-size: 8px;
        font-weight: 900;
    }
}
</style>