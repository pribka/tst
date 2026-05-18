<template>
    <apexchart 
        type="bar" 
        height="230"

        class="w-full max-h-full"
        :options="chartOptions" 
        :series="series" />
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        statistics: {
            type: Object,
            default: () => {},
        },
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

        // series() {
        //     return [{
        //         // name: 'Inflation',
        //         data: [12,10,10,10,10,10,10,10,10,10,21]
        //     }]
        // },
        chartSize() {
            if(this.windowWidth < 1800) {
                if(this.windowWidth < 1650) {
                    if(this.windowWidth < 768) {
                        return {
                            width: '230px',
                            height: '500px'
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
            return ["РБ – республиканский бюджет","За счет инвестора","Планируется","МБ – местный бюджет","МБ – местный бюджет","НФ – Национальный Фонд","Планируется","РБ – республиканский бюджет","За счет инвестора","ДИ – дополнительные инвестиции",""]
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
            apexchartKey: new Date(),
            chartOptions: {
                chart: {
                    type: 'rangeBar',
                    // height: 'auto',
                    toolbar: {
                        show: false,
                    },
                },
                grid: {
                    show: true,
                    strokeDashArray: 10,
                    // borderColor: this.appTheme.primaryOp2,
                    xaxis: {
                        lines: {
                            show: true,
                        },
                    },
                    yaxis: {
                        lines: {
                            show: false,
                        },
                    },
                },
                // colors: [this.appTheme.primary],
                plotOptions: {
                    bar: {
                        horizontal: true,
                        borderRadius: 10,
                        columnWidth: '50%',
                        dataLabels: {
                            position: 'center',
                        },
                    },
                },
                dataLabels: {
                    style: {
                        fontSize: '14px',
                        // fontFamily: this.appTheme.fontFamily,
                        fontWeight: 400,
                    },
                    formatter: function (val) {
                        return `${val}%`;
                    },
                },
                xaxis: {
                    tickPlacement: 'between',
                    position: 'top',
                    axisBorder: {
                        show: false,
                    },
                    axisTicks: {
                        show: false,
                    },
                    crosshairs: {
                        show: false,
                    },
                    type: 'category',
                    categories: this.statistics.series.map(item => { return item.label.split(' ')}),
                    labels: {
                        hideOverlappingLabels: false,
                        trim: false,
                        rotate: 0,
                        minWidth: 0,
                        maxWidth: 150,
                        style: {
                            // colors: [this.appTheme.textPrimary],
                            // fontFamily: this.appTheme.fontFamily,
                            fontSize: '14px',
                            cssClass: 'opacity-60',
                        },
                        formatter: function (val) {
                            return val;
                        },
                    },
                },
                tooltip: {
                    style: {
                        // fontFamily: this.appTheme.fontFamily,
                    },
                    marker: {
                        show: false,
                    },
                },
                yaxis: {
                    min: -100,
                    max: 100,
                    forceNiceScale: true,
                    stepSize: 25,
                    labels: {
                        maxWidth: 150,
                        align: 'left',
                        style: {
                            // colors: [this.appTheme.textPrimary],
                            // fontFamily: this.appTheme.fontFamily,
                            fontSize: '13px',
                        },
                    },
                },
            },
            series: [
                {
                    name: this.statistics.seriesUnit,
                    data: this.statistics.series
                    // [
                    //     {
                    //         x: '',
                    //         y: [0, 100],
                    //     },
                    //     {
                    //         x: '',
                    //         y: [0, 70],
                    //     },
                    //     {
                    //         x: '',
                    //         y: [0, -75],
                    //     },
                    // ],
                },
            ],
        }
    },
    methods: {
        updateChartData() {
            // if (this.item && this.item.funding_sources) {
            this.apexchartKey = Date.now(),
            this.chartOptions.labels = this.labels
            this.chartOptions.colors = this.palette
            // }
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

</style>