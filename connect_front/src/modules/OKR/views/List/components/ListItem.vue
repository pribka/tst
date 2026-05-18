<template>
    <a-spin :spinning="loading">
        <div class="obj-list-item">
            <a-collapse
                :bordered="false"
                class="collapse-obj-list-item"
                @change="onDetailsVisibleChange">
                <a-collapse-panel :key="objective.id">
                    <template slot="header">
                        <div class="obj-collapse-header" @click.stop="">
                            <div class="left-side">
                                <div class="top">
                                    <div class="period">
                                        <i class="fi fi-rr-calendar"></i>
                                        {{ period }}
                                    </div>
                                    <div v-if="objective.department" class="department">
                                        <i class="fi fi-rr-sitemap"></i>
                                        {{ objective.department.name }}
                                    </div>
                                    <div
                                        v-if="objective?.has_retrospective"
                                        class="retro"
                                        @click="showRetro">
                                        {{ $t('okr.retro') }}
                                    </div>
                                </div>
                                <div class="description" @click="openDetail()">
                                    <a-popover title="" :mouseEnterDelay="1">
                                        <template slot="content">
                                            {{ objective.objective }}
                                        </template>
                                        {{ objective.objective }}
                                    </a-popover>
                                </div>
                            </div>
                            <Profiler
                                class="operator"
                                :avatarSize="36"
                                :popoverText="$t('okr.operator')"
                                :showUserName="false"
                                :user="objective.operator" />
                            <div class="progress">
                                <div class="value_efforts">
                                    <a-badge
                                        :color="badgeColor"
                                        :text="badgeName" />
                                    <div class="percent">
                                        {{ `${parseInt(objective.progress*100)} %` }}
                                    </div>
                                </div>
                                <a-progress
                                    class="custom-progress"
                                    :percent="Number(objective.progress)*100"
                                    :show-info="false"
                                    :strokeWidth="12"
                                    strokeColor="rgba(29, 101, 192, 1)" />
                            </div>
                            <ObjectiveStatus
                                class="status"
                                :objective="objective"
                                @setLoading="setLoading" />
                            <ObjectiveActionMenu
                                class="action-menu"
                                v-if="objective.actions.edit || objective.actions.delete"
                                :objective="objective"
                                :editObjective="editObjective"
                                :deleteObjective="deleteHandler" />
                        </div>
                    </template>
                    <ListKeyResults
                        class="list-view-key-results"
                        :loading="KRloading"
                        :keyResults="keyResultsList"/>
                </a-collapse-panel>
            </a-collapse>
        </div>
    </a-spin>
</template>
<script>
import ItemsMixin from '@apps/OKR/mixins/ItemsMixin'
export default {
    name: 'ListItem',
    components: {
        ListKeyResults: () => import('./ListKeyResults.vue')
    },
    mixins: [
        ItemsMixin
    ],
    props: {
        objective: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            dateFormat: 'DD.MM.YYYY',
            loading: false,
            KRloading: false
        }
    },
    methods: {
        onDetailsVisibleChange(key) {
            if (key.length) {
                this.KRloading = true
                this.fetchKeyResults({
                    objectiveID: this.objective.id
                })
                    .finally(() => {
                        this.KRloading = false
                    })
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.obj-list-item {
    width: 100%;
    background-color: #FFF;
    border-radius: 12px;
    padding: 16px 20px;
    &::v-deep {
        .ant-collapse-header {
            padding: 0 0 0 40px;
        }
        .ant-collapse-item {
            border-bottom: 0;
        }
        .ant-collapse-content, .ant-collapse-borderless {
            background-color: #FFF;
        }
        .ant-collapse-content-box {
            padding-right: 0;
        }
    }
    .list-view-key-results {
        overflow-x: auto;
        margin-top: 16px;
    }
    .obj-collapse-header {
        display: grid;
        column-gap: 14px;
        grid-template-columns: 1fr repeat(4, auto);
        grid-template-areas: "left_side operator progress status action_menu";
        cursor: default;
        height: 68px;
        justify-content: space-between;
        @media (max-width: 1300px) {
            grid-template-columns: auto 1fr auto;
            grid-template-areas: "left_side left_side action_menu" "operator progress status ";
            row-gap: 16px;
            height: auto;
            .action-menu {
                justify-self: end;
            }
        }
        @media (max-width: 880px) {
            grid-template-areas: "left_side left_side action_menu" "progress progress progress" "operator status status";
            .progress {
                width: 100% !important;
            }
            .status {
                justify-self: end;
            }
        }
        .left-side {
            grid-area: left_side;
            display: flex;
            flex-direction: column;
            gap: 8px;
            .top {
                display: flex;
                gap: 16px;
                font-weight: 400;
                font-style: Regular;
                font-size: 12px;
                line-height: 16px;
                align-items: center;
                .period, .department {
                    display: flex;
                    gap: 8px;
                    color: #888;
                    align-items: baseline;
                }
                .retro {
                    color: #4777FF;
                    cursor: pointer;
                    padding: 4px 8px;
                    border-radius: 8px;
                    &:hover {
                        background-color: #F8F9FD;
                    }
                }
            }
            .description {
                cursor: pointer;
                font-weight: 400;
                font-size: 14px;
                color: #2D2D2D;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                line-height: 1.2;
                max-height: calc(2 * 1.2em);
                word-break: break-word;
                padding-top: 0;
                padding-bottom: 0;
                &:hover {
                    color: #4777FF;
                }
            }
        }
        .operator {
            grid-area: operator;
        }
        .progress {
            grid-area: progress;
            width: 295px;
            height: 36px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            .value_efforts {
                font-weight: 400;
                font-size: 12px;
                line-height: 16px;
                color: #2D2D2D;
                display: flex;
                justify-content: space-between;
                align-items: center;
                height: 16px;
                &::v-deep {
                    .ant-badge-status-dot {
                        height: 10px;
                        width: 10px;
                    }
                }
            }
            .percent {
                font-weight: 400;
                font-size: 12px;
                line-height: 16px;
                color: rgba(29, 101, 192, 1);
            }
            &::v-deep {
                .ant-progress-inner {
                    background-color: rgba(207, 214, 229, 1);
                }
                .ant-progress {
                    line-height: 10px;
                    box-sizing: border-box;
                }
                .ant-progress-inner {
                    border-radius: 4px;
                    background-color: rgba(207, 214, 229, 1);
                }
                .ant-progress-bg {
                    border-radius: 4px !important;
                }
            }
        }
        .status {
            grid-area: status;
            width: 168px;
            height: 36px;
            margin-right: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .action-menu {
            grid-area: action_menu;
        }
    }
}
</style>