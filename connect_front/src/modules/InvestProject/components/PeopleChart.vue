<template>
    <div class="invest_graph">
        <div class="invest_graph__left">
            <apexchart 
                type="donut" 
                :options="chartOptions" 
                class="chart"
                :width="chartSize.width"
                :height="chartSize.height"
                :series="series" />
        </div>
        <div class="invest_graph__right">
            <div>
                <div class="graph_label">
                    {{ $t('invest.amount') }}
                </div>
                <div class="graph_value">
                    {{ jobLabel(allJobs) }}
                </div>
                <div class="graph_list">
                    <div class="graph_list__item">
                        <div class="list_marker" style="background: #1c65c0;" />
                        <div>
                            <div>
                                {{ $t('invest.permanent') }}
                            </div>
                            <div>
                                {{ jobLabel(item.jobs_permanent) }}
                            </div>
                        </div>
                    </div>
                    <div class="graph_list__item">
                        <div class="list_marker" style="background: #f47c5f;" />
                        <div>
                            <div>
                                {{ $t('invest.temporary') }}
                            </div>
                            <div>
                                {{ jobLabel(item.jobs_temporary) }}
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
import { declOfNum } from '../utils.js'
export default {
    props: {
        item: {
            type: Object,
            required: true
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
                    return {
                        width: '180px',
                        height: '180px'
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
        allJobs() {
            return Number(this.item.jobs_temporary) + Number(this.item.jobs_permanent)
        }
    },
    data() {
        return {
            tab: 1,
            series: [this.item.jobs_permanent, this.item.jobs_temporary],
            chartOptions: {
                stroke: {
                    width: 0
                },
                legend: {
                    show: false
                },
                colors: [
                    '#1c65c0',
                    '#f47d60'
                ],
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
                                    formatter(value) {
                                        // eslint-disable-next-line radix
                                        return `${parseInt(value)}`
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '13px',
                                    fontWeight: 400,
                                    label: this.jobLabel(this.allJobs, false),
                                    formatter: () => this.allJobs
                                },
                            }
                        }
                    },
                },
                labels: [
                    this.$t('invest.postoyannye'), 
                    this.$t('invest.vremennye')
                ]
            }
        }
    },
    methods: {
        jobLabel(num, showCount = true) {
            if(showCount) {
                return num + ' ' + declOfNum(num,
                    [this.$t('invest.invest_mesto'), this.$t('invest.invest_mest'), this.$t('invest.invest_mest_plural')])
            } else {
                return declOfNum(num,
                    [this.$t('invest.invest_mesto'), this.$t('invest.invest_mest'), this.$t('invest.invest_mest_plural')])
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.invest_graph{
    display: grid;
    gap: 15px;
    grid-template-columns: 160px 1fr;
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
    &::v-deep{
        .chart{
            margin-left: -20px;
        }
        circle{
            fill: #f3f3f3;
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