<template>
    <div class="consolidation_group">
        <div class="consolidation_group__title">
            {{ group.title }}
        </div>

        <a-spin :spinning="drilldownLoading" size="small">
        <div class="consolidation_group__kpi_grid">
            <template v-for="(widget, widgetIndex) in group.widgets || []">
                <a-dropdown
                    v-if="(widget.drilldown || []).length > 1"
                    :key="`dd-${widgetKeyFn(widget, groupIndex, widgetIndex)}`"
                    :trigger="['click']"
                    placement="bottomLeft"
                    destroyPopupOnHide>
                    <div
                        class="consolidation_kpi_card"
                        :class="widgetClassFn(widget)">
                        <div class="consolidation_kpi_card__value">
                            {{ widget.value ?? 0 }}
                        </div>
                        <div class="consolidation_kpi_card__title">
                            {{ widget.title }}
                        </div>
                    </div>
                    <template #overlay>
                        <a-menu>
                            <a-menu-item
                                v-for="(dd, ddIdx) in widget.drilldown"
                                :key="ddIdx"
                                @click="openDrilldown(dd)">
                                {{ dd.title }}
                            </a-menu-item>
                        </a-menu>
                    </template>
                </a-dropdown>

                <div
                    v-else
                    :key="widgetKeyFn(widget, groupIndex, widgetIndex)"
                    class="consolidation_kpi_card"
                    :class="widgetClassFn(widget)"
                    @click="handleCardClick(widget)">
                    <div class="consolidation_kpi_card__value">
                        {{ widget.value ?? 0 }}
                    </div>
                    <div class="consolidation_kpi_card__title">
                        {{ widget.title }}
                    </div>
                </div>
            </template>
        </div>
        </a-spin>
    </div>
</template>

<script>
export default {
    props: {
        group: {
            type: Object,
            required: true
        },
        groupIndex: {
            type: Number,
            default: 0
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
        widgetKeyFn: {
            type: Function,
            required: true
        },
        widgetClassFn: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            drilldownLoading: false
        }
    },
    methods: {
        handleCardClick(widget) {
            const drilldown = widget.drilldown || []
            if (drilldown.length === 0) {
                this.$message.warning(this.$t('workplan.no_drilldown'))
                return
            }
            this.openDrilldown(drilldown[0])
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
    }
}
</script>

<style lang="scss" scoped>
.consolidation_group{
    margin-top: 18px;
    &__title{
        margin-bottom: 12px;
        font-size: 18px;
        font-weight: 600;
        color: var(--text_title);
    }
    &__kpi_grid{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(132px, 132px));
        gap: 12px;
    }
}

.consolidation_kpi_card{
    min-height: 112px;
    padding: 12px 14px;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    background: #fff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    cursor: pointer;
    transition: border-color .2s ease, background-color .2s ease;
    &__value{
        font-size: 18px;
        line-height: 1.1;
        font-weight: 700;
        color: #1f2a44;
        min-height: 20px;
    }
    &__title{
        margin-top: 5px;
        font-size: 12px;
        line-height: 1.25;
        color: #6f7f9b;
        font-weight: 500;
        min-height: 30px;
    }
    &--danger{
        border-color: #f4c7c3;
        .consolidation_kpi_card__value{
            color: #cb4b3f;
        }
    }
    &--warning{
        border-color: #f4e1a3;
        .consolidation_kpi_card__value{
            color: #b7791f;
        }
    }
}

@media (max-width: 768px) {
    .consolidation_group{
        &__kpi_grid{
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
    }
}
</style>
