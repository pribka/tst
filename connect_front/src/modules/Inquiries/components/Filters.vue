<template>
    <div class="filters check_button mb-4 md:mb-5">
        <div class="filters__wrap">
            <div class="filters__block">
                <div class="filter_label">
                    {{ $t('inquiries.treatmentCategory') }}
                </div>
                <div class="flex items-center">
                    <div 
                        class="summary_item bg_white"
                        :class="summaryActive['white'] && 'active'"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_0')"
                        @click="setSummaryFilters('white')">
                        <span>{{ summaryWhite }}</span>
                    </div>
                    <div 
                        class="summary_item bg_yellow"
                        :class="summaryActive['yellow'] && 'active'"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_1_2')"
                        @click="setSummaryFilters('yellow')">
                        <span>{{ summaryYellow }}</span>
                    </div>
                    <div 
                        class="summary_item bg_orange"
                        :class="summaryActive['orange'] && 'active'"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_3_5')"
                        @click="setSummaryFilters('orange')">
                        <span>{{ summaryOrange }}</span>
                    </div>
                    <div 
                        class="summary_item bg_red"
                        :class="summaryActive['red'] && 'active'"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_6_10')"
                        @click="setSummaryFilters('red')">
                        <span>{{ summaryRed }}</span>
                    </div>
                </div>
                <div class="mt-1">
                    <span style="opacity: 0.6;">{{ $t('inquiries.total_request') }}:</span> {{ summaryTotal }}
                </div>
            </div>
            <div 
                v-if="isMobile" 
                class="filter_btn cursor-pointer"
                :class="filterShow && 'show_filters'"
                @click="filterShow = !filterShow">
                <span>{{ $t('inquiries.filters') }}</span>
                <i v-if="!filterShow" class="fi fi-rr-angle-down" />
                <i v-else class="fi fi-rr-angle-up" />
            </div>
            <template v-if="filtersVisible">
                <div class="filters__block">
                    <div class="filter_label">
                        {{ $t('inquiries.statusFilter') }}
                    </div>
                    <a-select 
                        :value="statusFilter"
                        :allowClear="statusFilter ? true : false" 
                        size="large"
                        @change="changeStatus">
                        <a-select-option value="new_inquiries" class="flex items-center">
                            <a-badge color="blue" /> {{ $t('inquiries.new') }}
                        </a-select-option>
                        <a-select-option value="processed_inquiries" class="flex items-center">
                            <a-badge color="green" /> {{ $t('inquiries.processed') }}
                        </a-select-option>
                        <template #suffixIcon>
                            <i class="fi fi-rr-angle-down" />
                        </template>
                    </a-select>
                </div>
                <div class="filters__block">
                    <div class="filter_label">
                        {{ $t('inquiries.dateFilter') }}
                    </div>
                    <a-popover 
                        trigger="click" 
                        destroyTooltipOnHide
                        overlayClassName="date_select_popover"
                        :placement="isMobile ? 'bottom' : 'bottomLeft'">
                        <div class="filter_cs_input ant-input ant-input-lg">
                            <div class="value">
                                {{ datesText }}
                            </div>
                            <div class="suffix_icon">
                                <a-button 
                                    v-if="filters.current_day || filters.current_month || filters.current_year || filters.period" 
                                    type="ui" 
                                    flaticon
                                    shape="circle"
                                    size="small"
                                    icon="fi-rr-cross-small"
                                    ghost
                                    @click="clearDateFilter()" />
                                <i v-else class="fi fi-rr-angle-down" />
                            </div>
                        </div>
                        <template #content>
                            <div class="md:flex items-center mb-3">
                                <a-button 
                                    type="primary" 
                                    class="mb-1 md:mb-0 md:mr-2"
                                    :block="isMobile"
                                    :ghost="filters.current_day ? false : true" 
                                    @click="currentDayFilterHandler()">
                                    {{ $t('inquiries.current_day') }}
                                </a-button>
                                <a-button 
                                    type="primary" 
                                    :ghost="filters.current_month ? false : true" 
                                    :block="isMobile"
                                    class="mb-1 md:mb-0 md:mr-2"
                                    @click="currentMonthFilterHandler()">
                                    {{ $t('inquiries.current_month') }}
                                </a-button>
                                <a-button 
                                    type="primary" 
                                    :ghost="filters.current_year ? false : true" 
                                    :block="isMobile"
                                    @click="currentYearFilterHandler()">
                                    {{ $t('inquiries.current_year') }}
                                </a-button>
                            </div>
                            <div>
                                <a-config-provider :locale="ruRU">
                                    <template v-if="isMobile">
                                        <a-date-picker
                                            class="w-full mb-2"
                                            v-model="periodStart"
                                            :locale="locale"
                                            :getPopupContainer="trigger => trigger.parentElement"
                                            :placeholder="$t('inquiries.period_start')"
                                            format="DD.MM.YYYY"
                                            @change="periodChange" />
                                        <a-date-picker
                                            class="w-full"
                                            v-model="periodEnd"
                                            :locale="locale"
                                            :getPopupContainer="trigger => trigger.parentElement"
                                            :placeholder="$t('inquiries.period_end')"
                                            format="DD.MM.YYYY"
                                            @change="periodChange" />
                                    </template>
                                    <a-range-picker
                                        v-else
                                        v-model="periodRange"
                                        :locale="locale"
                                        :getPopupContainer="trigger => trigger.parentElement"
                                        :placeholder="[$t('inquiries.start'), $t('inquiries.end')]"
                                        format="DD.MM.YYYY"
                                        @change="periodChange" />
                                </a-config-provider>
                            </div>
                        </template>
                    </a-popover>
                </div>
                <div class="filters__block">
                    <div class="filter_label">
                        {{ $t('inquiries.orgFilter') }}
                    </div>
                    <a-select 
                        v-model="organizationsFilter" 
                        size="large"
                        @change="handleOrganizationsFilterChange">
                        <a-select-option value="only_my">
                            {{ $t('inquiries.organization') }}
                        </a-select-option>
                        <a-select-option value="all">
                            {{ $t('inquiries.with_departments') }}
                        </a-select-option>
                        <a-select-option value="descendants">
                            {{ $t('inquiries.departments_only') }}
                        </a-select-option>
                        <template #suffixIcon>
                            <i class="fi fi-rr-angle-down" />
                        </template>
                    </a-select>
                </div>
            </template>
        </div>
        <div 
            v-if="filtersVisible" 
            class="filters__wrap">
            <div class="filters__block">
                <div class="filter_label">
                    {{ $t('inquiries.sortList') }}
                </div>
                <a-select
                    v-model="ordering"
                    :allowClear="ordering ? true : false"
                    size="large"
                    @change="handleOrderingChange">
                    <a-select-option 
                        v-for="option in sortOptions" 
                        :key="option.value" 
                        class="flex items-center"
                        :value="option.value">
                        <i class="fi mr-2" :class="option.icon" />
                        {{ option.label }}
                    </a-select-option>
                    <template #suffixIcon>
                        <i class="fi fi-rr-angle-down" />
                    </template>
                </a-select>
            </div>
        </div>
    </div>
