<template>
    <a-spin :spinning="loading" class="objective-key-results-wrapper">
        <a-alert v-if="showEmpty" :message="$t('okr.noKeyResults')" type="info" banner/>
        <KeyResults
            v-else-if="!loading"
            :keyResults="keyResults" />
    </a-spin>
</template>
<script>
import KeyResults from '@apps/OKR/components/KeyResults'

export default {
    name: 'ListKeyResults',
    components: {
        KeyResults
    },
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