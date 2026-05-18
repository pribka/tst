<template>
    <div class="group_stat_card">
        <h2>
            {{ $t('wgr.all_task') }}
        </h2>
        <apexchart 
            type="donut" 
            :options="chartOptions" 
            :series="series" />
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
            required: true
        }
    },
    computed: {
        series() {
            return [
                this.stat.new, 
                this.stat.in_work, 
                this.stat.on_pause, 
                this.stat.on_check,
                this.stat.on_rework
            ]
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
                    position: 'bottom',
                    fontSize: '14px',
                },
                colors: [
                    '#80c6ff',
                    '#ca97ca',
                    '#ffc618',
                    '#c2d88e',
                    '#f7636f'
                ],
                dataLabels: {
                    enabled: true,
                    value: {
                        formatter(val) {
                            // eslint-disable-next-line radix
                            return `${parseInt(val)}%`
                        }
                    },
                    style: {
                        fontSize: '10px'
                    },
                    dropShadow: {
                        enabled: false
                    }
                },
                plotOptions: {
                    pie: {
                        customScale: 1,
                        donut: {
                            size: '60%',
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
                                    formatter(val) {
                                        // eslint-disable-next-line radix
                                        return `${parseInt(val)}`
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '0.8rem',
                                    fontWeight: 600,
                                    label: this.$t('wgr.on_performance')
                                }
                            }
                        }
                    },
                },
                labels: [
                    this.$t('wgr.new'), 
                    this.$t('wgr.work'),
                    this.$t('wgr.pause'), 
                    this.$t('wgr.review'),
                    this.$t('wgr.rework')
                ]
            }
        }
    }
}
</script>