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
    },
    computed: {
    },
    data() {
        return {
            chartOptions: {
                fill: {
                    colors: ['#76bb02']
                },
                labels: [this.$t('Done')],
                plotOptions: {
                    radialBar: {
                        dataLabels: {
                            name: {
                                fontSize: '14px',
                                offsetY: 20,
                                fontWeight: 600,
                            },
                            value: {
                                fontSize: '26px',
                                fontWeight: 300,
                                offsetY: -14,
                                formatter: (value) => parseInt(value) + '%'
                            }
                        }
                    },
                },
            },
        }
    }
}
</script>