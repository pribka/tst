<template>
    <div>
        <div class="map_filters md:flex items-center">
            <a-spin 
                v-if="!isMobile"
                :spinning="summaryLoader" 
                size="small">
                <div style="font-size: 16px;color:#000;">
                    {{ $t('sports.mapCount') }}: {{ summaryLength }}
                </div>
            </a-spin>
            <a-form-model
                v-show="!isFullscreen"
                ref="filterForm"
                class="md:flex items-center md:ml-3"
                :model="filter">
                <div class="md:flex items-center">
                    <a-form-model-item ref="region" label="" prop="region" class="mb-2 md:mb-0 md:mr-2">
                        <a-select
                            v-model="filter.region"
                            size="large"
                            show-search
                            allowClear
                            :class="filter.region && 'val_selected'"
                            :placeholder="$t('sports.mapRegion')"
                            :filter-option="filterOption"
                            class="w-full filter_select">
                            <a-select-option v-for="item in regions" :value="item.id" :key="item.id">
                                {{ item.name }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                    <a-form-model-item ref="district" label="" prop="district" class="mb-0">
                        <a-select
                            v-model="filter.district"
                            size="large"
                            show-search
                            allowClear
                            :loading="districtLoading"
                            :placeholder="$t('sports.mapDistrict')"
                            :class="filter.district && 'val_selected'"
                            :disabled="filter.region ? false : true"
                            :filter-option="filterOption"
                            class="w-full filter_select">
                            <a-select-option v-for="item in districtsList" :value="item.id" :key="item.id">
                                {{ item.name }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                </div>
                <div class="md:flex items-center mt-3 md:mt-0 md:ml-2">
                    <a-button 
                        type="primary" 
                        size="large" 
                        :block="isMobile"
                        flaticon
                        icon="fi-rr-filter"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('sports.setFilter')"
                        @click="setFilter()">
                        <template v-if="isMobile">{{ $t('sports.setFilter') }}</template>
                    </a-button>
                    <a-button 
                        type="primary" 
                        size="large" 
                        ghost 
                        :block="isMobile"
                        class="mt-2 md:mt-0 md:ml-1"
                        flaticon
                        icon="fi-rr-filter-slash"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="$t('sports.clearFilter')"
                        @click="clearFilter()">
                        <template v-if="isMobile">{{ $t('sports.clearFilter') }}</template>
                    </a-button>
                </div>
            </a-form-model>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        isFullscreen: {
            type: Boolean,
            default: false
        },
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
        summaryLength: {
            type: Number,
            default: 0
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
        regions() {
            if(this.regionsCache?.length)
                return this.regionsCache
            return []
        },
        isMobile() {
            return this.$store.state.isMobile;
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
            filter: {
                region: null,
                district: null
            }
        }
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
                region: null,
                district: null
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
.filter_select{
    min-width: 100%;
    max-width: 100%;
    @media (min-width: 768px) {
        min-width: 200px;
        max-width: 200px;
    }
    &:not(.ant-select-open){
        &:not(.val_selected){
            &::v-deep{
                .ant-select-selection__placeholder{
                    display: block!important;
                }
            }
        }
    }
}
.map_filters{
    &::v-deep{
        .ant-form-item{
            max-height: 40px;
        }
    }
}
</style>