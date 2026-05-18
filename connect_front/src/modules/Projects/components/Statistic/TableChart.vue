<template>
    <div>
        <div class="chart-table">
            <div class="chart-table__row" v-for="item in statistics" :key="item.id">
                <span>{{ item.name }}</span>
                <span>{{ $moment(item.dead_line).format('DD.MM.YYYY') }}</span>
                <div class="text-center">
                    <StatusRow :record="item" :text="item.status" />
                </div>
            </div>
        </div>
        <div class="chart-cards">
            <div class="card chart-cards__item" v-for="item in statistics" :key="item.id">
                <StatusRow :record="item" :text="item.status" />
                <div class="card__title">
                    <span class="card__name" :title="item.name">{{ item.name }}</span>
                    <span class="ml-4">{{ $moment(item.dead_line).format('DD.MM.YYYY') }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import StatusRow from '@/components/TableWidgets/Widgets/StatusRow.vue';
export default {
    props: {
        statistics: {
            type: Array,
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
    components: { StatusRow },
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
                            width: '230px',
                            height: '230px'
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
        // allPrice() {
        //     return Number(this.item.funds)
        // },
        // totalAmount() {
        //     return this.item.funding_sources.reduce((sum, each) => sum + Number(each.amount), 0)
        // },
        // allPriceStat() {
        //     return this.allPrice - this.totalAmount
        // },
        labels() {
            // let labels = this.item.funding_sources.map(each => each.funding_source.name)
            // labels.push('')
            // return labels
            return this.statistics?.labels || []
        },
        // series() {
        //     let series = this.item.funding_sources.map(each => Number(each.amount))
        //     series.push(this.allPriceStat)
        //     return series
        // },
        // percent() {
        //     return this.allPrice ? parseInt((this.totalAmount * 100/this.allPrice).toFixed(2)) : 0
        // },
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
            seriesData: [],
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
            // if (this.item && this.item.funding_sources) {
            this.apexchartKey = Date.now(),
            this.chartOptions.labels = this.labels
            this.seriesData = this.series
            this.chartOptions.colors = this.palette
            // }
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
$xs: 320px;
$md: 768px;

.chart-table {
    display: none;
    max-height: 234px;
    padding-right: 12px;
    margin-right: -12px;
    overflow-y: auto;
    @media (min-width: $md) {
        display: block;
    }
}

.chart-table__row {
    display: grid;
    grid-template-columns: 3fr 1fr 100px;
    align-items: center;
    column-gap: 40px;
    padding: 20px 0;
    line-height: 1;
    &:not(:first-child) {
        border-top: 1px solid rgba(97, 121, 250, 0.3);
    }
    &:first-child {
        padding-top: 0;
    }
    &:last-child {
        padding-bottom: 0;
    }
}

.chart-cards {
    display: block;
    margin: -10px;
    @media (min-width: $md) {
        display: none;
    }

}

.chart-cards__item {
    margin: 10px;
}

.card {
    padding: 6px 8px ;
    border: 1px solid #d4d4d4;
    border-radius: 8px;
}

.card__title {
    display: flex;
    justify-content: space-between;
    min-width: 0;
    margin-top: 6px;
}

.card__name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    @media (min-width: $md) {
        overflow: unset;
        white-space: unset;
        text-overflow: unset;
    }
}
</style>
