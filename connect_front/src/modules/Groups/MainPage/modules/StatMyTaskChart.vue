<template>
    <div 
        v-if="user && this.allStat"
        class="group_stat_card">
        <h2>
            {{ $t('wgr.my_task') }}
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
        id: {
            type: [String, Number],
            required: true
        },
        is_project: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
        series() {
            return [
                this.allStat.new, 
                this.allStat.in_work, 
                this.allStat.on_pause, 
                this.allStat.on_check,
                this.allStat.on_rework,
                this.allStat.completed
            ]
        }
    },
    data() {
        return {
            allStat: null,
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
                    '#f7636f',
                    '#89c340'
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
                    this.$t('wgr.rework'),
                    this.$t('wgr.completed')
                ]
            }
        }
    },
    created() {
        this.getTask()
    },
    methods: {
        async getTask() {
            try {
                let params = {
                    parent: 'all'
                }

                if(this.is_project)
                    params['filters'] = { project: this.id, operator_id: this.user.id }
                else
                    params['filters'] = { workgroup: this.id, operator_id: this.user.id }

                const {data} = await this.$http.get('tasks/task_kanban/status_count/', {params})
                if(data) {
                    this.allStat = {
                        ...data,
                        new_percent: parseInt(((data.new / this.taskCount) * 100).toFixed(2)),
                        in_work_percent: parseInt(((data.in_work / this.taskCount) * 100).toFixed(2)),
                        on_pause_percent: parseInt(((data.on_pause / this.taskCount) * 100).toFixed(2)),
                        on_check_percent: parseInt(((data.on_check / this.taskCount) * 100).toFixed(2)),
                        on_rework_percent: parseInt(((data.on_rework / this.taskCount) * 100).toFixed(2)),
                        completed_percent: parseInt(((data.completed / this.taskCount) * 100).toFixed(2))
                    }
                }
            } catch(e) {
                console.log(e)
                this.loading = false
            } finally {
                this.loading = false
            }
        }
    }
}
</script>