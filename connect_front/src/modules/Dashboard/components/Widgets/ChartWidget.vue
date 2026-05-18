<template>
    <WidgetWrapper 
        :widget="widget"
        ref="widgetWrapper"
        v-element-size="onResize"
        :class="isMobile && 'mobile_widget'">
        <div class="scroll">
            <template v-if="analyticsLoading">
                <a-spin class="custom_spinner"/>
            </template>
            <div 
                class="flex custom_opacity_transition"
                :class="analyticsLoading && 'custom_opacity'">
                <div class="flex min-w-0 border shrink-0 rounded-lg p-2 pl-4">
                    <div>
                        <div 
                            class="mb-2"
                            :class="'flex-wrap'">
                            <AnalyticsFilters
                                @updateFilters="getAnalyticReports"
                                currentMonth
                                :filters="filters" />
                        </div>
                        <div class="mb-4">
                            <div class="text-base">
                                {{ $t('dashboard.totalAppeals') }}
                            </div> 
                            <div class="text-4xl font-semibold">
                                {{ appealsTotal }}
                            </div>
                        </div>
                        <div class="flex flex-grow">
                            <div class="mr-6">
                                <PercentageList 
                                    fullWidth
                                    :analytics="appealsAnalytics" 
                                    :colors="colors"  />
                            </div>
                        </div>
                    </div>
                    <template v-if="widgetWidth >= 1000">
                        <div class="flex items-center">
                            <Chart
                                :analytics="appealsAnalytics"/>
                        </div>
                    </template>
                    
                </div>
                <div class="ml-2">
                    <div 
                        class="mb-2 p-3 rounded-md custom_bg custom_bg_green text-white"
                        @click="openModalByRef('statisticsModalSources')">
                        <div class="flex justify-between">
                            <div class="mr-2 flex flex-col justify-between">
                                <div class="text-sm font-medium">
                                    {{ $t('dashboard.entranceSources') }}
                                </div>
                                <div class="font-semibold text-2xl">
                                    {{ entranceSourceTotal }}
                                </div>
                            </div>
                            <a-progress 
                                class="custom_progress"
                                type="circle" 
                                strokeColor="#fff"
                                :strokeWidth="14"
                                :format="percent => percent.toFixed(1) + '%'"
                                :percent="entranceSourceTotal/appealsTotal*100" 
                                :width="70" />
                        </div>
                    </div>
                    <div 
                        class="mb-2 p-3 rounded-md custom_bg custom_bg_blue text-white"
                        @click="openModalByRef('statisticsModalTotal')">
                        <div class="flex justify-between">
                            <div class="mr-2 flex flex-col justify-between">
                                <div class="text-sm font-medium">
                                    {{ $t('dashboard.GOReviewed') }}
                                </div>
                                <div class="font-semibold text-2xl">
                                    {{ GOReviewedTotal }}
                                </div>
                            </div>
                            <a-progress 
                                class="custom_progress"
                                type="circle" 
                                strokeColor="#fff"
                                :strokeWidth="14"
                                :format="percent => percent.toFixed(1) + '%'"
                                :percent="GOReviewedTotal/appealsTotal*100" 
                                :width="70" />
                        </div>
                    </div>

                    <div class="p-3 rounded-md custom_bg_red text-white">
                        <div class="flex justify-between">
                            <div class="mr-2 flex flex-col justify-between">
                                <div class="text-sm font-medium">
                                    {{ $t('dashboard.deadlineViolation') }}
                                </div>
                                <div class="font-semibold text-2xl">
                                    {{ deadlineViolationTotal }}
                                </div>
                            </div>
                            <a-progress 
                                class="custom_progress"
                                type="circle" 
                                :percent="deadlineViolationTotal/appealsTotal*100" 
                                :format="percent => percent.toFixed(1) + '%'"
                                :strokeWidth="14"
                                strokeColor="#fff"
                                :width="70" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <StatisticsModalTotal 
            ref="statisticsModalTotal"
            :getAnalyticReports="getAnalyticReports"
            :analytics="GOReviewedAnalytics"
            :loading="analyticsLoading"
            :filters="filters"/>
        <StatisticsModalSources 
            ref="statisticsModalSources"
            :getAnalyticReports="getAnalyticReports"
            :analytics="entranceSourceAnalytics"
            :loading="analyticsLoading"
            :filters="filters"/>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { vElementSize } from '@vueuse/components'

