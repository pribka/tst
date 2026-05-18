<template>
    <div>
        <div 
            v-for="legendItem, index in legend"
            :key="legendItem"
            class="py-1 percentages_grid"
            :class="fullWidth && 'full_width'">
            <div class="text-base">
                {{ legendItem }}
            </div>
            <template v-if="!hideValues">
                <div class="pr-4 font-semibold text-base text-right">
                    {{ series[index] }}
                </div>
            </template>
            <div class="percentage w-10 flex flex-col shrink-0 text-center">
                <span class="text-base">
                    {{ getPercent(series[index]) }}%
                </span>
                <a-progress 
                    :percent="getPercent(series[index])" 
                    :showInfo="false"
                    :strokeColor="colors[index]"
                    size="small" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'PercentageList',
    props: {
        analytics: {
            type: Array,
            default: () => []    
        },
        fullWidth: {
            type: Boolean,
            default: false
        },
        colors: {
            type: Array,
            default: () => []
        },
        hideValues: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        totalAppeals() {
            return this.series.reduce((total, current) => total + current, 0)
        },
        legend() {
            return this.analytics.map(analyticsItem => analyticsItem.name)
        },
        series() {
            return this.analytics.map(analyticsItem => analyticsItem.value)
        },
    },
    methods: {
        getPercent(part) {
            return Number((part/this.totalAppeals*100).toFixed(0)) ? Number((part/this.totalAppeals*100).toFixed(0)) : 0
        }
    }
}
</script>

<style lang="scss" scoped>

.percentages_grid {
    border-bottom: 1px solid #ebebeb;
    display: grid;
    grid-template-columns: 1fr 60px 40px;
    &:last-child {
        border-bottom: none;
    }
}
.percentages_grid.full_width {
    grid-template-columns: minmax(300px, 1fr) 60px 40px;
}


.percentage::v-deep {
    .ant-progress-outer {
        display: flex;
    }
}
</style>