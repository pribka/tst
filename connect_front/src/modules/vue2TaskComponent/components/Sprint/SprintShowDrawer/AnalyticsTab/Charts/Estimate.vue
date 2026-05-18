<template>
    <div class="chart_block donut_chart">
        <div class="chart_block__label">
            {{ $t('task.general_estimate') }}
        </div>
        <apexchart 
            type="donut" 
            :options="chartOptions" 
            class="w-full"
            :series="series" />
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
export default {
    components: {
        apexchart: VueApexCharts
    },
    data() {
        return {
            series: [2300, 5400],
            chartOptions: {
                responsive: [{
                    breakpoint: 4000,
                    options: {
                        chart: {
                            height: 250
                        }
                    }
                }],
                chart: {
                    type: 'donut'
                },
                stroke:{
                    colors: "#FAFAFA",
                    width: 2
                },
                legend: {
                    fontFamily: 'Roboto',
                    position: 'right',
                    horizontalAlign: 'center', 
                    verticalAlign: 'center',
                    fontSize: '14px',
                    color: '#000',
                    formatter: function(seriesName, opts) {
                        return seriesName
                    },
                    markers: {
                        width: 20,
                        height: 20,
                        radius: 4,
                        offsetY: 5
                    },
                    itemMargin: {
                        horizontal: 0,
                        vertical: 5
                    },
                    onItemHover: {
                        highlightDataSeries: true
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                plotOptions: {
                    expandOnClick:false,
                    pie: {
                        customScale: 1,
                        borderRadius: 10,
                        donut: {
                            size:'88%',
                            background: 'transparent',
                            labels: {
                                show: true,
                                name: {
                                    fontSize: '16px',
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    offsetY: 25
                                },
                                value: {
                                    show: true,
                                    fontSize: '36px',
                                    fontWeight: 300,
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    offsetY: -15,
                                    formatter: (value) => {
                                        return value
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '16px',
                                    fontWeight: 400,
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    label: this.$t('task.thousand_tenge'),
                                    formatter: () => 5400
                                }
                            }
                        }
                    },
                },
                colors: [
                    '#0f68c1',
                    '#56bcc8',
                ],
                labels: [
                    this.$t('task.total_sum'), 
                    this.$t('task.other_expenses'), 
                ]
            }
        }
    }
}
</script>