export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },

    directives: {
        ElementSize: vElementSize
    },
    components: {
        AnalyticsFilters: () => import('../Analytics/AnalyticsFilters.vue'),
        PercentageList: () => import('../Analytics/PercentageList.vue'),
        StatisticsModalTotal: () => import('../Analytics/StatisticsModalTotal.vue'),
        StatisticsModalSources: () => import('../Analytics/StatisticsModalSources.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        Chart: () => import('../Chart.vue')
    },
    data() {
        return {
            analyticsLoading: false,
            filters: {
                selects: [
                    {
                        id: 'parent',
                        value: [],
                        loading: false,
                        options: {
                            list: [],
                            page: 0,
                            next: true
                        }
                    },
                    {
                        id: 'displayed',
                        value: [],
                        loading: false,
                        options: {
                            list: [],
                            page: 0,
                            next: true
                        }
                    }
                ],
                dateRange: {
                    start: null,
                    end: null,
                    format: 'YYYY-MM-DD'
                }
            },
            series: [252, 20, 15, 300],
            legend: [this.$t('dashboard.applications'), this.$t('dashboard.complaints'), this.$t('dashboard.suggestions'), this.$t('dashboard.others')],
            colors: [
                '#067fd8',
                '#fa9800',
                '#9641e5',
                '#d341ee',
                '#00aeab',
                '#c2d88e',
                '#f7636f'
            ],
            windowWidth: 0,
            widgetWidth: 0,
            analyticReports: [],
        }
    },
    computed: {
        defaultDateRange() {
            return {
                start: this.$moment(new Date())
                    .subtract(1, 'months').startOf('month').format(this.filters.dateRange.format),
                end: this.$moment(new Date())
                    .subtract(1, 'months').endOf('month').format(this.filters.dateRange.format),
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        related_object() {
            return this.widget.random_settings?.related_object?.id || null
        },
        //
        deadlineViolationAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.deadlineViolationAnalytics'));
        },
        deadlineViolationTotal() {
            return this.getTotal(this.$t('dashboard.deadlineViolationTotal'));
        },
        GOReviewedAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.GOReviewedAnalytics'));
        },
        GOReviewedTotal() {
            return this.getTotal(this.$t('dashboard.GOReviewedTotal'));
        },
        entranceSourceAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.entranceSourceAnalytics'));
        },
        entranceSourceTotal() {
            return this.getTotal(this.$t('dashboard.entranceSourceTotal'));
        },
        appealsAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.appealsAnalytics'));
        },
        appealsTotal() {
            return this.getTotal(this.$t('dashboard.appealsTotal'));
        },

        chartData() {
            return {
                series: this.getSeries(this.appealsAnalytics),
                labels: this.getLabels(this.appealsAnalytics),
            }
        }
    },
    mounted() {
        if(this.$refs.widgetWrapper) {
            this.widgetWidth = this.$refs.widgetWrapper.$el.clientWidth
        }
    },
    methods: {
        async getReportForms() {
            const parentSelect = this.filters.selects.find(selectItem => selectItem.id === 'parent')
            const reportFormsURL = `consolidation/report_forms?org_administrator=${parentSelect.value}`
            const { data } = await this.$http(reportFormsURL)
            return data.results
        },
        async getAnalyticsReports(reportFormId) {
            const analyticsReportsURL = `consolidation/analytic_reports?report_form=${reportFormId}`
            const { data } = await this.$http(analyticsReportsURL)
            return data.map(report => { 
                return {
                    analytics: [],
                    ...report
                }
            })  
        },
        async getAnalyticReports() {
            this.analyticsLoading = true;
            const reportForms = await this.getReportForms();
            if (!reportForms?.length) {
                console.log(this.$t('dashboard.noReportForms'));
                this.analyticReports = [];
                setTimeout(() => { this.analyticsLoading = false }, 1000);
        
                return 0;
            }
            const formCode = 'f2go';
            const foundIndex = reportForms.findIndex(form => form.code === formCode);
            if (foundIndex !== -1) {
                const reportFormId = reportForms[foundIndex].id;
                this.analyticReports = await this.getAnalyticsReports(reportFormId);
                this.analyticReports.forEach(async analyticReport => {
                    this.getAnalytics(analyticReport.id);
                });
            } else {
                console.log(this.$t('dashboard.noFormF2GO'));
                this.analyticReports = [];
            }
            setTimeout(() => { this.analyticsLoading = false }, 1000);
        },
        // TODO: REFACTORING
        async getAnalytics(analyticReportId) {
            const parentSelect = this.filters.selects.find(selectItem => selectItem.id === 'parent')
            const displaySelect = this.filters.selects.find(selectItem => selectItem.id === 'displayed')

            const parent = JSON.parse(JSON.stringify(parentSelect.value))
            const display = JSON.parse(JSON.stringify(displaySelect.value))
                
            const start = this.$moment(this.filters.dateRange.start)
                .startOf('month').format(this.filters.dateRange.format)
            const end = this.$moment(this.filters.dateRange.end)
                .endOf('month').format(this.filters.dateRange.format)

            const params = {
                organizations: parent ? [parent] : null,
                start: start || this.defaultDateRange.start,
                end: end || this.defaultDateRange.end,
                analytic_report: analyticReportId,
                display: display,
            }
            if(display === 'self') {
                delete params.display
            }
            const analyticsURL = `consolidation/${parent}/analytics/`
            const analyticsResponse = await this.$http.get(analyticsURL, { params })
            if(!analyticsResponse.data?.length) {
                return 0
            }
            const foundIndex = this.analyticReports.findIndex(report => report.id === analyticReportId)
            this.analyticReports[foundIndex].analytics = analyticsResponse.data
        },
        onResize({ width, height }) {
            this.widgetWidth = width
        },
        openModalByRef(ref) {
            this.$refs[ref].openModal()
        },
        openSetting() {
            eventBus.$emit('openSetting', this.widget)
        },
        getPercent(part) {
            return Number((part/this.totalAppeals*100).toFixed(0))
        },
        getExistingReport(reportName) {
            const foundIndex = this.analyticReports.findIndex(report => report.name === reportName)
            return this.analyticReports?.[foundIndex] || null
        },
        getExistingAnalytics(reportName) {
            const report = this.getExistingReport(reportName)
            if(report?.analytics?.length)
                return report.analytics
            return []
        },
        getTotal(reportName) {
            const analytics = this.getExistingAnalytics(reportName)
            if(analytics?.length)
                return analytics?.[0]?.value
                // return analytics.reduce((total, current) => total + current.value, 0) || 0
            return 0
        },
        getAnalyticsList(reportName) { 
            const analytics = this.getExistingAnalytics(reportName)
            if(analytics?.length)
                return JSON.parse(JSON.stringify(analytics))?.splice(1)
                // return analytics.reduce((total, current) => total + current.value, 0) || 0
            return []
        },
        getLabels(analytics) {
            return analytics.map(analyticsItem => analyticsItem.name)
        },
        getSeries(analytics) {
            return analytics.map(analyticsItem => analyticsItem.value)
        },
    }
}
</script>

