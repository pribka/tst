<template>
    <apexchart 
        type="donut" 
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
                stroke: {
                    width: 4,
                    colors: ['#fff'],
                    lineCap: 'square'
                },
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
                dataLabels: {
                    enabled: false,
                    value: {
                        formatter(value) {
                            // eslint-disable-next-line radix
                            return `${parseInt(value)}%`
                        }
                    },
                    style: {
                        fontSize: '10px',
                        colors: ['#333']
                    },
                    dropShadow: {
                        enabled: false
                    }
                },
                plotOptions: {
                    pie: {
                        customScale: 1,
                        donut: {
                            labels: {
                                show: true,
                                name: {
                                    fontSize: '2rem',
                                    color: '#000',
                                    offsetY: 20
                                },
                                value: {
                                    fontSize: '1.8rem',
                                    fontWeight: 300,
                                    offsetY: -14,
                                    formatter(value) {
                                        // eslint-disable-next-line radix
                                        return `${parseInt(value)}`
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '0.8rem',
                                    fontWeight: 600,
                                    label: 'Всего',
                                    formatter: () => this.series.reduce((total, current) => total + current, 0)
                                },
                            }
                        }
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