</template>

<script>
let summaryTimer;
import ruRU from 'ant-design-vue/es/locale/ru_RU'
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
export default {
    props: {
        setFilters: {
            type: Function,
            default: () => {}
        },
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        summary: {
            type: Object,
            default: () => null
        },
        setSummary: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        datesText() {
            if(this.filters.current_month || this.filters.current_year || this.filters.period || this.filters.current_day) {
                if(this.filters.current_day)
                    return this.$t('inquiries.current_day')
                if(this.filters.current_month)
                    return this.$t('inquiries.current_month')
                if(this.filters.current_year)
                    return this.$t('inquiries.current_year')
                if(this.filters.period) {
                    if(this.periodStart && this.periodEnd)
                        return `${this.$moment(this.periodStart).format('DD.MM.YYYY')} - ${this.$moment(this.periodEnd).format('DD.MM.YYYY')}`
                }
            }
            return ''
        },
        filterActive() {
            return this.$store.state.filter.filterActive[this.page_name]
        },
        summaryTotal() {
            return this.summary?.total || 0
        },
        summaryWhite() {
            return this.summary?.white || 0
        },
        summaryYellow() {
            return this.summary?.yellow || 0
        },
        summaryOrange() {
            return this.summary?.orange || 0
        },
        summaryRed() {
            return this.summary?.red || 0
        },
        filtersVisible() {
            if(this.isMobile)
                return this.filterShow
            return true
        }
    },
    data() {
        return {
            locale,
            ruRU,
            statusFilter: null,
            filters: {
                current_month: false,
                current_year: false,
                current_day: false,
                period: false,
                processed_inquiries: false,
                new_inquiries: false,
                organizations: false,
                total_value_filter: false
            },
            organizationsFilter: null,
            sortOptions: [
                {
                    label: this.$t('inquiries.sortByNumberAsc'),
                    value: 'issue__number',
                    icon: 'fi-rr-sort-alpha-down'
                },
                {
                    label: this.$t('inquiries.sortByNumberDesc'),
                    value: '-issue__number',
                    icon: 'fi-rr-sort-alpha-up'
                },
                {
                    label: this.$t('inquiries.sortNewestFirst'),
                    value: '-issue__issue_date',
                    icon: 'fi-rr-sort-numeric-down'
                },
                {
                    label: this.$t('inquiries.sortOldestFirst'),
                    value: 'issue__issue_date',
                    icon: 'fi-rr-sort-numeric-down-alt'
                }
            ],
            ordering: null,
            periodStart: null,
            periodEnd: null,
            loading: false,
            periodRange: [null, null],
            summaryActive: {},
            filterShow: false
        }
    },
    created() {
        this.filtersInit()
    },
    methods: {
        clearDateFilter() {
            this.filters['current_month'] = false
            this.filters['current_year'] = false
            this.filters['current_day'] = false
            this.filters['period'] = false
            this.periodStart = null
            this.periodEnd = null
            this.periodRange = [null, null]
            this.filterHandle()
        },
        filterHandle() {
            this.setFilters({
                filters: this.filters, 
                organizationsFilter: this.organizationsFilter, 
                summaryActive: this.summaryActive, 
                periodStart: this.periodStart, 
                periodEnd: this.periodEnd
            })
        },
        handleOrderingChange() {
            this.$store.commit('filter/SET_FILTERS_ORDERING', {
                name: this.page_name,
                value: this.ordering ? [this.ordering,] : []
            })
            this.filterHandle()
        },
        handleOrganizationsFilterChange(value) {
            this.filters['organizations'] = ['only_my', 'descendants'].includes(value)
            this.filterHandle()
        },
        changeStatus(value) {
            this.statusFilter = value
            if(!value) {
                this.filters['new_inquiries'] = false
                this.filters['processed_inquiries'] = false
            } else {
                if(value === 'new_inquiries') {
                    this.filters['new_inquiries'] = true
                    this.filters['processed_inquiries'] = false
                }
                if(value === 'processed_inquiries') {
                    this.filters['new_inquiries'] = false
                    this.filters['processed_inquiries'] = true
                }
            }
            this.filterHandle()
        },
        setSummaryFilters(type) {
            if(this.summaryActive?.[type])
                this.$delete(this.summaryActive, type)
            else
                this.$set(this.summaryActive, type, true)

            clearTimeout(summaryTimer)
            summaryTimer = setTimeout(() => {
                this.filterHandle()
            }, 600)
        },
        getSummary() {
            try {
                const params = {
                    page_name: this.page_name,
                    organizations: this.organizationsFilter
                }
                this.$http.get('/risk_assessment/summary/', {
                    params
                })
                    .then(({ data }) => {
                        this.setSummary(data)
                    })
                    .catch(error => {
                        console.error(error)
                    })
            } catch(e) {
                console.log(e)
            }
        },
        async filtersInit() {
            try {
                this.loading = true

                let params = {
                    model: this.model,
                    page_name: this.page_name
                }

                const { data } = await this.$http.get('/app_info/active_filters/', {
                    params
                })
                if(data) {
                    if('total_value_filter' in data.activeFilters && data.activeFilters['total_value_filter'].active) {
                        if(data.activeFilters['total_value_filter']?.values?.value?.length) {
                            data.activeFilters['total_value_filter'].values.value.forEach(item => {
                                this.$set(this.summaryActive, item, true)
                            })
                        }
                    }
                    if('issue_date_filter' in data.activeFilters && data.activeFilters['issue_date_filter'].active) {
                        if(data.activeFilters['issue_date_filter'].values.start === this.$moment().startOf('month').format('YYYY-MM-DD') && data.activeFilters['issue_date_filter'].values.end === this.$moment().endOf('month').format('YYYY-MM-DD')) {
                            this.filters['current_month'] = true
                        } else if(data.activeFilters['issue_date_filter'].values.start === this.$moment().startOf('year').format('YYYY-MM-DD') && data.activeFilters['issue_date_filter'].values.end === this.$moment().endOf('year').format('YYYY-MM-DD')) {
                            this.filters['current_year'] = true
                        } else if(this.$moment(data.activeFilters['issue_date_filter'].values.start).format('YYYY-MM-DD') === this.$moment().format('YYYY-MM-DD') && this.$moment(data.activeFilters['issue_date_filter'].values.end).format('YYYY-MM-DD') === this.$moment().format('YYYY-MM-DD')) {
                            this.filters['current_day'] = true
                        } else {
                            this.filters['period'] = true
                            this.periodRange = [
                                this.$moment(data.activeFilters['issue_date_filter'].values.start),
                                this.$moment(data.activeFilters['issue_date_filter'].values.end)
                            ]
                            this.periodStart = this.$moment(data.activeFilters['issue_date_filter'].values.start)
                            this.periodEnd = this.$moment(data.activeFilters['issue_date_filter'].values.end)
                        }
                    }
                    if('status' in data.activeFilters && data.activeFilters['status'].active)
                        if(data.activeFilters['status'].values.value[0] === 'new') {
                            this.statusFilter = 'new_inquiries'
                            this.filters['new_inquiries'] = true
                        } else if(data.activeFilters['status'].values.value[0] === 'processed') {
                            this.statusFilter = 'processed_inquiries'
                            this.filters['processed_inquiries'] = true
                        }
                    if('organizations_filter' in data.activeFilters && data.activeFilters['organizations_filter'].active) {
                        this.organizationsFilter = data.activeFilters['organizations_filter'].values.value
                    } else {
                        this.organizationsFilter = 'all'
                    }
                    if(data?.ordering.length) {
                        this.ordering = data.ordering[0]
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        currentDayFilterHandler() {
            this.filters.current_day = !this.filters.current_day
            if(this.filters.current_day) {
                if(this.filters['current_year'])
                    this.filters['current_year'] = false
                if(this.filters['current_month'])
                    this.filters['current_month'] = false
                if(this.filters['period']) {
                    this.filters['period'] = false
                    this.periodStart = null
                    this.periodEnd = null
                    this.periodRange = [null, null]
                }
            }
            this.filterHandle()
        },
        currentMonthFilterHandler() {
            this.filters.current_month = !this.filters.current_month
            if(this.filters.current_month) {
                if(this.filters['current_year'])
                    this.filters['current_year'] = false
                if(this.filters['current_day'])
                    this.filters['current_day'] = false
                if(this.filters['period']) {
                    this.filters['period'] = false
                    this.periodStart = null
                    this.periodEnd = null
                    this.periodRange = [null, null]
                }
            }
            this.filterHandle()
        },
        currentYearFilterHandler() {
            this.filters.current_year = !this.filters.current_year
            if(this.filters.current_year) {
                if(this.filters['current_month'])
                    this.filters['current_month'] = false
                if(this.filters['current_day'])
                    this.filters['current_day'] = false
                if(this.filters['period']) {
                    this.filters['period'] = false
                    this.periodStart = null
                    this.periodEnd = null
                    this.periodRange = [null, null]
                }
            }
            this.filterHandle()
        },
        periodChange(dates, type) {
            if(this.isMobile) {
                this.filters.period = true
                this.filters.current_month = false
                this.filters.current_year = false
                if(this.periodStart && this.periodEnd) {
                    if(this.periodStart >= this.periodEnd) {
                        this.$message.error('Период задан некорректно!')
                        return
                    }
                    this.filterHandle()
                }
            } else {
                if(dates.length) {
                    this.filters.period = true
                    this.filters.current_day = false
                    this.filters.current_month = false
                    this.filters.current_year = false
                    this.periodStart = dates[0]
                    this.periodEnd = dates[1]
                    if(this.periodStart && this.periodEnd)
                        this.filterHandle()
                } else {
                    this.filters.period = false
                    this.periodStart = null
                    this.periodEnd = null
                    this.periodRange = [null, null]
                    this.filterHandle()
                }
            }
        }
    }
}
</script>

<style lang="scss">
.date_select_popover{
    .ant-popover-inner-content{
        padding: 18px;
    }
    .ant-popover-inner{
        box-shadow: initial;
        border: 1px solid #D9D9D9;
        border-radius: 4px;
    }
    .ant-popover-arrow{
        display: none;
    }
}
</style>

<style lang="scss" scoped>
.filter_btn{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 10px;
    &.show_filters{
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #EFF2F5;
    }
}
.summary_item {
    height: 45px;
    min-width: 45px;
    padding: 2px 8px;
    border-radius: 4px;
    text-align: center;
    font-size: 16px;
    line-height: 40px;
    position: relative;
    overflow: hidden;
    border: 1px solid transparent;
    user-select: none;
    cursor: pointer;
    color:#000;
    span{
        position: relative;
        z-index: 5;
    }
    &.bg_white{
        background-color: #F4F4F4;
        border-color: #A9B3BF;
    }
    &.bg_yellow{
        background-color: #fbf7d3;
        border-color: #fee933;
    }
    &.bg_orange{
        background-color: #fcf1e7;
        border-color: #ff8812;
    }
    &.bg_red{
        background-color: #f5e3e2;
        border-color: #ff4e46;
    }
    &.active{
        &.bg_white{
            background-color: #A9B3BF;
        }
        &.bg_yellow{
            background-color: #fee933;
        }
        &.bg_orange{
            background-color: #ff8812;
        }
        &.bg_red{
            background-color: #ff4e46;
        }
    }
    &:not(:last-child) {
        margin-right: 5px;
    }
}
.filters{
    line-height: 1.6;
    color: #000;
    border-radius: 10px;
    padding: 15px;
    background: #fff;
    @media (min-width: 768px) {
        min-height: 80.5px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
    }
    .filter_label{
        opacity: 0.6;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .set_period {
        display: inline;
        .ant-calendar-picker{
            margin-top: 8px;
        }
    }
    .ordering {
        display: inline;
        margin-right: 8px;
        .select{
            width: 150px;
        }
    }
    .filters__block{
        &:not(:last-child){
            margin-bottom: 10px;
            @media (min-width: 768px) {
                margin-bottom: 0px;
                margin-right: 10px;
            }
            @media (min-width: 1400px) {
                margin-right: 20px;
            }
        }
        .filter_cs_input{
            width: 100%;
            user-select: none;
            cursor: pointer;
            @media (min-width: 768px) {
                min-width: 200px;
                max-width: 200px;
            }
            @media (min-width: 1400px) {
                min-width: 240px;
                max-width: 240px;
            }
            @media (min-width: 1550px) {
                min-width: 280px;
                max-width: 280px;
            }
            &.ant-input{
                &.ant-input-lg{
                    display: flex;
                    align-items: center;
                    height: 45px;
                }
            }
            .suffix_icon{
                display: inline-block;
                color: inherit;
                font-style: normal;
                line-height: 0;
                text-align: center;
                text-transform: none;
                vertical-align: -0.125em;
                text-rendering: optimizeLegibility;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                position: absolute;
                top: 50%;
                right: 11px;
                margin-top: -6px;
                color: rgba(0, 0, 0, 0.25);
                font-size: 12px;
                line-height: 1;
                transform-origin: 50% 50%;
                &::v-deep{
                    .ant-btn{
                        margin-top: -5px;
                        margin-right: -5px;
                    }
                }
            }
        }
        &::v-deep{
            .ant-select{
                width: 100%;
                @media (min-width: 768px) {
                    min-width: 200px;
                    max-width: 200px;
                }
                @media (min-width: 1400px) {
                    min-width: 240px;
                    max-width: 240px;
                }
                @media (min-width: 1550px) {
                    min-width: 280px;
                    max-width: 280px;
                }
                &.ant-select-lg{
                    .ant-select-selection--single{
                        height: 45px;
                        .ant-select-selection__rendered{
                            line-height: 45px;
                        }
                    }
                }
            }
        }
    }
    &__wrap{
        @media (max-width: 767.98px) {
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
        @media (min-width: 768px) {
            display: flex;
            align-items: flex-start;
        }
    }
}
</style>