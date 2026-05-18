<template>
    <a-spin class="key-results-spin" :spinning="loading">
        <div class="objective-key-results">
            <div class="kr-table-container">
                <div class="table-body">
                    <div class="table-header">
                        <div class="type header-cell">{{ $t('okr.type') }}</div>
                        <div class="name header-cell">{{ $t('okr.name') }}</div>
                        <div class="operator header-cell">{{ $t('okr.operator') }}</div>
                        <div class="period header-cell">{{ $t('okr.deadline') }}</div>
                        <div class="metric header-cell">{{ $t('okr.metric') }}</div>
                        <div class="base header-cell">{{ $t('okr.baseValueBriefly') }}</div>
                        <div class="plan header-cell">{{ $t('okr.plan') }}</div>
                        <div class="fact header-cell">{{ $t('okr.fact') }}</div>
                        <div class="progress--head header-cell">{{ $t('okr.completed') }}</div>
                    </div>
                    <a-collapse :bordered="false" class="key-results-collapse">
                        <a-collapse-panel v-for="kr in keyResults" :key=kr.id>
                            <template slot="header">
                                <div class="key-results-item" @click.stop="">
                                    <div class="type cell">
                                        <a-popover title="" :mouseEnterDelay="1">
                                            <template slot="content">
                                                {{ $t('okr.keyResult') }}
                                            </template>
                                            <div class="rounded kr-type">{{ $t('okr.kr') }}</div>
                                        </a-popover>
                                    </div>
                                    <!-- <a-popover v-if="showAddKR && kr?.actions?.edit"  title="" :mouseEnterDelay="1"> -->
                                    <a-popover v-if="!viewOnly && kr?.actions?.edit"  title="" :mouseEnterDelay="1">
                                        <template slot="content">
                                            {{ kr.description }}
                                        </template>
                                        <div class="cell name">
                                            <div class="editable" @click="editKR(kr)">
                                                {{ kr.description }}
                                            </div>
                                        </div>
                                    </a-popover>
                                    <a-popover v-else title="" :mouseEnterDelay="1">
                                        <template slot="content">
                                            {{ kr.description }}
                                        </template>
                                        <div class="cell name">{{ kr.description }}</div>
                                    </a-popover>
                                    <div class="cell">
                                        <Profiler
                                            :avatarSize="20"
                                            nameClass="okr-operator-profiler"
                                            :popoverText="$t('okr.operator')"
                                            :showUserName="true"
                                            :user="kr.operator" />
                                    </div>
                                    <div class="cell period">
                                        <template v-if="kr.date_end">
                                            {{ $moment(kr.date_end).format(dateFormat) }}
                                        </template>
                                        <template v-else>
                                            <div class='text-gray-300'>{{ $t('okr.deadlineNotSpecified') }}</div>
                                        </template>
                                    </div>
                                    <a-popover v-if="kr.metrics?.name" title="" :mouseEnterDelay="1">
                                        <template slot="content">
                                            {{ kr.metrics.name }}
                                        </template>
                                        <div class="cell name metric">{{ kr.metrics.name }}</div>
                                    </a-popover>
                                    <div v-else class="cell">-</div>
                                    <div class="cell">
                                        <a-input-number
                                            :ref="`input_${kr.id}_base`"
                                            :disabled="viewOnly || !kr?.actions?.update_initiatives"
                                            class="kr-input base"
                                            v-model="kr.base"
                                            :min="0"
                                            @keydown="e => stopEnter(e, 'base', kr)"
                                            @blur="() => save('base', kr)" />
                                    </div>
                                    <div class="cell">
                                        <a-input-number
                                            :ref="`input_${kr.id}_plan`"
                                            :disabled="viewOnly || !kr?.actions?.update_initiatives"
                                            class="kr-input plan"
                                            v-model="kr.plan"
                                            :min="0"
                                            @keydown="e => stopEnter(e, 'plan', kr)"
                                            @blur="() => save('plan', kr)" />
                                    </div>
                                    <div class="cell">
                                        <a-input-number
                                            :ref="`input_${kr.id}_fact`"
                                            :disabled="viewOnly || !kr?.actions?.update_initiatives"
                                            class="kr-input fact"
                                            v-model="kr.fact"
                                            :min="0"
                                            @keydown="e => stopEnter(e, 'fact', kr)"
                                            @blur="() => save('fact', kr)" />
                                    </div>
                                    <div class="cell">
                                        <div class="progress">
                                            <a-progress
                                                class="custom-progress bar"
                                                :percent="parseInt(kr.progress*100)"
                                                :show-info="false"
                                                :strokeWidth="8"
                                                strokeColor="#4777FF" />
                                            <div class="percent">{{ parseInt(kr.progress*100) }} %</div>
                                        </div>
                                    </div>
                                </div>
                            </template>
                            <Tasks
                                :keyResult="kr"
                                :tasks="kr.tasks"
                                :viewOnly="viewOnly" />
                        </a-collapse-panel>
                    </a-collapse>
                </div>
            </div>
            <a-button
                v-if="showAddKR"
                class="add-button"
                icon="plus"
                type="primary"
                @click="addKeyResult">
                {{ $t('okr.addKeyResult') }}
            </a-button>
        </div>
        <AddKeyResult
            v-if="showAddKR"
            ref="addKeyResult"
            @reloadObjective="reloadObjective" />
    </a-spin>
