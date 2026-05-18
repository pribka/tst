<template>
    <div>
        <div class="map_filters">
            <a-spin 
                :spinning="summaryLoader" 
                size="small">
                <div class="mb-2 blue_color" style="font-size: 16px;">
                    {{ $t('Total') }}: {{ summary ? summary.total : 0 }}
                </div>
                <div class="mb-2" style="color:#000;">{{ $t('Select the categories you are interested in') }}</div>
                <div class="flex items-center mb-4">
                    <div 
                        class="summary_item bg_white" 
                        :class="checkType('white')" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_0')"
                        @click="selectType('white')">
                        {{ summary && summary.white ? summary.white : 0 }}
                    </div>
                    <div 
                        class="summary_item bg_yellow" 
                        :class="checkType('yellow')" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_1_2')"
                        @click="selectType('yellow')">
                        {{ summary && summary.yellow ? summary.yellow : 0 }}
                    </div>
                    <div 
                        class="summary_item bg_orange" 
                        :class="checkType('orange')" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_3_5')"
                        @click="selectType('orange')">
                        {{ summary && summary.orange ? summary.orange : 0 }}
                    </div>
                    <div 
                        class="summary_item bg_red" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('inquiries.points_6_10')"
                        :class="checkType('red')" 
                        @click="selectType('red')">
                        {{ summary && summary.red ? summary.red : 0 }}
                    </div>
                </div>
            </a-spin>
            <a-form-model
                ref="filterForm"
                :model="filter">
                <div class="grid gap-2 grid-cols-2">
                    <a-form-model-item ref="issue_date_gte" :label="$t('Start date')" prop="issue_date_gte" class="mb-2">
                        <a-date-picker 
                            v-model="filter.issue_date_gte" 
                            :placeholder="$t('Select date')"
                            size="large" />
                    </a-form-model-item>
                    <a-form-model-item ref="issue_date_lte" :label="$t('Finish date')" prop="issue_date_lte" class="mb-2">
                        <a-date-picker 
                            v-model="filter.issue_date_lte" 
                            :placeholder="$t('Select date')"
                            size="large" />
                    </a-form-model-item>
                </div>
                <a-form-model-item ref="categories" :label="$t('Categories')" prop="categories" class="mb-2">
                    <a-tree-select
                        v-model="filter.categories"
                        size="large"
                        tree-data-simple-mode
                        style="width: 100%"
                        multiple
                        allowClear
                        dropdownClassName="select-none"
                        :dropdown-style="{ maxHeight: '300px', overflowY: 'auto', maxWidth: '300px' }"
                        :tree-data="categoryTree"
                        :placeholder="$t('Categories', { count: categoryTree.length })"
                        :load-data="onLoadData"/>
                </a-form-model-item>
                <div class="grid gap-2 grid-cols-2">
                    <a-form-model-item ref="region" :label="$t('Regions')" prop="region" class="mb-4">
                        <a-select
                            v-model="filter.region"
                            size="large"
                            show-search
                            allowClear
                            :filter-option="filterOption"
                            class="w-full">
                            <a-select-option v-for="item in regions" :value="item.id" :key="item.id">
                                {{ item.name }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                    <a-form-model-item ref="district" :label="$t('Districts')" prop="district" class="mb-4">
                        <a-select
                            v-model="filter.district"
                            size="large"
                            show-search
                            allowClear
                            :loading="districtLoading"
                            :disabled="filter.region ? false : true"
                            :filter-option="filterOption"
                            class="w-full">
                            <a-select-option v-for="item in districtsList" :value="item.id" :key="item.id">
                                {{ item.name }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                </div>
                <a-button 
                    type="primary" 
                    size="large" 
                    class="mb-2"
                    block
                    @click="setFilter()">
                    {{ $t('Apply Filter') }}
                </a-button>
                <a-button 
                    type="primary" 
                    size="large" 
                    ghost 
                    block
                    @click="clearFilter()">
                    {{ $t('Clear Filter') }}
                </a-button>
            </a-form-model>
        </div>
        <a-spin 
            :spinning="inquiriesLoading" 
            class="w-full mt-4"
            size="small">
            <div v-if="inquiries" class="inquiries_card cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="circle" :class="!inquiries.total_value && 'circle-border'" :style="{ backgroundColor: circleColor(inquiries.total_value) }">
                        <span>{{ inquiries.total_value }}</span>
                    </div>
                    <div class="flex items-center more_link" @click="openInquires()">
                        {{ $t('Go to inquiry') }} <i class="fi fi-rr-arrow-up-right ml-2 blue_color" style="font-size: 9px;" />
                    </div>
                </div>
                <div v-if="inquiries.organization" class="blue_color mb-3">
                    {{ inquiries.organization.name }}
                </div>
                <div v-if="inquiries.issue.number" class="card_row">
                    <span class="label">{{ $t('Inquiry Number') }}:</span>
                    <span class="val">{{ inquiries.issue.number }}</span>
                </div>
                <div v-if="inquiries.issue.issue_date" class="card_row">
                    <div class="label">{{ $t('Inquiry Date') }}:</div>
                    <div class="val">{{ $moment(inquiries.issue.issue_date).format('DD MMMM YYYY') }}</div>
                </div>
                <div v-if="inquiries.issue.issue_category" class="card_row">
                    <span class="label">{{ $t('Inquiry Category') }}:</span> {{ fullCategoryName(inquiries.issue.issue_category) }}
                </div>
                <template v-if="inquiries.location_points && inquiries.location_points.length">
                    <div v-for="(location, index) in inquiries.location_points" :key="location.id" class="card_row">
                        <span v-if="index === 0" class="label"><i class="fi fi-rr-marker mr-1"/> {{ $t('Location') }}:</span> {{ location.address }}
                    </div>
                </template>
            </div>
        </a-spin>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        mapData: {
            type: Array,
            default: () => []
        },
        getData: {
            type: Function,
            default: () => {}
        },
        getMapCenter: {
            type: Function,
            default: () => {}
        },
        regionsCache: {
            type: Array,
            default: () => []
        },
        setFilters: {
            type: Function,
            default: () => {}
        },
        districts: {
            type: Array,
            default: () => []
        },
        summaryData: {
            type: Object,
            default: () => null
        },
        summaryLoader: {
            type: Boolean,
            default: false
        },
        clearFilters: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        summary() {
            if(this.summaryData)
                return this.summaryData
            return {
                white: 0,
                orange: 0,
                yellow: 0,
                red: 0,
                total: 0
            }
        },
        regions() {
            if(this.regionsCache?.length)
                return this.regionsCache
            return []
        },
        districtsOpts() {
            if(this.districts?.length)
                return this.districts
            return this.districtsList
        }
    },
    data() {
        return {
            districtLoading: false,
            districtsList: [],
            categoryTree: [],
            inquiries: null,
            inquiriesLoading: false,
            filter: {
                issue_date_gte: null,
                issue_date_lte: null,
                categories: [],
                region: null,
                district: null,
                total_value: []
            }
        }
    },
    created() {
        this.getCategories()
    },
    watch: {
        'filter.region'(val) {
            if(val)
                this.changeRegion(val)
            else
                this.districtsList = []
        }
    },
    methods: {
        openInquires() {
            eventBus.$emit('view_inquiries', this.inquiries)
        },
        fullCategoryName(issue_category) {
            const buildFullName = (category, names = []) => {
                if (!category) {
                    return names
                }
                names.unshift(category.name)
                return buildFullName(category.issue_category, names)
            }
            return buildFullName(issue_category).join('/')
        },
        circleColor(total_value) {
            if (total_value >= 1 && total_value <= 2) {
                return '#fee933'
            } else if (total_value >= 3 && total_value <= 5) {
                return '#ff8812'
            } else if (total_value >= 5) {
                return '#ff4e46'
            } else {
                return '#A9B3BF'
            }
        },
        async getInfo(item) {
            try {
                this.inquiriesLoading = true
                const { data } = await this.$http.get(`/risk_assessment/${item.id}/`)
                if(data)
                    this.inquiries = data
            } catch(e) {
                console.log(e)
            } finally {
                this.inquiriesLoading = false
            }
        },
        onLoadData(treeNode) {
            return new Promise((resolve, reject) => {
                const { id, loaded } = treeNode.dataRef
                if(!loaded) {
                    this.$http.get('/app_info/select_list/', {
                        params: {
                            model: 'risk_assessment.IssueCategoryModel', 
                            parent: id
                        }
                    })
                        .then(({data}) => {
                            if(data?.selectList?.length) {
                                const index = this.categoryTree.findIndex(f => f.value === id)
                                if(index !== -1) {
                                    this.$set(this.categoryTree[index], 'loaded', true)
                                }
                                this.categoryTree = this.categoryTree.concat(data.selectList.map(item => {
                                    return {
                                        ...item,
                                        value: item.id,
                                        title: item.string_view,
                                        pId: id,
                                        loaded: false
                                    }
                                }))
                            }
                            resolve()
                        })
                        .catch(e => {
                            console.log(e)
                            reject()
                        })
                }
                resolve()
            })
        },
        async getCategories() {
            try {
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'risk_assessment.IssueCategoryModel', 
                        parent: 'root'
                    }
                })
                if(data?.selectList?.length) {
                    this.categoryTree = data.selectList.map(item => {
                        return {
                            ...item,
                            value: item.id,
                            title: item.string_view,
                            pId: 0,
                            loaded: false
                        }
                    })
                }
            } catch(e) {
                console.log(e)
            }
        },
        checkType(type) {
            const find = this.filter.total_value.find(f => f === type)
            return find ? 'selected' : ''
        },
        selectType(type) {
            const index = this.filter.total_value.findIndex(f => f === type)
            if(index !== -1)
                this.filter.total_value.splice(index, 1)  
            else
                this.filter.total_value.push(type)
        },
        async changeRegion(region) {
            try {
                this.districtLoading = true
                const { data } = await this.$http.get('/catalogs/location_admin_area/', { 
                    params: {
                        parent: region
                    }
                })
                if(data) {
                    this.districtsList = data
                }
            } catch(e) {
                console.log(e)
                this.districtsList = []
            } finally {
                this.districtLoading = false
            }
        },
        setFilter() {
            this.inquiries = null
            this.setFilters(this.filter)
            this.getMapCenter()
        },
        filterOption(input, option) {
            return (
                option.componentOptions.children[0].text.toLowerCase().indexOf(input.toLowerCase()) >= 0
            )
        },
        setRegion(value) {
            this.inquiries = null
            this.filter.region = value
        },
        setDistrict(value) {
            this.inquiries = null
            this.filter.district = value
        },
        clearFilter() {
            this.filter = {
                issue_date_gte: null,
                issue_date_lte: null,
                categories: [],
                region: null,
                district: null,
                total_value: []
            }
            this.inquiries = null
            this.districtsList = []
            this.setFilters({})
            this.clearFilters()
            this.getMapCenter()
        }
    }
}
</script>

