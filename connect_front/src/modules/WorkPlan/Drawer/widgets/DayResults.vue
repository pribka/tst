<template>
    <div>
        <div class="aside_wrapper" :class="[!isMobile && 'use_scroll', useInject && 'use_inject']">
            <a-spin :spinning="isLoading ? false : statisticsLoading" size="small" class="w-full">
                <div class="results_header">
                    <h3>{{ $t('workplan.day_results') }}</h3>
                    <!--<transition name="report-slide-down">
                        <component
                            :is="reportButtonComponent"
                            v-if="reportButtonComponent"
                            :reportSetting="reportSetting"
                            type="link" />
                    </transition>-->
                </div>
                <DayLoading v-if="isLoading" />
                <template v-if="dayStatistics">
                    <div class="list_item rounded-lg" style="background: #dfedff;">
                        <div class="icon_wrapper rounded-lg">
                            <div class="icon_bg" style="background: #4777FF;" />
                            <i class="fi fi-rr-clock" style="color: #4777FF;" />
                        </div>
                        <div class="info_wrapper">
                            <div class="info_wrapper__label">
                                {{ $t('workplan.total_spent') }}
                            </div>
                            <div class="info_wrapper__value">
                                {{ secondsFormat(dayStatistics.total_duration) }}
                            </div>
                        </div>
                    </div>
                    <template v-if="dayStatistics.by_work_type && dayStatistics.by_work_type.length">
                        <div v-for="(item, index) in dayStatistics.by_work_type" :key="index" class="list_item rounded-lg">
                            <div class="icon_wrapper rounded-lg">
                                <div class="icon_bg" :style="`background: ${item.work_type_color ? item.work_type_color : '#4777FF'};`" />
                                <i class="fi" :class="item.work_type_icon || 'fi-rr-stats'" :style="`color: ${item.work_type_color ? item.work_type_color : '#4777FF'};`" />
                            </div>
                            <div class="info_wrapper">
                                <div class="info_wrapper__label">
                                    {{ item.work_type_name }}
                                </div>
                                <div class="info_wrapper__value">
                                    {{ secondsFormat(item.duration) }}
                                </div>
                            </div>
                        </div>

                        <a-divider class="mb-4" />
                        <h4 class="flex items-center">
                            <i class="fi fi-rr-chart-simple-horizontal mr-2" />
                            {{ $t('workplan.time_distribution') }}
                        </h4>
                        <div v-for="(item, index) in dayStatistics.by_work_type" :key="`${index}_progress`" class="progress_line">
                            <div class="progress_line__header">
                                <div class="header_label">
                                    {{ item.work_type_name }}
                                </div>
                                <div class="header_value">
                                    {{item.quantity_percentage}}%
                                </div>
                            </div>
                            <div class="progress_line__wrapper">
                                <div class="progress_percent" :style="`background: ${item.work_type_color ? item.work_type_color : '#4777FF'};width: ${item.quantity_percentage}%;`" />
                            </div>
                        </div>
                    </template>
                </template>
            </a-spin>
        </div>
    </div>
</template>

<script>
import { secondsFormat } from '@/utils/utils.js'
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        DayLoading: () => import('./DayLoading.vue')
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        dayStatistics() {
            return this.$store.state.workplan.day_statistics?.[this.storeKey]?.data || null
        },
        reportSetting() {
            return this.$store.state.workplan.reportSettings?.[this.storeKey] || null
        },
        reportButtonComponent() {
            if(!this.reportSetting)
                return null
            return () => import('@/modules/Reports/components/OpenReportBySettingButton.vue')
        },
        statisticsLoading() {
            return this.$store.state.workplan.day_statistics?.[this.storeKey]?.loading || false
        },
        isLoading() {
            if(this.statisticsLoading && !this.dayStatistics)
                return true
            return false
        }
    },
    methods: {
        secondsFormat,
        formatMinutes(hours) {
            if (hours === null || hours === undefined) {
                return this.$t('workplan.zero_min')
            }
            const totalMinutes = Math.round(Number(hours) * 60)
            if (!totalMinutes) {
                return this.$t('workplan.zero_min')
            }
            const days = Math.floor(totalMinutes / 1440)
            const hrs = Math.floor((totalMinutes % 1440) / 60)
            const mins = totalMinutes % 60

            const parts = []
            if (days) parts.push(`${days} ${days === 1 ? this.$t('workplan.day_one') : this.$t('workplan.day_few')}`)
            if (hrs) parts.push(`${hrs} ${this.$t('workplan.hour_short')}`)
            if (mins) parts.push(`${mins} ${this.$t('workplan.minute_short')}`)

            return parts.join(' ')
        }
    },
    mounted() {
        this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
        this.$store.dispatch('workplan/getWorkHoursSummaryReportSetting', { storeKey: this.storeKey })
    }
}
</script>

<style lang="scss" scoped>
.progress_line{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__header{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 5px;
        .header_label{
            opacity: 0.8;
        }
        .header_value{
            font-weight: 600;
        }
    }
    &__wrapper{
        height: 10px;
        width: 100%;
        overflow: hidden;
        border-radius: 8px;
        background: #F8F9FD;
        position: relative;
        .progress_percent{
            border-radius: 8px;
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
    }
}
.list_item{
    display: flex;
    align-items: center;
    background: #F8F9FD;
    padding: 10px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .info_wrapper{
        &__label{
            opacity: 0.9;
            word-break: break-word;
            margin-bottom: 2px;
        }
        &__value{
            color: #000;
            word-break: break-word;
            font-size: 18px;
            line-height: 24px;
            font-weight: 600;
        }
    }
    .icon_wrapper{
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 18px;
        position: relative;
        overflow: hidden;
        .icon_bg{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.2;
        }
        i{
            position: relative;
            z-index: 5;
        }
    }
}
.aside_wrapper{
    background: #fff;
    border-radius: 12px;
    padding: 15px;
    &.use_inject{
        padding: 0px;
    }
    @media (min-width: 768px) {
        padding: 20px;
    }
    &.use_scroll{
        overflow-y: auto;
    }
    h3{
        font-size: 18px;
        font-weight: 600;
        color: #000;
        margin-bottom: 15px;
    }
    h4{
        font-size: 15px;
        color: #000;
        margin-bottom: 15px;
        font-weight: 600;
    }
}
.results_header{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 15px;
    h3{
        margin-bottom: 0;
    }
}
.report-slide-down-enter-active,
.report-slide-down-leave-active{
    transition: all 0.22s ease;
}
.report-slide-down-enter,
.report-slide-down-leave-to{
    opacity: 0;
    transform: translateY(-10px);
}
</style>
