<template>
    <div class="h-full consolidation">
        <ConsolidationFilters
            :scope="scope"
            :related-object="relatedObject"
            :scope-options="scopeOptions"
            :is-mobile="isMobile"
            :can-request="canRequestAISummary"
            :generate-loading="aiSummaryGenerateLoading"
            :get-popup-container="getPopupContainer"
            @update:scope="scope = $event"
            @update:relatedObject="relatedObject = $event"
            @generate-summary="handleGenerateSummary" />

        <ConsolidationAISummary
            ref="aiSummary"
            :scope="scope"
            :related-object-id="relatedObjectId"
            :related-object-summary-value="relatedObjectSummaryValue"
            :start-date="startDate"
            :end-date="endDate"
            :can-request="canRequestAISummary"
            :is-mobile="isMobile"
            @generate-loading-change="aiSummaryGenerateLoading = $event" />

        <ConsolidationPlaceholder v-if="!canFetchCards" />

        <ConsolidationKPIGroup
            v-for="(group, groupIndex) in visibleKpiGroups"
            :key="`kpi-${group?.title || groupIndex}`"
            :group="group"
            :group-index="groupIndex"
            :scope="scope"
            :related-object-id="relatedObjectReportValue"
            :start-date="startDate"
            :end-date="endDate"
            :widget-key-fn="kpiWidgetKey"
            :widget-class-fn="kpiCardClass" />

        <ConsolidationDashboardGroup
            v-for="(group, groupIndex) in visibleDashboardGroups"
            :key="group?.title || groupIndex"
            :group="group"
            :group-index="groupIndex"
            :widget-key-fn="widgetCacheKey"
            :loading-fn="isWidgetCardLoading"
            :error-fn="widgetCardError"
            :chart-data-fn="widgetChartData"
            :chart-width-fn="widgetChartWidth"
            :chart-height-fn="widgetChartHeight"
            :chart-type-fn="widgetChartType"
            :scope="scope"
            :related-object-id="relatedObjectReportValue"
            :start-date="startDate"
            :end-date="endDate" />
    </div>
</template>

