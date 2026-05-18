<template>
    <div class="analytics_table">
        <div class="pb-4 flex items-center">
            <PageFilter 
                :key="page_name"
                size="large"
                :model="model"
                :page_name="page_name" />
            <ExcelBtn
                :page_name="page_name"
                :queryParams="queryParams"
                :requestData="requestData"
                :orderQuery="orderQuery"
                class="ml-2" />
            <SettingsButton
                :pageName="page_name"
                class="ml-2" />
        </div>
        <UniversalTable 
            :model="model"
            :pageName="page_name"
            tableType="analytics"
            autoHeight
            :openHandler="openTask"
            :params="queryParams"
            :endpoint="endpoint"            
            :openModalStat="openModalStat"
            :openDescModal="openDescModal" />

        <a-modal
            :title="$t('task.task_desc')"
            :zIndex="5000"
            :visible="descVisible"
            @cancel="descVisible = false">
            <div class="break-words">
                {{ desc }}
            </div>
            <template slot="footer">
                <a-button @click="descVisible = false">
                    {{ $t('task.close') }}
                </a-button>
            </template>
        </a-modal>

        <a-modal
            :title="$t('task.task_stat')"
            :zIndex="5000"
            :visible="visible"
            :afterClose="afterClose"
            @cancel="visible = false">
            <div class="modal_stat">
                <template v-if="!dataBudget && !difficultyData">
                    <a-result :title="$t('task.stat_not_found')">
                        <template #icon>
                            <a-icon 
                                type="pie-chart" 
                                theme="twoTone" />
                        </template>
                    </a-result>
                </template>
                <div 
                    v-if="statData && statData.length" 
                    class="stat_wrapper">
                    <h4>{{ $t('task.general_estimate') }}</h4>
                    <div class="w-full flex justify-center">
                        <div style="max-width: 250px;">
                            <apexchart 
                                type="pie" 
                                :options="chartOptions" 
                                :series="series" />
                        </div>
                    </div>
                    <div class="list">
                        <div class="item flex items-center justify-between">
                            <span class="flex items-center">
                                <a-badge 
                                    color="purple"
                                    class="ml-2" />
                                {{ $t('task.total_sum') }}
                            </span>
                            <span class="text-sm font-semibold pl-2">
                                {{ priceFormat(dataBudget.total_sum) }} {{ currency }}
                            </span>
                        </div>
                        <template>
                            <div 
                                v-for="item in statData" 
                                :key="item.amount_sum.id"
                                class="item flex items-center justify-between">
                                <span class="flex items-center">
                                    <a-badge 
                                        :color="item.color"
                                        class="ml-2" />
                                    {{ item.label }}:
                                </span>
                                <span class="pl-2">
                                    {{ item.amount_sum }} {{ currency }}
                                </span>
                            </div>
                        </template>
                    </div>
                </div>
                <div 
                    v-if="difStatData && difStatData.length" 
                    class="stat_wrapper">
                    <h4>{{ $t('task.difficulty_rating') }}</h4>
                    <div 
                        class="w-full flex justify-center mt-2">
                        <div style="max-width: 250px;">
                            <apexchart 
                                type="donut" 
                                :options="difChartOptions" 
                                :series="difSeries" />
                        </div>
                    </div>
                    <div class="list">
                        <div class="item flex items-center justify-between">
                            <span class="flex items-center">
                                <a-badge 
                                    color="purple"
                                    class="ml-2" />
                                {{$t('task.overall_rating')}}
                            </span>
                            <span class="text-sm font-semibold pl-2">
                                {{ difficultyData.total_avg }}
                            </span>
                        </div>
                        <template>
                            <div 
                                v-for="item in difStatData"
                                :key="item.criterion.id"
                                class="item flex items-center justify-between">
                                <span class="flex items-center">
                                    <a-badge 
                                        :color="item.color"
                                        class="ml-2" />
                                    {{ item.label }}:
                                </span>
                                <span>
                                    {{ item.score_avg }}
                                </span>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
            <template slot="footer">
                <a-button @click="visible = false">
                    {{ $t('task.close') }}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { priceFormatter } from '@/utils'
