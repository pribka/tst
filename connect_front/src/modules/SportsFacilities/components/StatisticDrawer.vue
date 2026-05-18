<template>
    <a-drawer
        ref="reesterStatDrawer"
        :title="$t('sports.repairStat')"
        placement="right"
        :width="drawerWidth"
        :visible="visible"
        wrapClassName="sports_stat_drawer"
        destroyOnClose
        @close="visible = false">
        <template v-if="statInfo">
            <div class="grid gap-7 grid-cols-1 md:grid-cols-2 mb-7">
                <div class="stat_card">
                    <div class="stat_card__head">
                        <div class="lbl">
                            {{ $t('sports.all_object') }}
                        </div>
                        <div class="g_bal">
                            {{ statInfo.count }} {{ $t('sports.un') }}
                        </div>
                    </div>
                    <div v-for="item in ownershipForms" :key="item.ownership_form.id" class="stat_row">
                        <div class="row_info">
                            <div class="row_label">{{ item.ownership_form.name }}</div>
                            <div class="row_value">{{ item.count }} ({{ item.percent }}%)</div>
                        </div>
                        <a-progress 
                            :percent="item.percent" 
                            :strokeWidth="21"
                            :strokeColor="item.color"
                            :show-info="false" />
                    </div>
                </div>
                <div class="stat_card">
                    <div class="stat_card__head">
                        <div class="lbl">
                            {{ $t('sports.repair_price') }}
                        </div>
                        <div class="g_bal">
                            {{ statInfo.renovation_info ? priceFormatter(statInfo.renovation_info.amount_sum) : 0 }} {{ $t('sports.tg') }}
                        </div>
                    </div>
                    <template v-if="renovation_info && renovation_info.length">
                        <div v-for="info in renovation_info" :key="info.code" class="stat_row">
                            <div class="row_info">
                                <div class="row_label">{{ info.name }}</div>
                                <div class="row_value">{{ priceFormatter(info.amount_sum) }} ({{info.percent}}%)</div>
                            </div>
                            <a-progress 
                                :percent="info.percent" 
                                :strokeWidth="21"
                                :strokeColor="info.color"
                                :show-info="false" />
                        </div>
                    </template>
                </div>
            </div>
            <div class="stat_card md:flex">
                <div class="stat_left flex md:block justify-center">
                    <apexchart
                        :key="apexchartKey"
                        type="donut" 
                        :options="chartOptions" 
                        class="chart"
                        :width="chartSize.width"
                        :height="chartSize.height"
                        :series="facilityTypesSeries" />
                </div>
                <div class="stat_right md:pl-8 mt-4 md:mt-0">
                    <div class="grid gap-4 grid-cols-2 xl:grid-cols-3">
                        <div v-for="item in facilityTypes" :key="item.id" class="stat_value_item">
                            <div>
                                <div class="crc" :style="`background:${item.color};`" />
                            </div>
                            <div class="info">
                                <div class="name">{{ item.title }}</div>
                                <div class="val">{{ item.value }} ({{ item.percentage }}%)</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </template>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import VueApexCharts from 'vue-apexcharts'
