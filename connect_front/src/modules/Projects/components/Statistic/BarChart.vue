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
        // labels() {
        //     return ["РБ – республиканский бюджет","За счет инвестора","Планируется","МБ – местный бюджет","МБ – местный бюджет","НФ – Национальный Фонд","Планируется","РБ – республиканский бюджет","За счет инвестора","ДИ – дополнительные инвестиции",""]
        // },
        // seriesData() {
        //     return this.statistics.funds || []
        // },
        palette() {
            const numColors = this.statistics.series.length
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
                chart: {
                    type: 'bar',
                    // height: 'auto',
                    toolbar: {
                        show: false,
                    },
                },
                grid: {
                    show: true,
                    strokeDashArray: 10,
                },
                plotOptions: {
                    bar: {
                        horizontal: false,
                        borderRadius: 10,
                        borderRadiusApplication: 'end',
                        borderRadiusWhenStacked: 'last',
                        columnWidth: '50%',
                        dataLabels: {
                            position: 'top',
                        },
                    },
                },
                dataLabels: {
                    offsetY: 10,
                    style: {
                        fontSize: '14px',
                        // fontFamily: this.appTheme.fontFamily,
                        fontWeight: 400,
                    },
                },
                xaxis: {
                    tickPlacement: 'between',
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
                    categories: 
                        this.statistics.series.map(item => { return item.x.split(' ')})
                    ,
                    labels: {
                        hideOverlappingLabels: false,
                        maxHeight: 120,
                        trim: false,
                        rotate: 0,
                        minWidth: 0,
                        maxWidth: 500,
                        style: {
                            // colors: [this.appTheme.textPrimary],
                            // fontFamily: this.appTheme.fontFamily,
                            fontSize: '13px',
                        },
                        formatter: function (val) {
                            return val;
                        },
                    },
                },
                yaxis: {
                    labels: {
                        offsetX: -5,
                        offsetY: 4,
                        style: {
                            // colors: [this.appTheme.textPrimary],
                            // fontFamily: this.appTheme.fontFamily,
                            fontSize: '14px',
                            cssClass: 'opacity-60',
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
            },
            series: [
                {
                    name: this.statistics.seriesUnit,
                    data: this.statistics.series || []
                },
            ],
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
            // if (this.item && this.item.funding_sources) {
            this.apexchartKey = Date.now(),
            // this.chartOptions.labels = this.labels
            // this.seriesData = this.statistics.funds
            this.chartOptions.colors = ['#1D65C0'] || this.palette
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