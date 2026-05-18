<template>
    <div class="group_stat_card">
        <h2>
            {{ $t('project.tasks_complete') }}
        </h2>
        <div class="stat_wrap">
            <apexchart 
                type="radialBar" 
                :options="chartOptions" 
                :series="series" />
        </div>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {
        stat: {
            type: Object,
            require: true
        }
    },
    computed: {
        series() {
            return [this.stat.completed_percent]
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
                        hollow: {
                            margin: 0,
                            size: '55%'
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
                        top: -10
                    }
                },
                fill: {
                    colors: ['#76bb02']
                },
                labels: [this.$t('project.done')],
            },
        }
    }
}
</script>

<style lang="scss" scoped>
.group_stat_card{
    .stat_wrap{
        height: calc(100% - 35px);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }
}
</style>