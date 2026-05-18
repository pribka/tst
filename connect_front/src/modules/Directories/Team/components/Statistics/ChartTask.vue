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
        series: {
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
        }
    },
    data() {
        return {
            chartOptions: {
                stroke: {
                    width: 4,
                    colors: ['#fff'],
                    lineCap: 'square'
                },
                legend: {
                    show: true,
                    position: this.legendPosition,
                    fontSize: '14px',
                    offsetX: 0,
                    width: this.legendWidth,
                },
                colors: [
                    '#80c6ff',
                    '#ca97ca',
                    '#ffc618',
                    '#c2d88e',
                    '#f7636f',
                    '#c2d88e',
                    '#f7636f'
                ],
                dataLabels: {
                    enabled: true,
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
                                    label: this.$t('team.in_execution'),
                                    formatter: () => this.totalValue
                                },
                            }
                        }
                    },
                },
                labels: [
                    this.$t('New tasks'),
                    this.$t('In work'),
                    this.$t('On pause'),
                    this.$t('On check'),
                    this.$t('On rework'),
                    this.$t('Completed'),
                ]
            }

        }
    },
    created() {
        // this.getStatisticsByOrganization()
    },
    methods: {
        // async getStatisticsByOrganization() {
        //     const params = {
        //         filters: {
        //             organization: this.organization.id
        //         }
        //     }
        //     const { data } = await this.$http.post(`/tasks/task_kanban/status_count/`, params)

        //     const series = []
        //     for(const key in data) {
        //         series.push(data[key])
        //     }
        //     this.series = series
        // }
    }
}
</script>