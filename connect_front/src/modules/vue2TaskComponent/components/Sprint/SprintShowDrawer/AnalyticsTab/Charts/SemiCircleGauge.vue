<template>
    <div class="">
        <div class="chart-wrapper mx-auto">
            <apexchart 
                type="radialBar" 
                :options="chartOptions" 
                :series="series"/>
        </div>
        <p class="text-center -mt-10 mb-6">{{ name }}</p>

        <p class="">{{ $t('task.breakdown') }}</p>
        <ul class="text-muted">
            <li class="mt-3">
                {{ $t('task.sprint_rating_0_1') }}
            </li>
            <li class="mt-3">
                {{ $t('task.sprint_rating_1_2') }}
            </li>
            <li class="mt-3">
                {{ $t('task.sprint_rating_2_3') }}
            </li>
            <li class="mt-3">
                {{ $t('task.sprint_rating_3_4') }}
            </li>
            <li class="mt-3">
                {{ $t('task.sprint_rating_4_5') }}
            </li>
        </ul>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'

export default {
    components: {
        apexchart: VueApexCharts,
    },
    props: {
        chartData: {
            type: Object,
            default: () => ({ value: 0, name: ''})
        }
    },
    computed: {
        series() {
            if (this.chartData?.value) {
                return [this.chartData.value / 5 * 100]
            }
            return [0]
        },
        name() {
            return this.chartData?.name || ''
        }
    },
    data() {
        return {
            chartOptions: {
                chart: {
                    type: 'radialBar',
                    offsetY: -20,
                    sparkline: {
                        enabled: true
                    }
                },
                plotOptions: {
                    radialBar: {
                        startAngle: -90,
                        endAngle: 90,
                        hollow: {
                            size: '60%' 
                        },
                        track: {
                            background: "#e7e7e7",
                        },
                        dataLabels: {
                            name: {
                                show: false,
                                // fontSize: '14px',
                                // color: '##2D2D2D',
                                // fontWeight: '400',
                                // offsetY: 20,
                                // formatter: () => this.name,
                            },
                            value: {
                                offsetY: -20,
                                fontSize: '36px',
                                formatter: () => this.chartData.value
                            }
                        }
                    }
                },
                grid: {
                    padding: {
                        top: -10
                    }
                },
                fill: {
                    type: 'solid',
                    colors: ['#A8C985'],
                },
            },
          
          
        };
    },
        
    
}
</script>

<style scoped>
.text-muted {
    color: var(--functional-text-muted);
}
.chart-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    max-width: 320px;
    height: 180px;
}
</style>