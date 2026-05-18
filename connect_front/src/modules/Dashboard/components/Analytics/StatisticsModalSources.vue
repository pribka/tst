<template>
    <a-modal
        v-model="modalVisible"
        :width="modalWidth"
        :footer="null"
        class="relative">
        <template v-if="loading">
            <a-spin class="custom_spinner"/>
        </template>
        <div 
            class="custom_opacity_transition"
            :class="loading && 'custom_opacity'">
            <div class="mb-4">
                <div class="text-lg">
                    {{ $t('dashboard.entraceSourceAnalytics') }}
                </div> 
            </div>
            <div 
                class="mb-2"
                :class="0">
                <AnalyticsFilters
                    :filters="filters"
                    @updateFilters="getAnalyticReports" />
            </div>
            <div class="flex">
                <Histogram
                    :analytics="analytics"
                    :series="[{ data: series }]"
                    :colors="colors" />
                <template v-if="windowWidth >= 1000">
                    <ChartPolarArea
                        :analytics="analytics"
                        :colors="colors"/>
                </template>
                <PercentageList
                    :class="windowWidth < 1000 && 'ml-4'"     
                    :analytics="analytics"
                    :colors="colors" />
            </div>
        </div>
    </a-modal>
</template>

<script>
import AnalyticsFilters from './AnalyticsFilters.vue'

import ChartPolarArea from './ChartPolarArea.vue'
import Histogram from './Histogram.vue'
import PercentageList from './PercentageList.vue'
export default {
    props: {
        analytics: {
            type: Array,
            default: () => []
        },
        filters: {
            type: Object,
            required: true
        },
        getAnalyticReports: {
            type: Function,
            default: () => {}
        },
        loading: {
            type: Boolean,
            default: false
        },
    },
    components: {
        AnalyticsFilters,
        ChartPolarArea,
        Histogram,
        PercentageList
    },
    data() {
        return {
            start: null,
            end: null,

            organizations: [],
            subOrganizations: [],
            selectOrganizationLoading: false,
            selectSubOrganizationLoading: false,
            selectedOrganization: [],
            selectedSubOrganization: [],

            modalVisible: false,
            series: [4, 2, 1, 582],
            legend: [
                this.$t('dashboard.legend_favorable'),
                this.$t('dashboard.legend_burdensome'),
                this.$t('dashboard.legend_response'),
                this.$t('dashboard.legend_terminated'),
                this.$t('dashboard.legend_noted'),
                this.$t('dashboard.legend_other'),
            ],
            colors: [
                '#067fd8',
                '#fa9800',
                '#9641e5',
                '#d341ee',
                '#00aeab',
                '#c2d88e',
                '#f7636f'
            ],
            organizationPage: 1,
            organizationNext: true,
            scrollLoading: false,

            subOrganizationPage: 1,
            subOrganizationNext: true,
            subScrollLoading: false,
            pageSize: 10
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        modalWidth() {
            if(this.windowWidth > 1100) {
                return 1000
            }
            return this.windowWidth * 0.8
        }
    },
    methods: {
        openModal() {
            this.modalVisible = true
        },
        closeModal() {
            this.modalVisible = false
        },
        updateFilters() {
            this.$emit('change', {
                organization: this.selectedOrganization,
                subOrganization: this.selectedSubOrganization,
                start: this.start,
                end: this.end,
                subOrganizations: {
                    subOrganizationPage: this.subOrganizationPage,
                    subOrganizationNext: this.subOrganizationNext,
                    subScrollLoading: this.subScrollLoading,
                    subOrganizations: this.subOrganizations,
                }
            })
        }
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
</style>