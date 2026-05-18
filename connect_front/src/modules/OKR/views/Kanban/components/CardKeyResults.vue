<template>
    <a-spin :spinning="loading" class="objective-key-results-wrapper">
        <a-alert v-if="showEmpty" :message="$t('okr.noKeyResults')" type="info" banner/>
        <div v-else-if="!loading" class="kr-list">
            <div v-for="kr in keyResults" :key="kr.id" class="kr-item">
                <div class="label">{{ kr.description }}</div>
                <div class="progress">
                    <a-popover :title="kr?.metrics?.name" :mouseEnterDelay="0.8">
                        <template slot="content">
                            <div class="kr-metric">{{ `${$t('okr.baseValue')} - ${kr.base}` }}</div>
                            <div class="kr-metric">{{ `${$t('okr.planValue')} - ${kr.plan}` }}</div>
                            <div class="kr-metric">{{ `${$t('okr.factValue')} - ${kr.fact}` }}</div>
                        </template>
                        <a-progress
                            class="custom-progress bar"
                            :percent="parseInt(kr.progress*100)"
                            :show-info="false"
                            :strokeWidth="8"
                            strokeColor="#4777FF" />
                    </a-popover>
                    <div class="percent">{{ parseInt(kr.progress*100) }} %</div>
                </div>
            </div>
        </div>
    </a-spin>
</template>
<script>
export default {
    name: 'CardKeyResults',
    props: {
        loading: {
            type: Boolean,
            default: false
        },
        keyResults: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        showEmpty() {
            return !this.loading && this.keyResults.length === 0
        }
    }
}
</script>
<style lang="scss" scoped>
.objective-key-results-wrapper {
    min-height: 20px;
    width: 100%;
    .kr-list {
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        .kr-item {
            width: auto;
            display: flex;
            flex-direction: column;
            .label {
                flex: 1;
            }
            .progress {
                width: 100%;
                display: flex;
                gap: 5px;
                .bar {
                    flex: 1;
                }
                .percent {
                    min-width: 40px;
                    text-align: right;
                    color: #4777FF;
                }
            }
        }
    }
}
</style>