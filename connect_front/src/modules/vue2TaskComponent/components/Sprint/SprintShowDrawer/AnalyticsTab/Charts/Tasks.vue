<template>
    <div class="flex items-center justify-center flex-wrap">
        <div class="chart-wrapper flex items-center justify-center">
            <apexchart 
                type="donut" 
                :options="chartOptions" 
                :series="series" />
        </div>
        <div>
            <div 
                v-for="status in statistics" 
                :key="status.color" 
                class="flex items-center whitespace-nowrap text-base my-1">
                <a-badge :color="status.color" />
                {{ status.name }} - {{ status.value }}
            </div>
        </div>
    </div>
</template>

<script>
import VueApexCharts from 'vue-apexcharts'
const ANT_COLORS = {
    red: '#F5222D',
    volcano: '#FA541C',
    orange: '#FA8C16',
    gold: '#FAAD14',
    yellow: '#FADB14',
    lime: '#A0D911',
    green: '#52C41A',
    cyan: '#13C2C2',
    blue: '#1890FF',
    geekblue: '#2F54EB',
    purple: '#722ED1',
    magenta: '#EB2F96',
    grey: '#666666',
}

export default {
    components: {
        apexchart: VueApexCharts
    },
    props: {
        sprint: {
            type: Object,
            required: true
        }
    },
    computed: {
        statistics() {
            return [
                {
                    name: this.$t('task.new'),
                    value: this.sprint.new_task_count,
                    color: ANT_COLORS.blue
                },
                {
                    name: this.$t('task.in_work'),
                    value: this.sprint.in_work_task_count,
                    color: ANT_COLORS.orange
                },
                {
                    name: this.$t('task.completed'),
                    value: this.sprint.completed_task_count,
                    color: ANT_COLORS.green
                },
                {
                    name: this.$t('task.overdue'),
                    value: this.sprint.overdue_task_count,
                    color: ANT_COLORS.red
                }
            ]
        },
        labels() {
            return this.statistics.map(item => item.name)
        },
        colors() {
            return this.statistics.map(item => item.color)
        },
        series() {
            return this.statistics.map(item => item.value)
        },
        chartOptions() {
            return{
                chart: {
                    type: 'donut'
                },
                stroke:{
                    colors: "#FAFAFA",
                    width: 2
                },
                legend: {
                    show: false
                },
                dataLabels: {
                    enabled: false,
                },
                plotOptions: {
                    expandOnClick:false,
                    pie: {
                        customScale: 1,
                        borderRadius: 10,
                        donut: {
                            size:'88%',
                            background: 'transparent',
                            labels: {
                                show: true,
                                name: {
                                    fontSize: '16px',
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    offsetY: 25
                                },
                                value: {
                                    show: true,
                                    fontSize: '36px',
                                    fontWeight: 300,
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    offsetY: -15,
                                    formatter: (value) => {
                                        return value
                                    },
                                },
                                total: {
                                    show: true,
                                    fontSize: '16px',
                                    fontWeight: 400,
                                    color: '#000',
                                    fontFamily: 'Roboto',
                                    label: this.$t('task.total_tasks'),
                                    formatter: () => this.sprint.task_count
                                }
                            }
                        }
                    },
                },
                colors: this.colors,
                labels: this.labels
            }
        }
    },
    data() {
        return {
            
        }
    }
}
</script>

<style lang="scss" scoped>
.chart-wrapper {
    width: 180px;
    height: 180px;
    min-width: 180px;
    min-height: 180px;
}
</style>