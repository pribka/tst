<template>
    <apexchart 
        type="donut" 
        :options="chartOptions" 
        :width="width"
        :height="height"
        :series="series" />
</template>

<script>
import VueApexCharts from 'vue-apexcharts'

export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {
        allTasks: {
            type: Array,
            default: () => []
        },
        series: {
            type: Array,
            default: () => []
        },
        labels: {
            type: Array,
            default: () => []
        },
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
    },
    computed: {
        totalValue() {
            const ignoredKeys = ['completed', 'new', 'overdue'] 
            let resultCount = 0
            for(const key in this.taskStatistics) {
                if (!ignoredKeys.includes(key))
                    resultCount += this.taskStatistics[key]
            }
            return resultCount 
        },
        colors() {
            const antColors = {
                red: '#F5222D',
                volcano: '#FA541C',
                orange: '#FA8C16',
                gold: '#FAAD14',
                yellow: '#FADB14',
                lime: '#A0D911',
                green: '#52C41A',
                cyan: '#13C2C2',
                blue: '#1890FF',
                geekblue: '#2F54EB',
                purple: '#722ED1',
                magenta: '#EB2F96',
                grey: '#666666',
            }
            return this.allTasks.map(status => antColors[status.color] + 'BB')
        },
        chartOptions() {
            return {
                legend: { show: false },
                colors: this.colors,
                labels: this.labels,
                dataLabels: {
                    enabled: true,
                    value: {
                        formatter: (value) => parseInt(value)
                    },
                    style: {
                        fontSize: '10px',
                        colors: ['#333']
                    },
                    dropShadow: { enabled: false }
                },
                plotOptions: {
                    pie: {
                        donut: {
                            labels: {
                                show: true,
                                name: {
                                    color: '#000',
                                    offsetY: 20
                                },
                                value: {
                                    fontSize: '26px',
                                    fontWeight: 300,
                                    offsetY: -14,
                                    formatter: (value) => parseInt(value)
                                },
                                total: {
                                    show: true,
                                    fontSize: '14px',
                                    offsetY: 20,
                                    fontWeight: 600,
                                    label: this.$t('On execution'),
                                    formatter: () => this.totalValue
                                },
                            }
                        }
                    },
                },
            }
        }
    },
    data() {
        return {
        }
    },
}
</script>