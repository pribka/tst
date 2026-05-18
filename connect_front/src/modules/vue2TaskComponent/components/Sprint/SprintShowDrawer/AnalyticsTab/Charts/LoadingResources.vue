<template>
    <div class="chart_block donut_chart">
        <div class="chart_block__header">
            <div class="chart_block__header--label">
                {{ $t('task.resource_loading') }}
            </div>
            <div class="flex items-center md:ml-5">
                <div class="flex items-center">
                    <a-badge color="#1b66c1" />
                    {{ $t('task.actual') }}
                </div>
                <!--<div class="flex items-center ml-3">
                    <a-badge color="#56bcc8" />
                    Фактическая
                </div>-->
            </div>
        </div>
        <a-spin :spinning="loading" class="w-full">
            <div class="chart_wrapper">
                <div class="chart_wrapper__scroll">
                    <apexchart 
                        type="bar" 
                        height="300" 
                        class="w-full"
                        :options="chartOptions" 
                        :series="series" />
                </div>
            </div>
        </a-spin>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        taskSetFilter: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            series: [{
                name: this.$t('task.time_spent_short'),
                data: []
            }],
            chartOptions: {
                legend: {
                    show: false
                },
                chart: {
                    type: 'bar',
                    height: 300,
                    toolbar: {
                        show: false
                    },
                    events: {
                        legendClick: (chartContext, seriesIndex) => {
                            const { data } = this.series[0]
                            if(data[seriesIndex])
                                this.taskSetFilter(data[seriesIndex])
                        },
                        dataPointSelection: (event, chartContext, config) => {
                            if (config.dataPointIndex !== undefined) {
                                const selectedData = this.series[config.seriesIndex].data[config.dataPointIndex]
                                if(selectedData)
                                    this.taskSetFilter(selectedData)
                            }
                        }
                    }
                },
                grid: {
                    show: true,
                    strokeDashArray: 10,
                    borderColor: '#cdd2fa'
                },
                colors: ['#1b66c1'],
                plotOptions: {
                    bar: {
                        horizontal: false,
                        borderRadius: 6,
                        distributed: true,
                        borderRadiusApplication: "end",
                        borderRadiusWhenStacked: "last",
                        columnWidth: '30%',
                        dataLabels: {
                            position: 'top'
                        }
                    }
                },
                dataLabels: {
                    offsetY: 10,
                    style: {
                        fontSize: '14px',
                        fontFamily: 'Roboto',
                        fontWeight: 400
                    }
                },
                xaxis: {
                    tickPlacement: 'between',
                    axisBorder: {
                        show: false
                    },
                    axisTicks: {
                        show: false
                    },
                    crosshairs: {
                        show: false
                    },
                    type: 'category',
                    categories: [],
                    labels: {
                        hideOverlappingLabels: false,
                        maxHeight: 120,
                        trim: false,
                        rotate: 0,
                        minWidth: 0,
                        maxWidth: 500,
                        style: {
                            colors: ['#000'],
                            fontFamily: 'Roboto',
                            fontSize: '13px'
                        },
                        formatter: function(val) {
                            return val
                        }
                    }
                },
                yaxis: {
                    labels: {
                        offsetX: -5,
                        offsetY: 4,
                        style: {
                            colors: ['#000'],
                            fontFamily: 'Roboto',
                            fontSize: '14px',
                            cssClass: 'opacity-60'
                        }
                    }
                },
                tooltip: {
                    style: {
                        fontFamily: 'Roboto'
                    },
                    marker: {
                        show: false
                    }
                }
            }
        }
    },
    created() {
        this.getStat()
    },
    methods: {
        async getStat() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/report/time_tracking/`)
                if(data?.execute_time) {
                    this.series = [{
                        name: this.$t('task.time_spent_short'),
                        data: data.execute_time.map(item => ({
                            x: `${item.last_name} ${item.first_name}`,
                            y: item.wasted_time,
                            customData: item
                        }))
                    }]
                    this.chartOptions = {
                        ...this.chartOptions,
                        xaxis: {
                            ...this.chartOptions.xaxis,
                            categories: data.execute_time.map(item => [item.last_name, item.first_name])
                        }
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.chart_wrapper{
    overflow: hidden;
    width: 100%;
    &__scroll{
        width: 100%;
        overflow-x: auto;
    }
    &::v-deep{
        .apexcharts-bar-series{
            path{
                cursor: pointer;
            }
        }
    }
}
</style>