<style lang="scss" scoped>
.custom_spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.custom_opacity_transition {
    transition: opacity 0.3s ease,
}
.custom_opacity {
    opacity: 0.4;
}
.scroll{
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}
.mobile_widget{
    .scroll{
        height: 350px;
    }
}
.comment_empty{
    text-align: center;
    padding-top: 20px;
    i{
        font-size: 42px;
        color: var(--gray);
    }
    p{
        margin-top: 15px;
        margin-bottom: 20px;
        max-width: 280px;
        margin-left: auto;
        margin-right: auto;
    }
}
.shrink-0 {
    flex-shrink: 0;
}
.custom_progress::v-deep {
    .ant-progress-circle-trail {
        stroke: #fff6 !important;
    }
    .ant-progress-text {
        color: #fff;
    }
}
.custom_bg_red {
    background-color: #ff6f6f;
}
.custom_bg_green {
    background-color: #00b800;
}
.custom_bg_blue {
    background-color: #017ddd;   
}
.custom_bg {
    cursor: pointer;
    transition: opacity 0.3s ease;
    &:hover {
        opacity: 0.8;
    }
}
.statistics_grid {
    border-bottom: 1px solid #ebebeb;
    display: grid;
    grid-template-columns: 1fr 60px 40px;
    &:last-child {
        border-bottom: none;
    }
}

</style>

<!-- Убрать нули, пожирнее цифры на полар арея и меньше размер -->