<script>
export default {
    components: {
        ConsolidationAISummary: () => import('./components/ConsolidationAISummary.vue'),
        ConsolidationFilters: () => import('./components/ConsolidationFilters.vue'),
        ConsolidationKPIGroup: () => import('./components/ConsolidationKPIGroup.vue'),
        ConsolidationDashboardGroup: () => import('./components/ConsolidationDashboardGroup.vue'),
        ConsolidationPlaceholder: () => import('./components/ConsolidationPlaceholder.vue')
    },
    data() {
        return {
            scope: null,
            relatedObject: null,
            restoringFilters: false,
            initialized: false,
            normalizedWidgetCharts: {},
            aiSummaryGenerateLoading: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        dateRange() {
            return this.$store.state.workplan?.employeesDateRange || []
        },
        savedFilters() {
            return this.$store.state.workplan?.consolidationFilters || {
                scope: null,
                relatedObject: null
            }
        },
        kpiData() {
            return this.$store.state.workplan?.consolidationKeyResults?.data || null
        },
        dashboardData() {
            return this.$store.state.workplan?.consolidationDashboard?.data || null
        },
        reportSettingsCache() {
            return this.$store.state.workplan?.consolidationReportSettings || {}
        },
        widgetReportCache() {
            return this.$store.state.workplan?.consolidationWidgetReports || {}
        },
        kpiGroups() {
            return Array.isArray(this.kpiData?.groups)
                ? this.kpiData.groups
                : []
        },
        dashboardGroups() {
            return Array.isArray(this.dashboardData?.groups)
                ? this.dashboardData.groups
                : []
        },
        visibleKpiGroups() {
            return this.canFetchCards ? this.kpiGroups : []
        },
        visibleDashboardGroups() {
            return this.canFetchCards ? this.dashboardGroups : []
        },
        scopeOptions() {
            return [
                { value: 'root_organization', label: this.$t('workplan.filter_root_organization') },
                { value: 'organization', label: this.$t('workplan.filter_organization') },
                { value: 'project', label: this.$t('workplan.filter_project') },
                { value: 'user', label: this.$t('workplan.filter_user') }
            ]
        },
        dateRangeKey() {
            const start = this.dateRange?.[0] ? this.$moment(this.dateRange[0]).format('YYYY-MM-DD') : ''
            const end = this.dateRange?.[1] ? this.$moment(this.dateRange[1]).format('YYYY-MM-DD') : ''
            return `${start}_${end}`
        },
        relatedObjectId() {
            if (!this.relatedObject) return null
            if (typeof this.relatedObject === 'string') return this.relatedObject
            if (Array.isArray(this.relatedObject))
                return this.relatedObject[0]?.id || null
            return this.relatedObject?.id || null
        },
        isUserScope() {
            return this.scope === 'user'
        },
        relatedUsers() {
            if (!this.isUserScope) return []
            if (Array.isArray(this.relatedObject)) return this.relatedObject.filter(Boolean)
            return this.relatedObject ? [this.relatedObject] : []
        },
        relatedObjectIds() {
            if (this.isUserScope)
                return this.relatedUsers
                    .map(item => item?.id)
                    .filter(Boolean)

            if (!this.relatedObjectId) return []
            return [this.relatedObjectId]
        },
        relatedObjectUids() {
            if (!this.isUserScope) return []
            return this.relatedUsers
                .map(item => item?.uid || item?.id)
                .filter(Boolean)
        },
        relatedObjectParamValue() {
            if (this.isUserScope)
                return this.relatedObjectUids.join(',')

            return this.relatedObjectId
        },
        relatedObjectReportValue() {
            if (this.isUserScope)
                return this.relatedObjectIds

            return this.relatedObjectId
        },
        relatedObjectSummaryValue() {
            if (this.isUserScope)
                return this.relatedObjectIds.join(',')

            return this.relatedObjectId || ''
        },
        canRequestAISummary() {
            if (!this.startDate || !this.endDate || !this.scope)
                return false

            if (this.isUserScope)
                return this.relatedObjectIds.length === 1

            return Boolean(this.relatedObjectSummaryValue)
        },
        relatedObjectCacheKey() {
            const value = this.relatedObjectReportValue
            if (Array.isArray(value))
                return value.join(',')
            return value || ''
        },
        startDate() {
            if (!this.dateRange?.[0]) return null
            return this.$moment(this.dateRange[0]).format('YYYY-MM-DD')
        },
        endDate() {
            if (!this.dateRange?.[1]) return null
            return this.$moment(this.dateRange[1]).format('YYYY-MM-DD')
        },
        canRequest() {
            return Boolean(this.startDate && this.endDate && this.scope && this.relatedObjectParamValue)
        },
        canFetchCards() {
            return this.canRequest
        }
    },
    watch: {
        scope() {
            if (this.restoringFilters) return
            this.relatedObject = this.getDefaultRelatedObjectByScope()
            this.saveFiltersToStore()
            this.resetDashboardData()
        },
        relatedObjectParamValue() {
            if (this.restoringFilters) return
            this.saveFiltersToStore()
            if (this.canFetchCards)
                this.fetchDashboardData()
            else
                this.resetDashboardData()
        },
        dateRangeKey() {
            if (this.canFetchCards)
                this.refreshDataForCurrentDateRange()
            else
                this.resetDashboardData()
        }
    },
    methods: {
        handleGenerateSummary() {
            if (typeof this.$refs?.aiSummary?.generateSummary === 'function')
                this.$refs.aiSummary.generateSummary()
        },
        getDefaultRelatedObjectByScope(scope = this.scope) {
            return scope === 'user' ? [] : null
        },
        getPopupContainer(trigger) {
            return trigger?.parentNode || document.body
        },
        saveFiltersToStore() {
            this.$store.commit('workplan/SET_CONSOLIDATION_FILTERS', {
                scope: this.scope || null,
                relatedObject: this.scope === 'user'
                    ? (Array.isArray(this.relatedObject) ? this.relatedObject : [])
                    : (this.relatedObject || null)
            })
        },
        restoreFiltersFromStore() {
            this.restoringFilters = true
            this.scope = this.savedFilters?.scope || null
            this.relatedObject = this.scope === 'user'
                ? (Array.isArray(this.savedFilters?.relatedObject) ? this.savedFilters.relatedObject : [])
                : (this.savedFilters?.relatedObject || null)
            this.$nextTick(() => {
                this.restoringFilters = false
            })
        },
        resetDashboardData() {
            this.$store.commit('workplan/SET_CONSOLIDATION_KEY_RESULTS', null)
            this.$store.commit('workplan/SET_CONSOLIDATION_DASHBOARD', null)
        },
        widgetCacheKey(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const requestData = this.widgetReportRequest(widget)
            const reportCode = requestData?.reportCode || `widget-${groupIndex}-${widgetIndex}`
            const filterPreset = requestData?.filterPreset || ''
            const scope = this.scope || ''
            return [reportCode, filterPreset, scope].join('::')
        },
        kpiWidgetKey(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const widgetCode = widget?.widget_code || widget?.title || 'kpi-widget'
            return `${widgetCode}-${groupIndex}-${widgetIndex}`
        },
        widgetReportRequest(widget = {}) {
            return {
                reportCode: widget?.report_code || null,
                filterPreset: widget?.filter_preset || null
            }
        },
        kpiCardClass(widget = {}) {
            const title = String(widget?.title || '').toLowerCase()

            if (title.includes('просроч'))
                return 'consolidation_kpi_card--danger'
            if (title.includes('без движения'))
                return 'consolidation_kpi_card--warning'

            return ''
        },
        reportSettingsState(widget = {}) {
            const key = this.widgetCacheKey(widget)
            return this.reportSettingsCache?.[key] || {
                loading: false,
                loaded: false,
                data: null,
                error: null
            }
        },
        widgetReportState(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const key = [
                this.widgetCacheKey(widget, groupIndex, widgetIndex),
                this.relatedObjectCacheKey,
                this.startDate || '',
                this.endDate || ''
            ].join('::')

            return this.widgetReportCache?.[key] || {
                loading: false,
                loaded: false,
                data: null,
                error: null
            }
        },
        isWidgetCardLoading(widget = {}, groupIndex = 0, widgetIndex = 0) {
            return Boolean(
                this.reportSettingsState(widget).loading
                || this.widgetReportState(widget, groupIndex, widgetIndex).loading
            )
        },
        widgetCardError(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const widgetReportError = this.widgetReportState(widget, groupIndex, widgetIndex).error
            const reportSettingsError = this.reportSettingsState(widget).error
            const error = widgetReportError || reportSettingsError

            if (!error) return ''
            if (typeof error === 'string') return error
            if (typeof error?.detail === 'string') return error.detail
            if (Array.isArray(error?.non_field_errors) && error.non_field_errors.length)
                return error.non_field_errors[0]
            if (typeof error?.message === 'string') return error.message
            return 'Ошибка загрузки данных'
        },
        widgetChartData(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const data = this.widgetReportState(widget, groupIndex, widgetIndex).data
            if (!data?.series || !data?.chartOptions) return null

            const cacheKey = [
                this.widgetCacheKey(widget, groupIndex, widgetIndex),
                this.relatedObjectCacheKey,
                this.startDate || '',
                this.endDate || ''
            ].join('::')
            const cachedChart = this.normalizedWidgetCharts[cacheKey]

            if (cachedChart?.source === data)
                return cachedChart.value

            const categories = Array.isArray(data.chartOptions?.xaxis?.categories)
                ? data.chartOptions.xaxis.categories
                : []
            const isDenseChart = categories.length > 12
            const chartType = data.chartOptions?.chart?.type || 'line'
            const isLineChart = chartType === 'line'
            const linePointCount = isLineChart
                ? (Array.isArray(data.series) ? data.series : []).reduce((count, seriesItem) => {
                    const points = Array.isArray(seriesItem?.data) ? seriesItem.data : []
                    return count + points.filter(value => value !== null && value !== undefined && value !== '').length
                }, 0)
                : 0
            const hasSingleLinePoint = isLineChart && linePointCount <= 1

            const normalizedChart = {
                ...data,
                chartOptions: {
                    ...data.chartOptions,
                    chart: {
                        ...(data.chartOptions?.chart || {}),
                        toolbar: {
                            show: false
                        }
                    },
                    colors: data.chartOptions?.colors?.length
                        ? data.chartOptions.colors
                        : ['#1D65C0', '#31C56D', '#FF7B7B'],
                    grid: {
                        show: true,
                        strokeDashArray: 10,
                        borderColor: '#E7ECF4',
                        padding: {
                            left: 0,
                            right: 4,
                            top: -10,
                            bottom: 0
                        },
                        ...(data.chartOptions?.grid || {})
                    },
                    plotOptions: {
                        ...(data.chartOptions?.plotOptions || {}),
                        bar: {
                            ...((data.chartOptions?.plotOptions || {}).bar || {}),
                            borderRadius: 2,
                            borderRadiusApplication: 'end',
                            borderRadiusWhenStacked: 'last',
                            columnWidth: '44%'
                        }
                    },
                    dataLabels: {
                        enabled: isLineChart ? false : !isDenseChart,
                        ...(data.chartOptions?.dataLabels || {}),
                        formatter: (val) => (val === 0 || val === null || val === undefined) ? '' : val,
                        style: {
                            fontSize: '14px',
                            fontWeight: 400,
                            colors: [({ seriesIndex, dataPointIndex, w }) => {
                                const pointValue = w?.config?.series?.[seriesIndex]?.data?.[dataPointIndex]
                                return Number(pointValue) > 0 ? '#FFFFFF' : '#5F7192'
                            }],
                            ...((data.chartOptions?.dataLabels || {}).style || {})
                        }
                    },
                    xaxis: {
                        ...(data.chartOptions?.xaxis || {}),
                        axisBorder: {
                            show: false,
                            ...((data.chartOptions?.xaxis || {}).axisBorder || {})
                        },
                        axisTicks: {
                            show: false,
                            ...((data.chartOptions?.xaxis || {}).axisTicks || {})
                        },
                        crosshairs: {
                            show: false,
                            ...((data.chartOptions?.xaxis || {}).crosshairs || {})
                        },
                        labels: {
                            hideOverlappingLabels: true,
                            trim: false,
                            rotate: 0,
                            minWidth: 0,
                            style: {
                                fontSize: '11px',
                                colors: '#B0B8C5',
                                ...(((data.chartOptions?.xaxis || {}).labels || {}).style || {})
                            },
                            ...((data.chartOptions?.xaxis || {}).labels || {})
                        }
                    },
                    yaxis: {
                        ...(data.chartOptions?.yaxis || {}),
                        labels: {
                            offsetX: -5,
                            offsetY: 4,
                            style: {
                                fontSize: '11px',
                                colors: '#B0B8C5',
                                cssClass: 'opacity-60',
                                ...(((data.chartOptions?.yaxis || {}).labels || {}).style || {})
                            },
                            ...((data.chartOptions?.yaxis || {}).labels || {})
                        }
                    },
                    stroke: {
                        ...((data.chartOptions || {}).stroke || {}),
                        curve: isLineChart ? 'straight' : (((data.chartOptions || {}).stroke || {}).curve || 'smooth'),
                        width: isLineChart
                            ? (hasSingleLinePoint ? 0 : 4)
                            : 0,
                        lineCap: 'round'
                    },
                    markers: {
                        ...((data.chartOptions || {}).markers || {}),
                        size: isLineChart
                            ? (hasSingleLinePoint ? 4 : 0)
                            : (((data.chartOptions || {}).markers || {}).size || 0),
                        hover: {
                            ...(((data.chartOptions || {}).markers || {}).hover || {}),
                            size: isLineChart
                                ? (hasSingleLinePoint ? 5 : 4)
                                : ((((data.chartOptions || {}).markers || {}).hover || {}).size || 0)
                        },
                        strokeWidth: isLineChart ? 1.5 : (((data.chartOptions || {}).markers || {}).strokeWidth || 0),
                        strokeColors: isLineChart
                            ? (data.chartOptions?.colors?.length
                                ? data.chartOptions.colors
                                : ['#1D65C0', '#31C56D', '#FF7B7B'])
                            : (((data.chartOptions || {}).markers || {}).strokeColors || '#FFFFFF'),
                        fillOpacity: 1
                    },
                    legend: {
                        position: 'bottom',
                        horizontalAlign: 'left',
                        fontSize: '11px',
                        offsetY: 2,
                        labels: {
                            colors: '#5F7192'
                        },
                        markers: {
                            radius: 2
                        },
                        itemMargin: {
                            horizontal: 10
                        },
                        ...((data.chartOptions || {}).legend || {})
                    }
                }
            }

            this.$set(this.normalizedWidgetCharts, cacheKey, {
                source: data,
                value: normalizedChart
            })

            return normalizedChart
        },
        widgetChartWidth(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const chartData = this.widgetChartData(widget, groupIndex, widgetIndex)
            const categories = Array.isArray(chartData?.chartOptions?.xaxis?.categories)
                ? chartData.chartOptions.xaxis.categories
                : []

            if (categories.length <= 12)
                return '100%'

            return `${Math.max(categories.length * 34, 520)}px`
        },
        widgetChartHeight(widget = {}, groupIndex = 0, widgetIndex = 0) {
            const chartData = this.widgetChartData(widget, groupIndex, widgetIndex)
            const categories = Array.isArray(chartData?.chartOptions?.xaxis?.categories)
                ? chartData.chartOptions.xaxis.categories
                : []

            return categories.length <= 12 ? 240 : 250
        },
        widgetChartType(widget = {}, groupIndex = 0, widgetIndex = 0) {
            return this.widgetChartData(widget, groupIndex, widgetIndex)?.chartOptions?.chart?.type || 'line'
        },
        async fetchWidgetReportSettings(groups = this.dashboardGroups) {
            const widgetRequests = []

            groups.forEach(group => {
                ;(group?.widgets || []).forEach(widget => {
                    const requestData = this.widgetReportRequest(widget)
                    if (!requestData?.reportCode) return

                    widgetRequests.push(
                        this.$store.dispatch('workplan/getConsolidationReportSettings', {
                            reportCode: requestData.reportCode,
                            filterPreset: requestData.filterPreset,
                            scope: this.scope
                        })
                    )
                })
            })

            await Promise.all(widgetRequests)
        },
        async fetchWidgetReports(groups = this.dashboardGroups, { force = true } = {}) {
            if (!this.scope || !this.relatedObjectParamValue || !this.startDate || !this.endDate)
                return

            const widgetRequests = []

            groups.forEach((group, groupIndex) => {
                ;(group?.widgets || []).forEach((widget, widgetIndex) => {
                    const reportSettings = this.reportSettingsState(widget).data
                    if (!reportSettings) return

                    widgetRequests.push(
                        this.$store.dispatch('workplan/getConsolidationWidgetReport', {
                            widgetKey: this.widgetCacheKey(widget, groupIndex, widgetIndex),
                            reportSettings,
                            scope: this.scope,
                            relatedObjectId: this.relatedObjectReportValue,
                            startDate: this.startDate,
                            endDate: this.endDate,
                            force
                        })
                    )
                })
            })

            await Promise.all(widgetRequests)
        },
        async refreshWidgetReportsForCurrentFilters() {
            if (!this.canFetchCards) {
                this.resetDashboardData()
                return
            }

            const groups = this.dashboardGroups

            if (!groups.length) {
                await this.fetchDashboardData()
                return
            }

            await this.fetchWidgetReports(groups, { force: true })
        },
        async refreshDataForCurrentDateRange() {
            if (!this.canFetchCards) {
                this.resetDashboardData()
                return
            }

            await this.$store.dispatch('workplan/getConsolidationKeyResults', {
                scope: this.scope,
                relatedObjectId: this.relatedObjectParamValue
            })

            await this.refreshWidgetReportsForCurrentFilters()
        },
        async fetchDashboardData() {
            if (!this.canFetchCards) {
                this.resetDashboardData()
                return { kpiData: null, dashboardData: null }
            }

            const [kpiData, dashboardData] = await Promise.all([
                this.$store.dispatch('workplan/getConsolidationKeyResults', {
                    scope: this.scope,
                    relatedObjectId: this.relatedObjectParamValue
                }),
                this.$store.dispatch('workplan/getConsolidationDashboard', {
                    scope: this.scope
                })
            ])

            await this.fetchWidgetReportSettings(
                Array.isArray(dashboardData?.groups) ? dashboardData.groups : []
            )
            await this.fetchWidgetReports(
                Array.isArray(dashboardData?.groups) ? dashboardData.groups : [],
                { force: true }
            )

            return { kpiData, dashboardData }
        },
        async initializeView() {
            this.restoreFiltersFromStore()
            if (this.canFetchCards)
                await this.fetchDashboardData()
            else
                this.resetDashboardData()
            this.initialized = true
        }
    },
    created() {
        this.initializeView()
    },
    activated() {
        if (this.initialized)
            this.initializeView()
    }
}
</script>

<style lang="scss" scoped>
.consolidation{
    &__group{
        margin-top: 18px;
    }
}
</style>
