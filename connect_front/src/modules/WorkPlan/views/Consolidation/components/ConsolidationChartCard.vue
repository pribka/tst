<template>
    <div class="consolidation_card">
        <div class="consolidation_card__header">
            <div class="consolidation_card__title">
                {{ title }}
            </div>

            <a-dropdown
                v-if="drilldown.length > 1"
                :trigger="['click']"
                placement="bottomRight"
                destroyPopupOnHide>
                <div class="consolidation_card__details" @click.stop>
                    {{ $t('workplan.details') }}
                </div>
                <template #overlay>
                    <a-menu>
                        <a-menu-item
                            v-for="(dd, ddIdx) in drilldown"
                            :key="ddIdx"
                            @click="openDrilldown(dd)">
                            {{ dd.title }}
                        </a-menu-item>
                    </a-menu>
                </template>
            </a-dropdown>

            <div
                v-else-if="drilldown.length === 1"
                class="consolidation_card__details"
                @click.stop="openDrilldown(drilldown[0])">
                {{ $t('workplan.details') }}
            </div>
        </div>

        <div class="consolidation_card__body">
            <a-spin
                v-if="loading"
                :spinning="true"
                size="small"
                class="consolidation_card__spinner">
                <div class="consolidation_card__loading_text">
                    Загрузка...
                </div>
            </a-spin>

            <div
                v-else-if="error"
                class="consolidation_card__error">
                {{ error }}
            </div>

            <div
                v-else-if="chartData"
                class="consolidation_card__chart_wrap">
                <button
                    v-if="showScrollLeft"
                    type="button"
                    class="consolidation_card__scroll_btn consolidation_card__scroll_btn--left"
                    @mouseenter="startChartScroll('left')"
                    @mouseleave="stopChartScroll"
                    @focus="startChartScroll('left')"
                    @blur="stopChartScroll">
                    <i class="fi fi-rr-angle-small-left" />
                </button>

                <div
                    ref="scrollContainer"
                    class="consolidation_card__chart_scroll"
                    @scroll="updateScrollState">
                    <apexchart
                        :width="chartWidth"
                        :height="chartHeight"
                        :type="chartType"
                        :options="chartData.chartOptions"
                        :series="chartData.series"
                        class="consolidation_card__chart" />
                </div>

                <button
                    v-if="showScrollRight"
                    type="button"
                    class="consolidation_card__scroll_btn consolidation_card__scroll_btn--right"
                    @mouseenter="startChartScroll('right')"
                    @mouseleave="stopChartScroll"
                    @focus="startChartScroll('right')"
                    @blur="stopChartScroll">
                    <i class="fi fi-rr-angle-small-right" />
                </button>
            </div>

            <span v-else class="consolidation_card__placeholder" />
        </div>
        <div v-if="drilldownLoading" class="consolidation_card__drill_overlay">
            <a-spin :spinning="true" />
        </div>
    </div>
</template>

