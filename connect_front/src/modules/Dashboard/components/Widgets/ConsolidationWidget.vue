<template>
    <WidgetWrapper 
        :widget="widget"
        ref="widgetWrapper"
        v-element-size="onResize"
        :class="isMobile && 'mobile_widget'">
        <div class="scroll">
            <div 
                class="flex h-full custom_opacity_transition">
                <div class="flex w-full min-w-0 border shrink-0 rounded-lg p-2 pl-4">
                    <div class="w-full flex flex-col min-h-0">
                        <div class="mb-8 flex">
                            <div class="mr-8">
                                <div class="text-base">
                                    {{ $t('dashboard.appealsPeriod') }}
                                </div> 
                                <div class="text-4xl font-semibold">
                                    {{ appealsTotal }}
                                </div>
                            </div>
                            <div>
                                <DateRangeSelect 
                                    @updateFilters="resetOrganizationGrid"
                                    :filters="filters"/>
                            </div>
                        </div>
                        <div>
                            <div class="custom_grid">
                                <span></span>
                                <span class="font-semibold text-center rounded-tl-xl header_cell custom_bg_warning">1-2 {{ $t('dashboard.points') }}</span>
                                <span class="font-semibold text-center header_cell custom_bg_danger">3-5 {{ $t('dashboard.points') }}</span>
                                <span class="font-semibold text-center rounded-tr-xl header_cell custom_bg_fatal">6-10 {{ $t('dashboard.points') }}</span>
                            </div>
                            <div class="data_grid rounded-tl-xl rounded-bl-xl rounded-br-xl">
                                <div class="custom_grid data_row">
                                    <div class="data_cell min-w-0 w-full flex items-center">
                                        <OrganizationSelect
                                            ref="organizationSelect"
                                            class="flex-grow min-w-0"
                                            @updateFilters="resetOrganizationGrid"
                                            :filters="filters" />
                                        <a-tooltip placement="top">
                                            <template slot="title">
                                                <span>{{ appealMode ? $t('dashboard.toList') : $t('dashboard.appeals') }}</span>
                                            </template>
                                            <a-button
                                                class="ml-2 shrink-0"
                                                flaticon
                                                :type="appealMode ? 'primary' : 'default'"
                                                :ghost="appealMode"
                                                icon="fi-rr-rectangle-list"
                                                @click="setAppealMode">
                                            </a-button>
                                        </a-tooltip>
                                    </div>
                                    <span class="text-center data_cell">{{ getParentAnalytics(0) }}</span>
                                    <span class="text-center data_cell">{{ getParentAnalytics(1) }}</span>
                                    <span class="text-center data_cell">{{ getParentAnalytics(2) }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex back">
                            <template v-if="parentId || appealMode">
                                <span
                                    @click="backToList"
                                    class="flex items-center font-semibold text-center back_link">
                                    <span class="pt-1 text-xl mr-2">
                                        <i class="fi fi-rr-arrow-left"></i>
                                    </span>
                                    {{ $t('dashboard.backToList') }}
                                </span>
                            </template>
                        </div>
                        <div class="flex flex-col min-h-0">
                            <div 
                                :class="appealMode ? 'risk_grid' : 'custom_grid'">
                                <template v-if="appealMode">
                                    <span class="font-semibold text-center header_cell"></span>
                                    <span class="font-semibold text-center header_cell">{{ $t('dashboard.number') }}</span>
                                    <span class="font-semibold text-center header_cell">{{ $t('dashboard.date') }}</span>
                                    <span class="font-semibold text-center rounded-tl-xl header_cell custom_bg_warning">1-2 {{ $t('dashboard.points') }}</span>
                                    <span class="font-semibold text-center header_cell custom_bg_danger">3-5 {{ $t('dashboard.points') }}</span>
                                    <span class="font-semibold text-center rounded-tr-xl header_cell custom_bg_fatal">6-10 {{ $t('dashboard.points') }}</span>
                                </template>
                                <template v-else> 
                                    <span></span>
                                    <span class="font-semibold text-center rounded-tl-xl header_cell custom_bg_warning">1-2 {{ $t('dashboard.points') }}</span>
                                    <span class="font-semibold text-center header_cell custom_bg_danger">3-5 {{ $t('dashboard.points') }}</span>
                                    <span class="font-semibold text-center rounded-tr-xl header_cell custom_bg_fatal">6-10 {{ $t('dashboard.points') }}</span>
                                </template>
                            </div>
                            <div class="data_grid rounded-tl-xl rounded-bl-xl rounded-br-xl">
                                <template v-if="appealMode">
                                    <div 
                                        v-for="(appeal, index) in appeals.list"
                                        :key="appeal.id"
                                        class="risk_grid data_row">

                                        <span class="data_cell">{{ index+1 }}</span>
                                        <span class="data_cell">{{ appeal.issue.number }}</span>
                                        <span class="text-center data_cell">{{ appeal.issue.issue_date }}</span>
                                        <span class="text-center data_cell">{{ powerCell(appeal.total_value, 0, 2) }}</span>
                                        <span class="text-center data_cell">{{ powerCell(appeal.total_value, 3, 5) }}</span>
                                        <span class="text-center data_cell">{{ powerCell(appeal.total_value, 6, 10) }}</span>
                                    </div>
                                </template>
                                <template v-else>
                                    <div 
                                        v-for="organization in organizations.list"
                                        :key="organization.id"
                                        class="custom_grid data_row">
                                        <span class="data_cell">
                                            <span 
                                                :title="organization.name"
                                                @click="selectOrganization(organization)"
                                                class="organization_name">
                                                {{ organization.name }}
                                            </span>
                                        </span>
                                        <span 
                                            v-for="analytics, index in organization.analytics"
                                            :key="index"
                                            class="text-center data_cell">{{ analytics }}</span>
                                    </div>
                                </template>
                                <template v-if="showGrid">
                                    <template v-if="appealMode">
                                        <infinite-loading 
                                            ref="infiniteLoading"
                                            @infinite="getAppealList"
                                            :identifier="identifier+'_appeals'"
                                            :distance="10">
                                            <div 
                                                slot="spinner"
                                                class="flex items-center justify-center inf_spinner">
                                                <a-spin size="small" />
                                            </div>
                                            <div slot="no-more"></div>
                                            <div slot="no-results"></div>
                                        </infinite-loading>
                                    </template>
                                    <template v-else>
                                        <infinite-loading 
                                            ref="infiniteLoading"
                                            @infinite="getOrganizationList"
                                            :identifier="identifier"
                                            :distance="10">
                                            <div 
                                                slot="spinner"
                                                class="flex items-center justify-center inf_spinner">
                                                <a-spin size="small" />
                                            </div>
                                            <div slot="no-more"></div>
                                            <div slot="no-results"></div>
                                        </infinite-loading>
                                    </template>
                                </template>
                            </div>
                        </div>
                    </div>                    
                </div>
            </div>
        </div>
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
        // AnalyticsFilters
        OrganizationSelect: () => import('../Analytics/OrganizationSelect.vue'),
        DateRangeSelect: () => import('../Analytics/DateRangeSelect.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
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
                        },
                        parent: null
                    },
                ],
                dateRange: {
                    start: null,
                    end: null,
                    format: 'YYYY-MM-DD'
                }
            },
            identifier: new Date(),
            organizationList: [],
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
            organizations: {
                next: true,
                list: [],
                page: 0
            },
            appeals: {
                next: true,
                list: [],
                page: 0
            },
            appealsTotal: 0,
            appealMode: false,
            selectedOrganization: null,
            appealOrganization: null,
            parentAnalytics: null
        }
    },
    computed: {
        isFinalOrganization() {
            return this.parentOrganization && this.organizations?.list?.length === 0 && !this.organizations.next
        },        
        parentOrganization() {
            const select = this.filters.selects.find(select => select.id === 'parent')
            const organizationId = Array.isArray(select?.value) ? select.value?.[0] : select.value
            return organizationId
        },
        showGrid() {
            return this.parentOrganization && !this.filters.selects[0].loading
        },
        // isListEmpty() {
        //     return this.organizations?.list?.length > 0 && !this.organizations.next
        // },
        parentId() {
            return this.filters.selects[0].parent
        },
        defaultDateRange() {
            return {
                start: this.$moment(new Date())
                    .subtract(1, 'week').format(this.filters.dateRange.format),
                end: this.$moment(new Date()).format(this.filters.dateRange.format),
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        related_object() {
            return this.widget.random_settings?.related_object?.id || null
        },
        //
        dashboardDeadlineViolationAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.deadlineViolationAnalytics'))
        },
        dashboardDeadlineViolationTotal() {
            return this.getTotal(this.$t('dashboard.deadlineViolationTotal'))
        },
        // 
        dashboardGOReviewedAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.GOReviewedAnalytics'))
        },
        dashboardGOReviewedTotal() {
            return this.getTotal(this.$t('dashboard.GOReviewedTotal'))
        },
        //
        dashboardEntraceSourceAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.entraceSourceAnalytics'))
        },
        dashboardEntraceSourceTotal() {
            return this.getTotal(this.$t('dashboard.entraceSourceTotal'))
        },
        // 
        dashboardAppealsAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.appealsAnalytics'))
        },

        _appealsTotal() {
            if (this.isFinalOrganization) {
                return this.appeals?.list?.length || 0
            }
            return this.organizations.list.reduce((total, organization) => { 
                return total + organization.analytics.reduce((analyticsTotal, analytics) => {
                    return analyticsTotal + analytics
                })
            }, 0)
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
        getParentAnalytics(index) {
            return this.parentAnalytics?.[index] || 0
        },
        async getOrganizationAnalytics() {
            const data = await this.syncOrganizatoinData([{ id: this.filters.selects[0].value }], 'parent')
            this.parentAnalytics = data[0].analytics
        },
        setAppealMode() {
            if (this.appealMode) {
                this.appealMode = false
                this.appealOrganization = null
                // this.resetAppeals()
            } else {
                this.appealMode = true
                this.appealOrganization = this.filters.selects[0].value
            }
            this.resetOrganizationList()
            this.resetAppeals()
            this.setTotalValue()
        },
        backToList() {
            this.filters.selects[0].parent = null
            // this.filters.selects[0].value = null
            this.resetAppealMode()
            this.$refs?.organizationSelect?.initParentOptions()
        },
        powerCell(value, start, end) {
            return (value >= start && value <= end) ? value : 0
        },
        resetOrganizationList() {
            this.identifier = new Date()
            this.organizations.list.splice(0)
            this.organizations.page = 0
            this.organizations.next = true
            
            this.appeals.list.splice(0)
            this.appeals.page = 0
            this.appeals.next = true
        },
        resetAppeals() {
            this.appeals.list.splice(0)
            this.appeals.page = 0
            this.appeals.next = true
            this.identifier = new Date()
        },
        // TODO: REFACTORING
        async getAnalytics(analyticReportId) {
            const parentSelect = this.filters.selects.find(selectItem => selectItem.id === 'parent')
            const displaySelect = this.filters.selects.find(selectItem => selectItem.id === 'displayed')

            const parent = JSON.parse(JSON.stringify(parentSelect.value))
            const display = JSON.parse(JSON.stringify(displaySelect.value))
                
            const start = this.$moment(this.filters.dateRange.start).format(this.filters.dateRange.format)
            const end = this.$moment(this.filters.dateRange.end).format(this.filters.dateRange.format)

            const params = {
                organizations: parent ? [parent] : null,
                start: start || this.defaultDateRange.start,
                end: end || this.defaultDateRange.end,
                analytic_report: analyticReportId,
                display: display,
            }
            if(!params.display?.length) {
                delete params.display
            }

            const analyticsURL = `consolidation/${parent}/analytics`
            const analyticsResponse = await this.$http.get(analyticsURL, { params })
            if(!analyticsResponse.data?.length) {
                return 0
            }
            const foundIndex = this.analyticReports.findIndex(report => report.id === analyticReportId)
            this.analyticReports[foundIndex].analytics = analyticsResponse.data
        },
        async setTotalValue() {
            const dateRange = this.filters.dateRange

            const params = {
                display: 'descendants',
                organization: this.selectedOrganization || this.parentOrganization,
                filters: { 
                    issue__issue_date__gte: this.$moment(dateRange?.start).format('YYYY-MM-DD') || '',
                    issue__issue_date__lte: this.$moment(dateRange?.end).format('YYYY-MM-DD') || '' 
                }
            }
            if (this.appealMode) {
                delete params.display
            }
            const { data } = await this.$http(`risk_assessment/count/`, {
                params
            })
            this.appealsTotal = data.count
        },
        selectOrganization(organization) {
            this.selectedOrganization = organization.id
            this.filters.selects[0].parent = JSON.parse(JSON.stringify(this.filters.selects[0].value))
            this.setTotalValue()

            this.resetOrganizationList()

            this.$refs?.organizationSelect?.initParentOptions(organization.id)
        },
        resetOrganizationGrid() {
            this.getOrganizationAnalytics()
            this.setTotalValue()
            this.resetOrganizationList()
        },
        resetAppealMode() {
            this.selectedOrganization = null
            this.appealMode = false
            this.setTotalValue()
            this.resetOrganizationList()
        },
        async syncOrganizatoinData(organizationList, dist=null) {
            const data = await this.getRiskData(organizationList, dist)
            const organizations = organizationList.map(organization => {
                const analyticsData = data.find(analytic => analytic.organization_id === organization.id)
                organization.analytics = [0, 0, 0]
                for(let i=0; i < analyticsData?.data?.length; i++) {
                    if (analyticsData.data[i].total_value <= 2) {
                        organization.analytics[0] += analyticsData.data[i].dcount
                    } else if (analyticsData.data[i].total_value >= 3 && 
                            (analyticsData.data[i].total_value <= 5)) {
                        organization.analytics[1] += analyticsData.data[i].dcount
                    } else {
                        organization.analytics[2] += analyticsData.data[i].dcount
                    }
                }
                // organization.analytics = analyticsData.data
                // organization.analytics = [{ total_value: 0, dcount: 1}, { total_value: 3, dcount: 1}, { total_value: 5, dcount: 1}]
                return organization
            })
            if (dist === 'parent') {
                return organizations
            }
            this.organizations.list.push(...organizations)
        },
        async getOrganizationList($state) {
            if (this.organizations.next) {
                this.organizations.page++
                const params = {
                    page_size: 10,
                    page: this.organizations.page,
                    page_name: 'risk_map_widget'
                }

                const url = this.getSelectURL()                
                const { data } = await this.$http(url, { params })
                if (data?.results?.length) {
                    const organizationList = data.results.map(relation => relation.contractor)
                    await this.syncOrganizatoinData(organizationList)
                }
                this.organizations.next = data.next

                if (data.next) {
                    $state.loaded()
                } else {
                    if (!this.organizations.list?.length) {
                        this.appealMode = true
                    }
                    $state.complete()
                }
            }
        },
        async getAppealList($state) {
            if (this.appeals.next) {
                this.appeals.page++
                const dateRange = this.filters.dateRange
                const params = {
                    page_size: 10,
                    page: this.appeals.page,
                    page_name: 'risk_map_widget',
                    filters: { 
                        organization: this.appealOrganization || this.selectedOrganization,
                        issue__issue_date__gte: this.$moment(dateRange?.start).format('YYYY-MM-DD') || '',
                        issue__issue_date__lte: this.$moment(dateRange?.end).format('YYYY-MM-DD') || '' 
                    }
                }

                const url = `/risk_assessment/`
                const { data } = await this.$http(url, { params })
                this.appeals.list.push(...data.results)

                if (data.next) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            }
        },
        
        async getRiskData(organizations, dist) {
            const url = `/risk_assessment/aggregate/`
            
            const organizationIdList = organizations.map(organization => organization.id)
            
            const dateRange = this.filters.dateRange
            const payload = {
                display: 'descendants',
                organizations: organizationIdList,
                filters: {
                    issue__issue_date__gte: this.$moment(dateRange?.start).format('YYYY-MM-DD') || '',
                    issue__issue_date__lte: this.$moment(dateRange?.end).format('YYYY-MM-DD') || '' 
                }
            }
            if (dist === 'parent') {
                delete payload.display
            }
            const { data } = await this.$http.post(url, payload)
            return data 
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
        getExitstingReport(reportName) {
            const foundIndex = this.analyticReports.findIndex(report => report.name === reportName)
            return this.analyticReports?.[foundIndex] || null
        },
        getExitstingAnalytics(reportName) {
            const report = this.getExitstingReport(reportName)
            if(report?.analytics?.length)
                return report.analytics
            return []
        },
        getTotal(reportName) {
            const analytics = this.getExitstingAnalytics(reportName)
            if(analytics?.length)
                return analytics?.[0]?.value
                // return analytics.reduce((total, current) => total + current.value, 0) || 0
            return 0
        },
        getAnalyticsList(reportName) {
            const analytics = this.getExitstingAnalytics(reportName)
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
        getSelectURL() {
            let parentOrganizationId = this.parentOrganization
            if (this.selectedOrganization) {
                parentOrganizationId = this.selectedOrganization
            } 
            return parentOrganizationId ? `/users/my_organizations/${parentOrganizationId}/relations/` : null
        },

    }
}
</script>

<style lang="scss" scoped>
.risk_grid {
    display: grid;
    grid-template-columns: 60px repeat(5, 1fr);
    &:last-child {
        border-bottom: none;
    }
}
.back {
    height: 32px;
    flex-shrink: 0;
}
.back_link {
    cursor: pointer;
    transition: color 0.2s ease;
}
.back_link:hover {
    color: var(--blue);
}
.header_cell,
.data_cell {
    padding: 0.5rem 0.5rem;
}
.header_cell {
    color: #333;
}
.data_cell + .data_cell {
    border-left: 1px solid #ebebeb;
}
.data_row:not(:last-child) {
    border-bottom: 1px solid #ebebeb;
}

.data_row {
    border-left: 1px solid #ebebeb;
    border-right: 1px solid #ebebeb;
}
.data_grid {
    overflow-y: auto;
    border-top: 1px solid #ebebeb;
    border-bottom: 1px solid #ebebeb;
}
.organization_name {
    cursor: pointer;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    transition: color 0.2s ease;
    &:hover {
        color: var(--blue);
    }
}
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
.custom_grid {
    display: grid;
    grid-template-columns: 1fr repeat(3, 100px);
    &:last-child {
        border-bottom: none;
    }
}
.custom_bg_warning {
    background-color: #ffe936;
}
.custom_bg_danger {
    background-color: #ff9231;
}
.custom_bg_fatal {
    background-color: #ff4e46;   
}


</style>
