<template>
    <apexchart 
        type="bar" 
        :options="chartOptions" 
        width="400"
        height="300"
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
        colors: {
            type: Array,
            default: () => []
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
            const data = this.getSeries(this.analytics)
            if(data?.length) {
                return [{ data: data }]
            }
            return []
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
                chart: {
                    height: 350,
                    
                    type: 'bar',
                    events: {
                        click: function(chart, w, e) {
                            // console.log(chart, w, e)
                        }
                    }
                },
                colors: this.colors,
                plotOptions: {
                    bar: {
                        columnWidth: '45%',
                        distributed: true,
                    }
                },
                dataLabels: {
                    enabled: false
                },
                legend: {
                    show: false
                },
                xaxis: {
                    categories: this.labels,
                    labels: {
                        style: {
                            colors: this.colors,
                            fontSize: '12px'
                        }
                    }
                }
            }
        }
    },
    data() {
        return {

        }
    },
    methods: {
        getLabels() {
            return this.analytics.map(analyticsItem => analyticsItem.name.split(' '))
        },
        getSeries() {
            return this.analytics.map(analyticsItem => analyticsItem.value)
        },
    }
}
</script>