<template>
    <div class="invest_graph" :class="useBackground && 'useBackground'">
        <div class="invest_graph__left">
            <apexchart
                :key="apexchartKey"
                type="donut" 
                :options="chartOptions" 
                class="chart"
                :width="chartSize.width"
                :height="chartSize.height"
                :series="seriesData" />
        </div>
        <div class="invest_graph__right">
            <div>
                <div class="graph_label">
                    {{ $t('invest.projectCost') }}
                </div>
                <div class="graph_value">
                    {{ allPrice }} {{ $t('invest.mlnTenge') }}
                </div>
                <div class="graph_list">
                    <div v-for="(source, index) in item.funding_sources" :key="source.id" class="graph_list__item">
                        <div class="list_marker" :style="`background: ${palette[index]}`" />
                        <div>
                            <div>
                                {{ source.funding_source.name }}
                            </div>
                            <div>
                                {{ source.amount }} {{ $t('invest.mlnTenge') }}
                            </div>
                        </div>
                    </div>
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
        item: {
            type: Object,
            required: true
        },
        graphColor: {
            type: String,
            default: '#f9f9f9'
        },
        useBackground: {
            type: Boolean,
            default: true
        }
    },
    components: {
        apexchart: VueApexCharts
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
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
        allPrice() {
            return Number(this.item.funds)
        },
        totalAmount() {
            return this.item.funding_sources.reduce((sum, each) => sum + Number(each.amount), 0)
        },
        allPriceStat() {
            return this.allPrice - this.totalAmount
        },
        labels() {
            let labels = this.item.funding_sources.map(each => each.funding_source.name)
            labels.push('')
            return labels
        },
        series() {
            let series = this.item.funding_sources.map(each => Number(each.amount))
            series.push(this.allPriceStat)
            return series
        },
        percent() {
            return this.allPrice ? parseInt((this.totalAmount * 100/this.allPrice).toFixed(2)) : 0
        },
        palette() {
            const numColors = this.item.funding_sources.length
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
            apexchartKey: Date.now(),
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
                                        return `${parseInt((parseInt(value) * 100/this.allPrice).toFixed(2))}%`
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '13px',
                                    fontWeight: 400,
                                    label: this.$t('invest.invest_sobrano_sredstv'),
                                    formatter: () => `${this.percent}%`
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
        item: {
            handler: 'updateChartData',
            immediate: true,
            deep: true,
        },
    },
    methods: {
        updateChartData() {
            if (this.item && this.item.funding_sources) {
                this.apexchartKey = Date.now(),
                this.chartOptions.labels = this.labels
                this.seriesData = this.series
                this.chartOptions.colors = this.palette
            }
        }        
    },
    mounted() {
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
.invest_graph{
    display: grid;
    gap: 15px;
    grid-template-columns: 1fr;
    @media (min-width: 768px) {
        grid-template-columns: 160px 1fr;
    }
    @media (min-width: 1600px) {
        grid-template-columns: 160px 1fr;
    }
    @media (min-width: 1800px) {
        grid-template-columns: 200px 1fr;
    }
    &__right{
        display: flex;
        justify-content: flex-start;
    }
    &.useBackground{
        &::v-deep{
            circle{
                fill: #f9f9f9;
            }
        }
    }
    &::v-deep{
        .chart{
            margin-left: -20px;
        }
    }
    .graph_list{
        margin-top: 10px;
        font-size: 13px;
        &__item{
            display: flex;
            align-items: baseline;
            &:not(:last-child){
                margin-bottom: 10px;
            }
            .list_marker{
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #f9f9f9;
                margin-right: 10px;
            }
        }
    }
    .graph_label{
        color: #000000;
        opacity: 0.6;
        font-size: 13px;
        margin-bottom: 6px;
    }
    .graph_value{
        color: #000000;
        font-size: 24px;
        line-height: 24px;
    }
}
</style>