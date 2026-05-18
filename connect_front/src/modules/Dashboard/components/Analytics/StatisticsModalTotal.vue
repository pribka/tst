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
                    {{ $t('dashboard.totalAppeals') }}
                </div> 
                <div class="text-4xl font-semibold">
                    {{ appealsTotal }}
                </div>
            </div>
            <div class="mb-2">
                <AnalyticsFilters
                    :filters="filters"
                    @updateFilters="getAnalyticReports" />
            </div>
            <div class="flex">
                <PercentageList 
                    :analytics="analytics"
                    :colors="colors" />
        
                <Chart
                    :analytics="analytics"/>
            </div>
        </div>
    </a-modal>
</template>

<script>
import AnalyticsFilters from './AnalyticsFilters.vue'

import Chart from '../Chart.vue'
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
        Chart,
        PercentageList,
    },
    data() {
        return {


            modalVisible: false,
          
            colors: [
                '#067fd8',
                '#fa9800',
                '#9641e5',
                '#d341ee',
                '#00aeab',
                '#c2d88e',
                '#f7636f'
            ],
        
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        modalWidth() {
            if(this.windowWidth > 1200) {
                return 1000
            }
            return this.windowWidth * 0.8
        },
        appealsTotal() {
            return this.getTotal()
        },
    },
    methods: {
        openModal() {
            this.modalVisible = true
        },
        closeModal() {
            this.modalVisible = false
        },
        getTotal() {
            if(this.analytics?.length)
                return this.analytics.reduce((total, current) => total + current.value, 0) || 0
            return 0
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

<style lans="scss" scoped>

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