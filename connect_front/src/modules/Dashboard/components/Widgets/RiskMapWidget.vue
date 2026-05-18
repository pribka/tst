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
                        <div class="mb-2 flex justify-between">
                            <div class="mr-8">
                                <div class="text-base">
                                    {{ $t('dashboard.appeals_total') }}
                                </div> 
                                <div class="text-4xl font-semibold">
                                    {{ appealsTotal }}
                                </div>
                            </div>
                            <div>
                                <DateRangeSelect 
                                    @updateFilters="updateFilters"
                                    :filters="filters"/>
                            </div>
                        </div>
                        <div class="shrink-0 overflow-x-auto">
                            <div class="risk_data">
                                <div class="custom_grid">
                                    <span></span>
                                    <span class="font-semibold text-center rounded-tl-xl header_cell custom_bg_neutral">{{ $t('dashboard.points_0') }}</span>
                                    <span class="font-semibold text-center header_cell custom_bg_warning">{{ $t('dashboard.points_1_2') }}</span>
                                    <span class="font-semibold text-center header_cell custom_bg_danger">{{ $t('dashboard.points_3_5') }}</span>
                                    <span class="font-semibold text-center rounded-tr-xl header_cell custom_bg_fatal">{{ $t('dashboard.points_5_10') }}</span>
                                </div>
                                <div class="data_grid rounded-tl-xl rounded-bl-xl rounded-br-xl">
                                    <div class="custom_grid data_row">
                                        <div class="data_cell min-w-0 w-full flex items-center">
                                            <OrganizationSelect
                                                ref="organizationSelect"
                                                class="flex-grow min-w-0"
                                                @updateFilters="resetOrganizationGrid"
                                                :filters="filters" />
                                        </div>
                                        <span class="text-center data_cell">{{ getParentAnalytics(0) }}</span>
                                        <span class="text-center data_cell">{{ getParentAnalytics(1) }}</span>
                                        <span class="text-center data_cell">{{ getParentAnalytics(2) }}</span>
                                        <span class="text-center data_cell">{{ getParentAnalytics(3) }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-2 mb-4 custom_grid back">
                            <div class="flex justify-between">
                                <a-button
                                    class="w-1/2 mr-2"
                                    flaticon
                                    :disabled="!parentId"
                                    :loading="organizationLoading"
                                    type="primary"
                                    ghost
                                    @click="setPreviousParent">
                                    {{ $t('dashboard.higher_level') }}
                                </a-button>
                                <a-button
                                    class="ml-auto w-1/2"
                                    flaticon
                                    type="primary"
                                    ghost
                                    @click="setAppealMode">
                                    {{ appealMode ? $t('dashboard.show_organizations') : $t('dashboard.show_appeals') }}
                                </a-button>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <div class="risk_data flex flex-col min-h-0">
                                <div 
                                    :class="appealMode ? 'risk_grid' : 'custom_grid'">
                                    <template v-if="appealMode">
                                        <span class="min-w-0 font-semibold text-center header_cell"></span>
                                        <span class="min-w-0 truncate font-semibold text-center header_cell" title="Номер">{{ $t('dashboard.number') }}</span>
                                        <span class="min-w-0 font-semibold text-center header_cell">{{ $t('dashboard.date') }}</span>
                                    </template>
                                    <template v-else> 
                                        <span></span>
                                    </template>
                                    <span class="font-semibold text-center rounded-tl-xl header_cell custom_bg_neutral">0 баллов</span>
                                    <span class="font-semibold text-center header_cell custom_bg_warning">1-2 балла</span>
                                    <span class="font-semibold text-center header_cell custom_bg_danger">3-5 баллов</span>
                                    <span class="font-semibold text-center rounded-tr-xl header_cell custom_bg_fatal">5-10 баллов</span>
                                </div>
                                <div class="data_grid rounded-tl-xl rounded-bl-xl rounded-br-xl">
                                    <template v-if="appealMode">
                                        <div 
                                            v-for="(appeal, index) in appeals.list"
                                            :key="appeal.id"
                                            class="risk_grid data_row">
                                            <span class="min-w-0 data_cell">{{ index+1 }}</span>
                                            <span class="min-w-0 truncate data_cell" :title="appeal.issue.number">{{ appeal.issue.number }}</span>
                                            <span class="min-w-0 truncate text-center data_cell" :title="appeal.issue.issue_date">{{ appeal.issue.issue_date }}</span>
                                            <span class="min-w-0 text-center data_cell">{{ powerCell(appeal.total_value, 0, 0) }}</span>
                                            <span class="min-w-0 text-center data_cell">{{ powerCell(appeal.total_value, 1, 2) }}</span>
                                            <span class="min-w-0 text-center data_cell">{{ powerCell(appeal.total_value, 3, 5) }}</span>
                                            <span class="min-w-0 text-center data_cell">{{ powerCell(appeal.total_value, 6, 2) }}</span>
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
                                                ref="appealInfiniteLoading"
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
                                            <template v-if="!appeals.next && appeals.list && !appeals.list.length">
                                                <div class="no_results data_cell">
                                                    {{ $t('dashboard.no_appeals') }}
                                                </div>
                                            </template>
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
                                            <template v-if="!organizations.next && organizations.list && !organizations.list.length">
                                                <div class="no_results data_cell">
                                                    {{ $t('dashboard.no_organizations') }}
                                                </div>
                                            </template>
                                        </template>
                                    </template>
                                </div>
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
import InfiniteLoading from 'vue-infinite-loading'
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
        InfiniteLoading
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
            parentAnalytics: null,
            parentList: [],
            organizationLoading: false
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
            return this.getAnalyticsList(this.$t('dashboard.deadlineViolation'))
        },
        dashboardDeadlineViolationTotal() {
            return this.getTotal(this.$t('dashboard.deadlineViolation'))
        },
        // 
        dashboardGOReviewedAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.GOReviewed'))
        },
        dashboardGOReviewedTotal() {
            return this.getTotal(this.$t('dashboard.GOReviewed'))
        },
        //
        dashboardEntraceSourceAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.entraceSource'))
        },
        dashboardEntraceSourceTotal() {
            return this.getTotal(this.$t('dashboard.entraceSource'))
        },
        // 
        dashboardAppealsAnalytics() {
            return this.getAnalyticsList(this.$t('dashboard.appeals'))
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
        setPreviousParent() {
            const lastIndex = String(this.parentList.length-1)
            
            this.selectedOrganization = this.parentList[lastIndex]
            this.filters.selects[0].parent = this.parentList[lastIndex-1] || null
            this.setTotalValue()

            this.resetOrganizationList()
            this.$refs?.organizationSelect?.initParentOptions(this.parentList[lastIndex])
            this.parentList.splice(-1, 1)
            this.organizationLoading = true
        },
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
        async backToList() {
            
            this.filters.selects[0].parent = null
            // this.filters.selects[0].value = null
            this.resetAppealMode()
            await this.$refs?.organizationSelect?.initParentOptions()
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
            this.parentList.push(this.filters.selects[0].value)
            this.filters.selects[0].parent = JSON.parse(JSON.stringify(this.filters.selects[0].value))
            this.setTotalValue()

            this.resetOrganizationList()

            this.$refs?.organizationSelect?.initParentOptions(organization.id)
        },
        updateFilters() {
            this.selectedOrganization = this.filters.selects[0].value
            this.resetOrganizationGrid
        },
        resetOrganizationGrid() {
            this.getOrganizationAnalytics()
            this.setTotalValue()
            this.resetOrganizationList()
        },
        resetAppealMode() {
            // this.selectedOrganization = null
            this.appealMode = false
            this.setTotalValue()
            this.resetOrganizationList()
        },
        async syncOrganizatoinData(organizationList, dist=null) {
            const data = await this.getRiskData(organizationList, dist)
            const organizations = organizationList.map(organization => {
                const analyticsData = data.find(analytic => analytic.organization_id === organization.id)
                organization.analytics = [0, 0, 0, 0]
                for(let i=0; i < analyticsData?.data?.length; i++) {
                    if (analyticsData.data[i].total_value < 1) {
                        organization.analytics[0] += analyticsData.data[i].dcount
                    } else if (analyticsData.data[i].total_value <= 2) {
                        organization.analytics[1] += analyticsData.data[i].dcount
                    } else if (analyticsData.data[i].total_value >= 3 && 
                            (analyticsData.data[i].total_value <= 5)) {
                        organization.analytics[2] += analyticsData.data[i].dcount
                    } else {
                        organization.analytics[3] += analyticsData.data[i].dcount
                    }
                }
                return organization
            })
            if (dist === 'parent') {
                return organizations
            }
            this.organizations.list.push(...organizations)
        },
        async getOrganizationList($state) {
            if (this.organizations.next) {
                this.organizationLoading = true
                this.organizations.page++
                const params = {
                    page_size: 10,
                    page: this.organizations.page,
                    page_name: 'risk_map_widget'
                }

                const url = this.getSelectURL()
                let response = null
                try {
                    response = await this.$http(url, { params })
                } catch (error) {
                    console.error(error)
                }
                const data = response.data
                if (data?.results?.length) {
                    const organizationList = data.results.map(relation => relation.contractor)
                    await this.syncOrganizatoinData(organizationList)
                }
                this.organizations.next = data.next

                if (data.next) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
                this.organizationLoading = false

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
                let response = null
                try {
                    response = await this.$http(url, { params })
                } catch (error) {
                    console.error(error)
                }
                const data  = response?.data
                if (data?.results?.length) {
                    this.appeals.list.push(...data.results)
                    this.appeals.next = data.next
                }


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
            if (this.selectedOrganization && this.parentId) {
                parentOrganizationId = this.selectedOrganization
            } 
            return parentOrganizationId ? `/users/my_organizations/${parentOrganizationId}/relations/` : null
        },

    }
}
</script>

<style lang="scss" scoped>
.no_results {
    border-left: 1px solid #ebebeb;
    border-right: 1px solid #ebebeb;
}
.risk_data {
    min-width: 550px;
}
.risk_grid {
    display: grid;
    grid-template-columns: 60px repeat(2, 1fr) repeat(4, 100px);
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
    grid-template-columns: 1fr repeat(4, 100px);
    &:last-child {
        border-bottom: none;
    }
}
.custom_bg_neutral {
    background-color: #eee;
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
