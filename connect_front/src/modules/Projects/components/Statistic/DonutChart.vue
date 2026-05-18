<template>
    <div class="chart">
        <apexchart
            :key="apexchartKey"
            type="donut" 
            :options="chartOptions" 
            class="chart"
            :width="chartSize.width"
            :height="chartSize.height"
            :series="series" />
        <div class="marker-list chart__markers">
            <div v-for="(label, index) in labels" :key="label" class="legend__row">
                <div class="list_marker" :style="`background: ${palette[index]}`" />
                <div class="whitespace-nowrap">
                    {{ label }} - {{ series[index] }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        statistics: {
            type: Object,
            default: null,
        },
        // item: {
        //     type: Object,
        //     // required: true,
        //     default: null,
        // },
        graphColor: {
            type: String,
            default: '#f9f9f9'
        },
    },
    components: {
        apexchart: VueApexCharts
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        series() {
            return this.statistics?.series || []
        },
        chartSize() {
            if(this.windowWidth < 1800) {
                if(this.windowWidth < 1650) {
                    if(this.windowWidth < 768) {
                        return {
                            width: '130px',
                            height: '130px'
                        }
                    } else {
                        return {
                            width: '180px',
                            height: '180px'
                        }
                    }
                } else {
                    return {
                        width: '200px',
                        height: '200px'
                    }
                }
            } else {
                return {
                    width: '230px',
                    height: '230px'
                }
            }
        },
        labels() {
            // let labels = this.item.funding_sources.map(each => each.funding_source.name)
            // labels.push('')
            // return labels
            return this.statistics?.labels || []
        },
        palette() {
            const numColors = this.labels.length
            const palette = []
            const saturation = 60
            const lightness = 50

            for (let i = 0; i < numColors; i++) {
                const hue = Math.round((360 / numColors) * i)
                palette.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
            }
            palette.push(this.graphColor)
            return palette
        }
    },
    data() {
        return {
            tab: 1,
            apexchartKey: Math.floor(new Date().getTime() / 1000),
            chartOptions: {
                stroke: {
                    width: 0
                },
                legend: {
                    show: false
                },
                colors: [],
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
                chart: {
                    foreColor: '#000'
                },
                plotOptions: {
                    pie: {
                        customScale: 1,
                        startAngle: 1,
                        donut: {
                            size:'90%',
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
                                    formatter: (value) => {
                                        // eslint-disable-next-line radix
                                        return `${parseInt((parseInt(value) * 100/43).toFixed(2))}%`
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '13px',
                                    fontWeight: 400,
                                    label: this.statistics.totalLabel,
                                    formatter: (value) => value.globals.seriesTotals.reduce((a, b) => {
                                        return a + b
                                    }, 0)
                                },
                            }
                        }
                    },
                },
                labels: []
            }
        }
    },
    watch: {
        // item: {
        //     handler: 'updateChartData',
        //     immediate: true,
        //     deep: true,
        // },
    },
    methods: {
        updateChartData() {
            this.apexchartKey = Date.now(),
            this.chartOptions.labels = this.labels
            this.chartOptions.colors = this.palette
        }        
    },
    mounted() {
        this.updateChartData()
        eventBus.$on('update_price_chart', () => {
            this.updateChartData()
        })
    },
    beforeDestroy() {
        eventBus.$off('update_price_chart')
    }
}
</script>

<style lang="scss" scoped>
$md: 768px;
.chart {
    display: flex;
    align-items: center;
    flex-direction: column;
    @media (min-width: $md) {
        flex-direction: row;
    }
}

.chart__markers {
    margin-top: 15px;
    @media (min-width: $md) {
        margin-top: 0;
        margin-left: 30px;
    }
}

.legend__row {
    display: flex;
    align-items: center;
    &:not(:last-child) {
        margin-bottom: 10px;
    }
}

.marker-list {
    @media (min-width: $md) {
        padding-right: 12px;
        margin-right: -12px;
    }
}

.list_marker {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #f9f9f9;
    margin-right: 10px;
}
</style>