<style lang="scss" scoped>
.inquiries_card{
    background: #edf2fc;
    border: 1px solid #1D65C0;
    border-radius: 8px;
    padding: 15px;
    .card_row{
        color: #000;
        .label{
            color: #5f6165;
            margin-right: 5px;
            white-space: nowrap;
            display: flex;
            float: left;
            align-items: center;
            .fi{
                color: var(--blue);
            }
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
    .circle {
        min-width: 40px;
        padding: 2px 8px;
        border-radius: 99999px;
        font-weight: 500;
        text-align: center;
        font-size: 0.875rem;
        position: relative;
        overflow: hidden;
        border: 1px solid transparent;
        -webkit-user-select: none;
        -moz-user-select: none;
        user-select: none;
        cursor: pointer;
        color: #000;
        border: 1px solid transparent;
    }
    .circle-border{
        border: var(--bgColor6) solid 1px; 
    }
    .more_link{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
    }
}
.map_filters{
    background: #FAFAFA;
    border-radius: 8px;
    padding: 15px;
    .summary_item{
        min-width: 40px;
        padding: 2px 8px;
        border-radius: 99999px;
        font-weight: 500;
        text-align: center;
        font-size: 0.875rem;
        position: relative;
        overflow: hidden;
        border: 1px solid transparent;
        -webkit-user-select: none;
        -moz-user-select: none;
        user-select: none;
        cursor: pointer;
        color: #000;
        border: 1px solid transparent;
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
        &.selected{
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
        &:not(:last-child){
            margin-right: 7px;
        }
    }
}
</style>