<script>
export default {
    components: {
        apexchart: () => import('vue-apexcharts')
    },
    props: {
        title: {
            type: String,
            default: ''
        },
        scope: {
            type: String,
            default: ''
        },
        relatedObjectId: {
            type: [String, Array],
            default: ''
        },
        startDate: {
            type: String,
            default: ''
        },
        endDate: {
            type: String,
            default: ''
        },
        drilldown: {
            type: Array,
            default: () => []
        },
        loading: {
            type: Boolean,
            default: false
        },
        error: {
            type: String,
            default: ''
        },
        chartData: {
            type: Object,
            default: null
        },
        chartWidth: {
            type: [String, Number],
            default: '100%'
        },
        chartHeight: {
            type: [String, Number],
            default: 240
        },
        chartType: {
            type: String,
            default: 'line'
        }
    },
    data() {
        return {
            drilldownLoading: false,
            scrollTimer: null,
            scrollState: {
                hasScroll: false,
                canScrollLeft: false,
                canScrollRight: false
            }
        }
    },
    computed: {
        showScrollLeft() {
            return Boolean(this.scrollState.hasScroll && this.scrollState.canScrollLeft)
        },
        showScrollRight() {
            return Boolean(this.scrollState.hasScroll && this.scrollState.canScrollRight)
        }
    },
    watch: {
        chartData() {
            this.$nextTick(() => {
                this.updateScrollState()
            })
        },
        chartWidth() {
            this.$nextTick(() => {
                this.updateScrollState()
            })
        },
        chartHeight() {
            this.$nextTick(() => {
                this.updateScrollState()
            })
        }
    },
    methods: {
        updateScrollState() {
            const scrollContainer = this.$refs.scrollContainer
            if (!scrollContainer) return

            const maxScrollLeft = Math.max(scrollContainer.scrollWidth - scrollContainer.clientWidth, 0)
            const scrollLeft = scrollContainer.scrollLeft || 0
            const hasScroll = maxScrollLeft > 4
            const nextState = {
                hasScroll,
                canScrollLeft: hasScroll && scrollLeft > 4,
                canScrollRight: hasScroll && scrollLeft < maxScrollLeft - 4
            }

            if (
                this.scrollState.hasScroll === nextState.hasScroll
                && this.scrollState.canScrollLeft === nextState.canScrollLeft
                && this.scrollState.canScrollRight === nextState.canScrollRight
            ) {
                return
            }

            this.scrollState = nextState
        },
        startChartScroll(direction = 'right') {
            this.stopChartScroll()

            const scrollContainer = this.$refs.scrollContainer
            if (!scrollContainer) return

            const step = direction === 'left' ? -16 : 16
            const tick = () => {
                const maxScrollLeft = Math.max(scrollContainer.scrollWidth - scrollContainer.clientWidth, 0)
                const nextScrollLeft = Math.min(
                    Math.max(scrollContainer.scrollLeft + step, 0),
                    maxScrollLeft
                )

                if (nextScrollLeft === scrollContainer.scrollLeft) {
                    this.stopChartScroll()
                    this.updateScrollState()
                    return
                }

                scrollContainer.scrollLeft = nextScrollLeft
                this.updateScrollState()
            }

            tick()
            this.scrollTimer = window.setInterval(tick, 32)
        },
        stopChartScroll() {
            if (!this.scrollTimer) return

            window.clearInterval(this.scrollTimer)
            this.scrollTimer = null
        },
        async openDrilldown(item) {
            if (this.drilldownLoading) return
            this.drilldownLoading = true
            try {
                const data = await this.$store.dispatch('workplan/getConsolidationPreparedReportSettings', {
                    reportCode: item.report_code,
                    filterPreset: item.filter_preset || null,
                    scope: this.scope,
                    relatedObjectId: this.relatedObjectId,
                    startDate: this.startDate,
                    endDate: this.endDate
                })

                if (!data)
                    throw new Error('empty_report_settings')

                await this.$store.dispatch('reports/openReportModal', {
                    ...data,
                    appSectionCode: data.app_section_code
                })
            } catch (error) {
                this.$message.error(this.$t('workplan.drilldown_error'))
            } finally {
                this.drilldownLoading = false
            }
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.updateScrollState()
        })
    },
    beforeDestroy() {
        this.stopChartScroll()
    }
}
</script>

<style lang="scss" scoped>
.consolidation_card{
    min-height: 160px;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    background: #fff;
    display: flex;
    flex-direction: column;
    position: relative;
    &__drill_overlay{
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.75);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        z-index: 10;
    }
    &__header{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 14px 16px 0;
    }
    &__title{
        font-weight: 500;
        color: var(--text_title);
        margin-bottom: 6px;
    }
    &__details{
        margin-bottom: 6px;
        color: var(--blue);
        cursor: pointer;
        font-size: 11px;
        white-space: nowrap;
    }
    &__body{
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        min-height: 180px;
    }
    &__spinner{
        width: 100%;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    &__loading_text{
        margin-top: 8px;
        color: var(--text_grey);
        font-size: 12px;
    }
    &__placeholder{
        color: var(--text_grey);
        text-align: center;
        word-break: break-word;
    }
    &__error{
        color: #cb4b3f;
        text-align: center;
        word-break: break-word;
        font-size: 12px;
        line-height: 1.4;
    }
    &__chart{
        min-width: 100%;
        min-height: 220px;
        padding: 0 8px 4px 0;
    }
    ::v-deep .apexcharts-bar-area {
        transform-box: fill-box;
        transform-origin: 50% 100%;
        transform: scaleX(0.78);
    }
    &__chart_wrap{
        width: 100%;
        position: relative;
        align-self: stretch;
        display: flex;
        align-items: center;
    }
    &__chart_scroll{
        overflow-x: auto;
        overflow-y: hidden;
        padding-bottom: 10px;
        scrollbar-width: thin;
        width: 100%;
    }
    &__scroll_btn{
        position: absolute;
        top: calc(50% - 18px);
        transform: translateY(-50%);
        z-index: 2;
        width: 28px;
        height: 28px;
        border: 0;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 4px 14px rgba(31, 42, 68, 0.12);
        color: #5F7192;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        pointer-events: none;
        transition: opacity .2s ease;
        .fi{
            font-size: 16px;
            line-height: 1;
        }
        &--left{
            left: 8px;
        }
        &--right{
            right: 8px;
        }
    }
    &:hover{
        .consolidation_card__scroll_btn{
            opacity: 1;
            pointer-events: auto;
        }
    }
}
</style>