import eventBus from '@/utils/eventBus'
import VueApexCharts from 'vue-apexcharts'
import { mapActions, mapState } from 'vuex'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        apexchart: VueApexCharts,
        ExcelBtn: () => import('./ExcelBtn.vue')
    },
    props: {
        obj: {
            type: [String, Number],
            default: () => null
        },
        pageSize: {
            type: Number,
            default: 30
        },
        page_name: {
            type: [String, Number],
            default: 'analytics_table'
        },
        model: {
            type: String,
            default: 'tasks.TaskModel'
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        requestData: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            tablesInfo: state => state.table.tablesInfo
        }),
        endpoint() {
            return `/tasks/analytics/`
        },
        dataBudget() {
            if(this.budgetStat?.total_sum)
                return this.budgetStat
            else
                return null
        },
        difficultyData() {
            if(this.difficultyStat?.total_avg)
                return this.difficultyStat
            else
                return null
        },
        currency() {
            if(this.dataBudget?.currency)
                return this.dataBudget.currency.icon
            return ''
        },
        statData() {
            if(this.budgetStat?.detail_sum?.length)
                return this.budgetStat.detail_sum.map((item, index) => {
                    return {
                        ...item,
                        label: item.cost_item.name,
                        percent: item.amount_sum / this.dataBudget.total_sum * 100,
                        color: this.chartColor(index)
                    }
                })
            return []
        },
        difStatData() {
            if(this.difficultyStat?.detail_avg?.length)
                return this.difficultyStat.detail_avg.map((item, index) => {
                    return {
                        ...item,
                        label: item.criterion.name,
                        color: this.chartColor(index)
                    }
                })
            return []
        },
        series() {
            return this.statData.map(item => item.percent)
        },
        difSeries() {
            return this.difStatData.map(item => item.score_avg)
        },
        difChartOptions() {
            return {
                colors: this.difStatData.map(item => item.color),
                chart: {
                    type: 'pie'
                },
                legend: {
                    show: false
                },
                labels: this.difStatData.map(item => item.label),
                markers: {
                    colors: ['#F44336', '#E91E63', '#9C27B0']
                }
            }
        },
        chartOptions() {
            return {
                colors: this.statData.map(item => item.color),
                chart: {
                    type: 'pie'
                },
                legend: {
                    show: false
                },
                labels: this.statData.map(item => item.label),
                markers: {
                    colors: ['#F44336', '#E91E63', '#9C27B0']
                }
            }
        },
    },
    data() {
        return {
            openStat: null,
            visible: false,
            taskLoading: false,
            budgetStat: null,
            difficultyStat: null,
            orderQuery: null,
            desc: '',
            descVisible: false,
            data: [],
        }
    },
    methods: {
        openDescModal(record) {
            this.desc = record.description ? record.description : ''
            this.descVisible = true
        },
        currencyTable(item) {
            return item.budget?.currency?.icon ? item.budget.currency.icon : ''
        },
        afterClose() {
            this.openStat = null
            this.budgetStat = null
            this.difficultyStat = null
        },
        async openModalStat(id) {
            try {
                this.taskLoading = true
                this.openStat = id
                this.visible = true
                const { data } = await this.$http('/tasks/budget/aggregate/', {
                    params: {
                        obj: id
                    }
                })
                if(data) {
                    this.budgetStat = data
                }

                const res = await this.$http('/tasks/difficulty/aggregate/', {
                    params: {
                        obj: id
                    }
                })

                if(res?.data) {
                    this.difficultyStat = res.data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.taskLoading = false
            }
        },
        openTask(id) {
            let query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== id || !query.task) {
                query.task = id
                this.$router.push({query})
            }
        },
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        chartColor(index) {
            switch (index) {
            case 0:
                return '#80c6ff'
                break;
            case 1:
                return '#c2d88e'
                break;
            case 2:
                return '#ca97ca'
                break;
            case 3:
                return '#ffc618'
                break;
            case 4:
                return '#88c240'
                break;
            case 5:
                return '#008ffb'
                break;
            default:
                return '#816bf8'
            }
        }
    },
}
</script>

<style lang="scss" scoped>
.analytics_table{
    .name{
        cursor: pointer;
        word-break: break-word;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }
}
.modal_stat{
    .stat_wrapper{
        &:not(:last-child){
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border2);
            padding-bottom: 10px;
        }
        h4{
            font-weight: 600;
            margin-bottom: 5px;
        }
    }
}
</style>