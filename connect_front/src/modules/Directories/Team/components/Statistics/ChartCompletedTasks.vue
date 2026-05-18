<template>
    <apexchart 
        type="radialBar" 
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
            default: () => [0]
        },
        height: {
            type: String,
            default: '100%'
        },
        width: {
            type: String,
            default: '100%'
        },
        // offset: {
        //     type: Boolean,
        //     default: false
        // },
    },
    computed: {
    },
    data() {
        return {
            chartOptions: {
                chart: {
                    type: 'radialBar',
                    offsetY: this.offset && -10,
                    sparkline: {
                        enabled: true
                    }
                },
                plotOptions: {
                    radialBar: {
                        hollow: {
                            margin: 10,
                            size: 70
                        },
                        track: {
                            background: "#eff2f5",
                            dropShadow: {
                                enabled: false
                            }
                        },
                        dataLabels: {
                            name: {
                                show: false
                            },
                            value: {
                                offsetY: 7,
                                fontSize: '26px',
                                fontWeight: 300,
                            }
                        }
                    }
                },
                grid: {
                    padding: {
                        // top: this.offset && -10
                    }
                },
                fill: {
                    colors: ['#76bb02']
                },
                labels: [this.$t('team.completed')],
            },
        }
    }
}
</script>