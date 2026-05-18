<template>
    <div class="consolidation_group">
        <div class="consolidation_group__title">
            {{ group.title }}
        </div>

        <div class="consolidation_group__grid">
            <ConsolidationChartCard
                v-for="(widget, widgetIndex) in group.widgets || []"
                :key="widgetKeyFn(widget, groupIndex, widgetIndex)"
                :title="widget.title"
                :drilldown="widget.drilldown || []"
                :loading="loadingFn(widget, groupIndex, widgetIndex)"
                :error="errorFn(widget, groupIndex, widgetIndex)"
                :chart-data="chartDataFn(widget, groupIndex, widgetIndex)"
                :chart-width="chartWidthFn(widget, groupIndex, widgetIndex)"
                :chart-height="chartHeightFn(widget, groupIndex, widgetIndex)"
                :chart-type="chartTypeFn(widget, groupIndex, widgetIndex)"
                :scope="scope"
                :related-object-id="relatedObjectId"
                :start-date="startDate"
                :end-date="endDate" />
        </div>
    </div>
</template>

<script>
export default {
    components: {
        ConsolidationChartCard: () => import('./ConsolidationChartCard.vue')
    },
    props: {
        group: {
            type: Object,
            required: true
        },
        groupIndex: {
            type: Number,
            default: 0
        },
        widgetKeyFn: {
            type: Function,
            required: true
        },
        loadingFn: {
            type: Function,
            required: true
        },
        errorFn: {
            type: Function,
            required: true
        },
        chartDataFn: {
            type: Function,
            required: true
        },
        chartWidthFn: {
            type: Function,
            required: true
        },
        chartHeightFn: {
            type: Function,
            required: true
        },
        chartTypeFn: {
            type: Function,
            required: true
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
    &__grid{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
    }
}

@media (max-width: 768px) {
    .consolidation_group{
        &__grid{
            grid-template-columns: 1fr;
            gap: 12px;
        }
    }
}
</style>
