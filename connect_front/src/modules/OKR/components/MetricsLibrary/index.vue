<template>
    <div class="wrapper">
        <a-button
            type="ui"
            :size="size"
            :ghost="ghost"
            v-tippy="{ content: $t('okr.metricsLibrary') }"
            flaticon
            icon="fi-rr-arrow-up-right-from-square"
            @click="openModal" />
        <a-modal
            v-model="visible"
            :zIndex="1700"
            class="metrics-library-modal"
            width="680px"
            :footer="null"
            :afterClose="afterClose" >
            <template slot="title" class="modal-title">
                {{ $t('okr.metricsLibrary') }}
            </template>
            <div class="content" ref="content">
                <div class="search">
                    <a-input-search
                        size='large'
                        v-model="search"
                        :placeholder="$t('okr.searchMetricsLibrary')"/>
                </div>
                <div class="item">
                    <a-dropdown
                        :zIndex="160000"
                        v-model="dropDownVisible"
                        :trigger="['click']"
                        key="dd_add_metric"
                        :getPopupContainer="getPopupContainer"
                        overlayClassName="add-metric-dropdown"
                        @visibleChange="onVisibleChange">
                        <div class="add-metric">{{ $t('okr.addCustomMetric') }}</div>
                        <a-menu slot="overlay">
                            <AddMetric
                                ref="addMetric"
                                @close="dropdownClose" />
                        </a-menu>
                    </a-dropdown>
                    <div class="description cursor-default">{{ $t('okr.addMetricIfNotInLibrary') }}</div>
                </div>
                <div class="list">
                    <div v-for="metric in filteredMetrics" :key=metric.id class="item">
                        <div class="metric-option">
                            <div class="metric" @click="selectMetric(metric)">{{ metric.name }}</div>
                            <a-dropdown
                                :trigger="['click']"
                                v-model="editDropDownVisible[metric.id]"
                                overlayClassName="add-metric-dropdown"
                                @visibleChange="(vis) => onEditDDVisibleChange(vis, metric)">
                                <i class="fi fi-rr-pencil"></i>
                                <a-menu slot="overlay">
                                    <AddMetric
                                        :ref="`metric_${metric.id}`"
                                        :inject="metric"
                                        edit
                                        @close="closeEditDropDown" />
                                </a-menu>
                            </a-dropdown>
                        </div>
                        <div class="description cursor-default">{{ `${metric.description ? metric.description : '-'}` }}</div>
                    </div>
                    <a-empty v-if="!filteredMetrics.length" :description="false" class="metric-empty" />
                </div>
            </div>
        </a-modal>
    </div>
</template>
<script>
import { mapState } from 'vuex'
import AddMetric from './components/AddMetric.vue'

export default {
    name: 'MetricsLibrary',
    components: {
        AddMetric
    },
    props: {
        size: {
            type: String,
            default: 'default'
        },
        ghost: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            visible: false,
            search: '',
            dropDownVisible: false,
            editDropDownVisible: {}
        }
    },
    computed: {
        ...mapState({
            metrics: state => state.okr.metrics
        }),
        filteredMetrics() {
            return this.metrics.filter(metric =>
                metric.name.toLowerCase().includes(this.search.toLowerCase()) ||
                metric.description.toLowerCase().includes(this.search.toLowerCase())
            )
        },
    },
    methods: {
        getPopupContainer() {
            return this.$refs.content
        },
        openModal() {
            this.visible = true
        },
        closeModal() {
            this.visible = false
        },
        dropdownClose() {
            this.dropDownVisible = false
        },
        closeEditDropDown(key) {
            this.editDropDownVisible[key] = false
        },
        onEditDDVisibleChange(vis, metric) {
            if (vis) {
                this.$nextTick(() => {
                    const el = this.$refs[`metric_${metric.id}`][0] || null
                    if (el) {
                        vis ? el.fillForm() : el.resetForm()
                    }
                })
            }
        },
        onVisibleChange(vis) {
            if (!vis) {
                this.$nextTick(() => {
                    const el = this.$refs.addMetric || null
                    if (el) {
                        el.resetForm()
                    }
                })
            }
        },
        selectMetric(metric) {
            this.$emit('selectMetric', metric.id)
            this.closeModal()
        },
        afterClose() {
            this.search = ''
            this.editDropDownVisible = {}
        }
    }
}
</script>
<style lang="scss" scoped>
.wrapper {
    .library-button {
        background-color: #fff;
        border-radius: 4px;
        border-color: #d9d9d9;
    }
}
</style>
<style lang="scss">
.metrics-library-modal {
    .modal-title {
        font-weight: 400;
        font-size: 16px;
    }
    .ant-modal-header {
        border-bottom: unset;
    }
    .content {
        height: 350px;
        overflow: auto;
        display: flex;
        flex-direction: column;
        gap: 15px;
        .search {}
        .list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            overflow: auto;
            flex: 1;
        }
        .item {
            cursor: pointer;
            .metric, .description, .add-metric {
                font-weight: 400;
                font-size: 14px;
                color: #000;
            }
            .description {
                opacity: 0.6;
            }
            .add-metric {
                color: #1D65C0;
            }
            .metric-option {
                display: flex;
                align-items: center;
                gap: 16px;
                .metric {
                    flex: 1;
                }
            }
        }
        .metric-empty {
            flex: 1;
            align-content: center;
        }
    }
    .ant-input {
        border-radius: 4px;
        margin-bottom: 0;
    }
}
</style>
<style lang="scss">
.add-metric-dropdown {
    min-width: unset !important;
    width: 410px;
    padding: 20px;
    z-index: 160000;
}
</style>