</template>
<script>
import { mapState, mapMutations } from 'vuex'
import AddKeyResult from './components/AddKeyResult.vue'
import Tasks from './components/Tasks'

export default {
    name: 'KeyResults',
    components: {
        AddKeyResult,
        Tasks
    },
    props: {
        addKeyResultAvailable: {
            type: Boolean,
            default: false
        },
        viewOnly: {
            type: Boolean,
            default: true
        },
        keyResults: {
            type: Array,
            default: () => []
        },
        objectiveActions: {
            type: Object,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            dateFormat: 'DD.MM.YYYY',
            prevKeys: [],
            initiatives: {}
        }
    },
    computed: {
        ...mapState({
            // keyResults: state => state.okr.objectiveKeyResults
        }),

        showAddKR() {
            // return !this.viewOnly
            return this.objectiveActions?.edit || false
        },
        updateKRAvailable() {
            // return !this.viewOnly
            return this.actions.update_key_results || false
        }
    },
    methods: {
        ...mapMutations({
            UPDATE_KEY_RESULT: 'okr/UPDATE_KEY_RESULT',
            SET_ADD_KEY_RESULT_MODAL_VISIBLE: 'okr/SET_ADD_KEY_RESULT_MODAL_VISIBLE'
        }),
        stopEnter(e, field, kr) {
            if (e.key === 'Enter') {
                e.stopPropagation();
                e.preventDefault();
                this.save(field, kr)
            }
        },
        editKR(kr) {
            this.$refs.addKeyResult.edit = true
            this.$refs.addKeyResult.inject = {...kr}
            this.$refs.addKeyResult.fillForm()
            this.SET_ADD_KEY_RESULT_MODAL_VISIBLE(true)
        },
        pressEnter(field='', kr=undefined) {
            if (!field || !kr)
                return
            const el = this.$refs[`input_${kr.id}_${field}`][0]
            if (el) {
                el.blur()
            }
        },
        reloadObjective() {
            this.$emit('reloadData')
        },
        async save(field='', kr=undefined) {
            if (!field || !kr)
                return
            this.loading = true
            const payload = {}
            payload[field] = kr[field]
            if (!payload[field]) {
                payload[field] = 0
            }
            try {
                const { data } = await this.$http.patch(`/okr/key_results/${kr.id}/`, payload)
                if (data) {
                    this.UPDATE_KEY_RESULT(data)
                    this.$emit('reloadData')
                }
            } catch(e) {
                this.$message.error(this.$t('okr.saveDataFailed'))
            } finally {
                this.loading = false
            }
        },
        addKeyResult() {
            this.SET_ADD_KEY_RESULT_MODAL_VISIBLE(true)
        },
    }
}
</script>
<style lang="scss" scoped>
$columns: 46px 1fr 140px 70px 140px 100px 100px 100px 125px;
.key-results-spin::v-deep {
    height: 100%;
    .ant-spin-container {
        height: 100%;
    }
}
.objective-key-results {
    display: flex;
    gap: 15px;
    flex-direction: column;
    min-width: 1040px;
    .kr-table-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        border: 1px solid rgba(229, 231, 239, 1);
        background-color: #F0F1F7;
        border-radius: 16px;
        overflow: hidden;
        .key-results-item, .table-header {
            display: grid;
            grid-template-columns: $columns;
            column-gap: 8px;
            align-items: center;
        }
        .type {
            justify-self: center;
            font-size: 12px;
        }
        .table-header {
            // padding-left: 40px;
            width: 100%;
            grid-template-rows: 40px;
            background-color: #F0F1F7;
            font-weight: 400;
            font-size: 12px;
            line-height: 16px;
            color: #2D2D2D;
            position: sticky;
            top: 0;
            z-index: 10;
            .header-cell {
                padding: 8px 4px;
            }
        }
        .table-body {
            overflow: auto;
            width: 100%;
            .key-results-collapse {
                background-color: #fff;
                border-radius: 0;
                .ant-collapse-item {
                    &:not(:last-child){
                        border-bottom: 1px solid #DADADA;
                    }
                }
                &::v-deep {
                    .ant-collapse-header {
                        // padding: 0 0 0 40px;
                        padding: 0 0 0 0;
                    }
                    .ant-collapse-arrow {
                        left: 62px;
                    }
                    .ant-collapse-item {
                        border-bottom: 0;
                    }
                    .ant-collapse-content {
                        background-color: #F8F9FD;
                    }
                    .ant-collapse-content-box {
                        padding: 0;
                    }
                }
            }
            .key-results-item {
                width: 100%;
                cursor: default;
                height: 60px;
                .cell {
                    padding: 8px 4px;
                    font-size: 12px;
                    color: #2D2D2D;
                    .base.ant-input-number {
                        background-color: #E8EDFA;
                        border-color: #E8EDFA;
                        font-size: 14px;
                        color: #4777FF;
                    }
                    .plan.ant-input-number {
                        background-color: #E6EFE3;
                        border-color: #E6EFE3;
                        font-size: 14px;
                        color: #368225;
                    }
                    .fact.ant-input-number {
                        background-color: #FFF8EB;
                        border-color: #FFF8EB;
                        font-size: 14px;
                        color: #FF9A01;
                    }
                    .kr-input.ant-input-number {
                        width: 100%;
                    }
                    .edit-icon {
                        font-size: 18px;
                        cursor: pointer;
                    }
                    .okr-operator-profiler {
                        font-size: 12px;
                        color: #2D2D2D;
                    }
                    &::v-deep {
                        .ant-input-number-handler-wrap {
                            display: none;
                        }
                        .ant-progress-inner {
                            background-color: rgba(29, 101, 192, 0.1);
                        }
                    }
                }
                .progress {
                    display: flex;
                    gap: 5px;
                    align-items: center;
                    .bar {
                        flex: 1;
                    }
                }
                
                .rounded {
                    height: 20px;
                    width: 20px;
                    border-radius: 50%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .kr-type {
                    background-color: #E6EFE3;
                    color: #368225;;
                }
                .t-type {
                    background-color: #E8EDFA;
                    color: #4777FF;
                }
                .name {
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    line-height: 1.5;
                    max-height: calc(3 * 1.5em);
                    word-break: break-word;
                    padding-left: 46px;
                    padding-top: 0;
                    padding-bottom: 0;
                }
                .metric {
                    padding-left: 0;
                }
                .editable {
                    cursor: pointer;
                    color: #4777FF !important;
                    &:hover {
                        text-decoration: underline;
                    }
                }
            }
        }
    }
    .add-button {
        width: min-content;
    }
}
</style>