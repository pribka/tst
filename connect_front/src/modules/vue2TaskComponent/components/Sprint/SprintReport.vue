<template>
    <div class="report_content body_wrap">
        <div 
            v-if="isMobile"
            class="completed_tag_mobile">
            <a-tag 
                color="green">
                {{ $t('task.sprint_completed') }}
            </a-tag>
        </div>
        <div 
            class="flex justify-between"
            :class="[column && 'flex-col', isMobile && 'flex-col mt-2']">
            <div>
                <a-table
                    v-if="!isMobile"
                    :columns="columns" 
                    :data-source="tableTasks" 
                    :scroll="scroll"
                    size="small"
                    :pagination="false"
                    :row-key="record => record.id">
                    <div slot="id" slot-scope="text, record">
                        <span
                            class="cursor-pointer"
                            @click="openTask(record)">
                            {{ record.counter }}
                        </span>
               
                    </div>
                    <template 
                        slot="name" 
                        slot-scope="text, record">
                        <a 
                            @click="openTask(record)" 
                            class="table_name">
                            {{text}}
                        </a>
                    </template>
                    <template slot="operator" slot-scope="text, record">
                        <Operator :item="text" :record="record"/>
                    </template>
                    <template slot="wasted_time" slot-scope="text">
                        {{text ? text : 0}} {{ $t('task.hours') }}
                    </template>

                    <template slot="completed" slot-scope="text, record">
                        <a-tooltip :title="$t('task.completed')" destroyTooltipOnHide v-if="record.completed">
                            <a-icon  type="check-circle" />
                        </a-tooltip>
                        <a-tooltip v-else :title="$t('task.returned')" destroyTooltipOnHide> 
                            <a-icon  type="close-circle" />
                        </a-tooltip>
                        
                    </template>
                </a-table>
                <div
                    v-if="isMobile"
                    class="reposrt_task_list">
                    <a-card
                        v-for="task in tableTasks"
                        :key="task.id"
                        class="report_task_mobile">
                        <div 
                            class="flex justify-between"
                            @click="openTask(task)">
                            <div class="flex">
                                <span class="mr-2">{{ task.counter }}</span>
                                <span>{{ task.name }}</span>
                            </div>
                            <div>
                                <Operator 
                                    :item="task.operator" 
                                    :record="task"
                                    :showUserName="false"/>
                            </div>
                        </div>
                        <div class="flex justify-between mt-2 font-semibold">
                            <div>
                                {{ $t('task.hours_spent') }}
                            </div>
                        </div>
                        <div class="flex justify-between">
                            <div>
                                {{task.wasted_time || 0}} {{ $t('task.hours') }}
                            </div>
                            <div>
                                <a-tooltip :title="$t('task.completed')" destroyTooltipOnHide v-if="task.completed">
                                    <a-icon  type="check-circle" />
                                </a-tooltip>
                                <a-tooltip v-else destroyTooltipOnHide :title="$t('task.returned')" > 
                                    <a-icon  type="close-circle" />
                                </a-tooltip>
                            </div>
                        </div>
                    </a-card>
                </div>

                <div 
                    class="grid mt-1 gap-2"
                    :class="isMobile ? 'grid-cols-1' : 'grid-cols-3'">
                    <a-card class="w-full" hoverable>
                        {{ $t('task.completed') }}: {{data.completed_task_count	}}
                    </a-card>
                    <a-card class="w-full" hoverable>
                        {{ $t('task.returned_to_list') }}: {{data.uncompleted_task_count	}}
                    </a-card>
                    <a-card 
                        v-if="data.total_time" 
                        class="w-full" 
                        hoverable>
                        {{ $t('task.time_spent') }}: {{data.total_time  || 0	}} {{ $t('task.hours') }}
                    </a-card>
                    <a-card 
                        v-if="dataBudget" 
                        class="w-full" 
                        hoverable>
                        {{ $t('task.general_estimate') }}: {{ priceFormat(dataBudget.total_sum) }} <template v-if="currency">{{ currency }}</template>
                    </a-card>
                    <a-card 
                        v-if="dataDifficulty" 
                        class="w-full" 
                        hoverable>
                        {{ $t('task.difficulty_assessment') }}: {{ dataDifficulty.total_avg }}
                    </a-card>

                </div>
                <div 
                    v-if="!isMobile" 
                    class="report_comments">
                    <Comments 
                        class="mt-4"
                        :allowComments="isAuthor"
                        v-if="!hideComment"
                        model="sprint"
                        :previewMode="true"
                        :related_object="data.id" 
                        :extendDrawerZIndex="1010" />
                </div>
            </div>
            <div 
                class="w-full justify-between"
                :class="[column && 'mt-4', isMobile ? 'mt-6' : 'ml-2 ']">
                <export-excel
                    v-if="!column"
                    class="excel_export_btn mb-4"
                    :fields="excelFields"
                    :footer="excelFooter"
                    :worksheet="$t('task.sprint_report')"
                    :fetch="beforeGenerate"
                    :name="`${$t('task.report')} ${data.name} ${$t('task.from')} ${$moment().format('DD.MM.YYYY')}.xls`">
                    <a-button 
                        type="primary" 
                        :loading="excelLoading">
                        {{ $t('task.excel_download') }}
                    </a-button>
                </export-excel>

                <!-- deadline  -->
                <div 
                    class="flex tag-deadline justify-between w-full" 
                    :class="(!column && !isMobile) && 'ml-2'">
                    <div>
                        {{ $t('task.start') }}:
                        {{$moment(data.begin_date).format('D MMMM, HH:mm')}}
                    </div>
                   
                    <div>
                        {{ $t('task.end') }}:
                        {{$moment(data.finished_date).format('D MMMM, HH:mm')}}
                    </div>
                </div>
               
                <!-- charts -->
                <apexchart
                    v-if="data.execute_time.length > 0"
                    class="mt-4"
                    type="polarArea"
                    height="300"
                    width="100%"
                    :options="chartOptionsTime"
                    :series="seriesTime" />

                <apexchart
                    class="mt-4"
                    type="bar"
                    height="300"
                    width="100%"
                    :options="chartOptionsTasks"
                    :series="seriesTasks" />

                <SprintBudget 
                    :task="data"
                    :stat="{key: 'budget'}" />
                <SprintDifficulty 
                    :task="data"
                    :stat="{key: 'difficulty'}" />
            </div>
            
            <div v-if="isMobile" class="report_comments">
                <Comments 
                    class="mt-4 pl-4 pr-4 w-1/2"
                    :allowComments="isAuthor"
                    v-if="!hideComment"
                    model="sprint"
                    :previewMode="true"
                    :related_object="data.id" 
                    :extendDrawerZIndex="1010" />
            </div>
        </div>
    </div>  