import { priceFormatter } from '@/utils/index'
export default {
    components: {
        apexchart: VueApexCharts
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        facilityTypes() {
            if (!this.statInfo.facility_types || !Array.isArray(this.statInfo.facility_types))
                return []
            const colors = this.chartOptions.colors
            const total = this.statInfo.facility_types.reduce((sum, item) => sum + (item.count || 0), 0)
            return this.statInfo.facility_types.map((item, index) => ({
                title: item.facility_type?.full_name || this.$t('sports.not_specified2'),
                value: item.count || 0,
                id: item.facility_type.id,
                percentage: total > 0 ? +(item.count / total * 100).toFixed(2) : 0,
                color: colors[index % colors.length]
            }))
        },
        facilityTypesSeries() {
            return this.statInfo.facility_types.map(item => item.count)
        },
        facilityTypesLabels() {
            return this.statInfo.facility_types.map(item => item.facility_type.full_name || item.facility_type.name)
        },
        ownershipForms() {
            const colors = this.strokeColor
            const total = this.statInfo.ownership_forms.reduce((sum, item) => sum + item.count, 0)

            return this.statInfo.ownership_forms.map((item, index) => ({
                ...item,
                percent: total > 0 ? +(item.count / total * 100).toFixed(2) : 0,
                color: colors[index % colors.length]
            }))
        },
        renovation_info() {
            const colors = this.strokeColor
            const total = this.statInfo.renovation_info.renovation_types.reduce((sum, item) => sum + item.amount_sum, 0)

            return this.statInfo.renovation_info.renovation_types.map((item, index) => ({
                ...item,
                percent: total > 0 ? +(item.amount_sum / total * 100).toFixed(2) : 0,
                color: colors[index % colors.length]
            }))
        },
        chartSize() {
            if(this.windowWidth < 1800) {
                if(this.windowWidth < 1650) {
                    if(this.windowWidth < 768) {
                        return {
                            width: '230px',
                            height: '230px'
                        }
                    } else {
                        return {
                            width: '220px',
                            height: '220px'
                        }
                    }
                } else {
                    return {
                        width: '220px',
                        height: '220px'
                    }
                }
            } else {
                return {
                    width: '230px',
                    height: '230px'
                }
            }
        },
        drawerWidth() {
            if(this.windowWidth > 975)
                return 975
            else {
                return '100%'
            }
        },
        chartOptions() {
            return {
                stroke: {
                    width: 0
                },
                legend: {
                    show: false
                },
                colors: [
                    "#DDA0DD", "#800080", "#ADD8E6", "#FFA500",
                    "#FFB6C1", "#A52A2A", "#DDA0DD", "#800080", "#ADD8E6", 
                    "#FFA500", "#FFFFE0", "#FFB6C1", "#A52A2A", "#DDA0DD", 
                    "#800080", "#ADD8E6", "#FFA500", "#FFFFE0", "#FFB6C1", 
                    "#A52A2A", "#DDA0DD", "#800080", "#ADD8E6", "#FFA500"
                ],
                dataLabels: {
                    enabled: false,
                    value: {
                        formatter(value) {
                        // eslint-disable-next-line radix
                            return `${parseInt(value)}%`
                        }
                    },
                    style: {
                        fontSize: '10px',
                        colors: ['#333']
                    },
                    dropShadow: {
                        enabled: false
                    }
                },
                chart: {
                    foreColor: '#000'
                },
                plotOptions: {
                    pie: {
                        customScale: 1,
                        startAngle: 1,
                        donut: {
                            size:'87%',
                            labels: {
                                show: true,
                                name: {
                                    fontSize: '2rem',
                                    color: '#000',
                                    offsetY: 20,
                                    formatter: value => {
                                        if(typeof value === 'object')
                                            return value
                                        if(value.length >= 26)
                                            return value.slice(0, 23) + '...'
                                        return value
                                    }
                                },
                                value: {
                                    fontSize: '1.8rem',
                                    fontWeight: 300,
                                    offsetY: -14,
                                    formatter: value => {
                                        return value
                                    }
                                },
                                total: {
                                    show: true,
                                    fontSize: '13px',
                                    fontWeight: 400,
                                    label: ['Всего видов спортивных', 'сооружений'],
                                    color: '#000',
                                    formatter: () => this.statInfo.count_facility_types
                                },
                            }
                        }
                    },
                },
                labels: this.facilityTypesLabels
            }
        }
    },
    data() {
        return {
            maxLength: 16,
            strokeColor: ['#1690ff', '#fe851a', '#b461f2'],
            visible: false,
            statInfo: null,
            apexchartKey: Date.now()
        }
    },
    methods: {
        priceFormatter
    },
    mounted(){
        eventBus.$on('viewStatDrawer', data => {
            this.statInfo = data
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('viewStatDrawer')
    }
}
</script>

<style lang="scss" scoped>
.sports_stat_drawer{
    &::v-deep{
        .ant-drawer-body{
            padding: 20px 10px;
            @media (min-width: 768px) {
                padding: 24px;
            }
        }
    }
}
.stat_value_item{
    display: flex;
    align-items: baseline;
    .crc{
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }
    .info{
        padding-left: 8px;
    }
    .name{
        font-size: 13px;
        line-height: 18px;
    }
    .val{
        opacity: 0.6;
    }
}
.stat_card{
    background: #FAFAFA;
    border-radius: 12px;
    padding: 20px 15px;
    color: #000;
    height: 100%;
    .lbl{
        opacity: 0.6;
        margin-bottom: 5px;
    }
    .g_bal{
        font-size: 18px;
        line-height: 26px;
    }
    &__head{
        padding-bottom: 15px;
        border-bottom: 1px dashed #e1e1e1;
        margin-bottom: 10px;
    }
    .stat_row{
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .row_info{
            display: flex;
            align-items: center;
            justify-content: space-between;
            .row_label{
                opacity: 0.6;
            }
        }
        &::v-deep{
            .ant-progress{
                .ant-progress-inner{
                    background-color: #E3E3E3;
                }
            }
        }
    }
}
</style>