</template>

<script>
import { mapState } from 'vuex'
import Operator from "../Operator.vue"
import VueApexCharts from 'vue-apexcharts'
import Comments from '@apps/vue2CommentsComponent'
import SprintBudget from './SprintBudget.vue'
import SprintDifficulty from './SprintDifficulty.vue'
import { priceFormatter } from '@/utils'
import excel from 'vue-excel-export'
export default {
    components: {
        Operator,
        apexchart: VueApexCharts,
        Comments,
        SprintBudget,
        SprintDifficulty,
        'export-excel': excel,
    },
    props: {
        data: Object,
        column: {
            type: Boolean,
            default: false,
        },
        hideComment : {
            type: Boolean,
            default: false,
        }
    },
    data(){
        return {
            tableTasks: this.data.tasks,
            excelLoading: false,
            tasks: this.data.tasks,
            excelFields: {
                [this.$t('task.task_number')] : 'counter', 
                [this.$t('task.name')]: 'name',
                [this.$t('task.completed_returned')]: 'completed',
                [this.$t('task.operator')]: 'operator',
                [this.$t('task.hours_spent')]: 'wasted_time',
                [this.$t('task.general_estimate')]: 'budget',
                [this.$t('task.difficulty_assessment')]: 'difficulty'
            },
            columns: [
                {
                    title: '#',
                    dataIndex: 'id',
                    key: 'id',
                    scopedSlots: { customRender: 'id' },
                    width: 80,
                  
                },
                {
                    title: this.$t('task.name'),
                    dataIndex: 'name',
                    key: 'name',
                    scopedSlots: { customRender: 'name' },
                    width: 200,
                },

                {
                    title: this.$t('task.operator'),
                    dataIndex: 'operator',
                    key: 'operator',
                    scopedSlots: { customRender: 'operator' }
                },
                {
                    title: this.$t('task.hours_spent'),
                    dataIndex: 'wasted_time',
                    key: 'wasted_time',
                    scopedSlots: { customRender: 'wasted_time' }
                
                },
                {
                    title: this.$t('task.completed_returned'),
                    dataIndex: 'completed',
                    key: 'completed',
                    scopedSlots: { customRender: 'completed' }
                
                },

            ],
            chartOptionsTasks: {
                plotOptions: {
                    bar: {
                        horizontal: false,
                        columnWidth: '35%',
                        endingShape: 'rounded'
                    },
                },
                dataLabels: {
                    enabled: false
                },
                title: {
                    text: this.$t('task.completed_tasks_count')
                },
                stroke: {
                    show: true,
                    width: 5,
                    colors: ['transparent']
                },
                xaxis: {
                    categories: this.data.operator_list.map(el => el.last_name + ' ' + el.first_name),
                },
               
                
                fill: {
                    opacity: 1
                },
            },
            chartOptionsTime: {
                stroke: {
                    colors: ['#fff']
                },
                fill: {
                    opacity: 0.8
                },
                title: {
                    text: this.$t('task.task_time')
                },
                plotOptions: {
                    polarArea: {
                        rings: {
                            strokeWidth: 1
                        },
                        spokes: {
                            strokeWidth: 2
                        },
                    }
                },
                yaxis: {
                    labels: {
                        formatter: function (value) {
                            return value.toFixed(2) 
                        }
                    },
                },
               
                responsive: [{
                    breakpoint: 480,
                    options: {
                        chart: {
                            width: 200
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }],
                tooltip: {
                    y: {
                        formatter: (val) => {
                            return   val + " " + this.$t('task.hours')
                        }
                    }
                },
              
                labels: this.data.execute_time.map(el => el.last_name + ' ' + el.first_name)

        
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            user: state => state.user.user
        }),
        getBudgetStat() {
            if(this.$store.getters['task/getAsideStat'](this.data.id, 'budget'))
                return this.$store.getters['task/getAsideStat'](this.data.id, 'budget')
            else
                return null
        },
        dataBudget() {
            if(this.getBudgetStat?.total_sum)
                return this.getBudgetStat
            else
                return null
        },
        currency() {
            if(this.dataBudget.currency)
                return this.dataBudget.currency.icon
            else
                return ''
        },
        getDifficultyStat() {
            if(this.$store.getters['task/getAsideStat'](this.data.id, 'difficulty'))
                return this.$store.getters['task/getAsideStat'](this.data.id, 'difficulty')
            else
                return null
        },
        dataDifficulty() {
            if(this.getDifficultyStat?.total_avg)
                return this.getDifficultyStat
            else
                return null
        },
        excelFooter() {
            let footer = []
            if(this.getBudgetStat) {
                footer[0] = `${this.$t('task.general_estimate')}: ${this.priceFormat(this.getBudgetStat.total_sum)} ${this.getBudgetStat?.currency?.icon && this.getBudgetStat.currency.icon}` 
            }
            if(this.getDifficultyStat) {
                let index = 0
                if(footer[0]?.length)
                    index = 1
                footer[index] = `${this.$t('task.difficulty_assessment')}: ${this.getDifficultyStat.total_avg}` 
            }

            return footer
        },
        isAuthor(){
            return this.user.id === this.data.author.id
        },
        loading(){
            return !!this.data.id
        },
        tableScroll() {
          
            return 750
        },
        scroll() {
            return {
                x: this.tableScroll,
                y: 'calc(100vh - 330px)'
            }
        },
        excelData() {
            return this.tasks.map(el => {
                return {
                    counter: el.counter,
                    name: el.name,
                    completed: el.completed ? this.$t('task.completed'): this.$t('task.returned'),
                    operator: el.operator.last_name + ' ' + el.operator.first_name,
                    wasted_time: el.wasted_time,
                    budget: el.budget ? el.budget : '',
                    difficulty: el.difficulty ? el.difficulty : ''
                }
            })
        },
        seriesTime(){
            return this.data.execute_time.map(el => el.wasted_time)
        },
        seriesTasks(){
            let res = this.data.operator_list.map(el=> {
                return {
                    data: [  el.completed_task_count],
                    name: el.last_name + ' ' + el.first_name
                }
            })

            // return [{
            //     name: this.data.operator_list.map(el => el.last_name + ' ' + el.first_name),
            //     data:  this.data.operator_list.map(el => el.completed_task_count)}]
            return res
        },
        isMobile() {
            return this.$store.state.isMobile
        }
       
    },
   
    methods:{
        async beforeGenerate() {
            try {
                this.excelLoading = true
                const data = this.tasks
                for (let key in data) {
                    const budget = await this.$http.get(`/tasks/budget/aggregate/`, {
                        params: {
                            obj: data[key].id
                        }
                    })
                    const difficulty = await this.$http.get(`/tasks/difficulty/aggregate/`, {
                        params: {
                            obj: data[key].id
                        }
                    })

                    this.tasks[key].budget = budget.data?.total_sum ? `${this.priceFormat(budget.data.total_sum)} ${budget.data?.currency?.icon && budget.data.currency.icon}` : ''
                    this.tasks[key].difficulty = difficulty.data?.total_avg ? difficulty.data.total_avg : ''
                }

                return this.tasks.map(el => {
                    return {
                        counter: el.counter,
                        name: el.name,
                        completed: el.completed ? this.$t('task.completed'): this.$t('task.returned'),
                        operator: el.operator.last_name + ' ' + el.operator.first_name,
                        wasted_time: el.wasted_time,
                        budget: el.budget ? el.budget : '',
                        difficulty: el.difficulty ? el.difficulty : ''
                    }
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.excelLoading = false
            }
        },
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        openTask(record){
            let query = Object.assign({}, this.$route.query)
            query.task = record.id
            if(!this.$route.query.task)
                this.$router.push({query})
        }
        
    },
    
}
</script>

<style lang="scss">
.report_content{
    .table_name{
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
    }
}
.report_task_mobile {
    &:not(:last-child) {
        margin-bottom: 8px;
    }
}
.tag-deadline{
    .ant-tag{
        text-align: center;
        padding: 10px 0;
        font-size: 15px;
    }
}
</style>

<style lang="scss" scoped>

.completed_tag_mobile {
    display: flex;
    justify-content: flex-end;
    .ant-tag {
        margin-right: 0;
    }
}

</style>