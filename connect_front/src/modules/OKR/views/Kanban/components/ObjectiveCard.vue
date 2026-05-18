<template>
    <a-spin :spinning="loading">
        <div class="objective-card">
            <div class="department">
                {{ department }}
            </div>
            <div class="status">
                <ObjectiveStatus
                    :objective="objective"
                    @setLoading="setLoading" />
            </div>
            <div class="actions">
                <div
                    v-if="objective?.has_retrospective"
                    class="retro"
                    @click="showRetro">
                    {{ $t('okr.retro') }}
                </div>
                <ObjectiveActionMenu
                    v-if="objective.actions.edit || objective.actions.delete"
                    :objective="objective"
                    :editObjective="editObjective"
                    :deleteObjective="deleteHandler" />
            </div>
            <div class="objective" @click="openDetail()">
                {{ objective.objective }}
            </div>
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
                    :strokeWidth="15"
                    strokeColor="rgba(29, 101, 192, 1)" />
            </div>
            <div class="period">
                <i class="fi fi-rr-calendar"></i>
                {{ period }}
            </div>
            <div class="operator">
                <Profiler
                    :avatarSize="20"
                    nameClass="text-sm"
                    :popoverText="$t('okr.owner')"
                    :showUserName="false"
                    :user="objective.owner" />
                <i class="fi fi-rr-angle-small-right"></i>
                <Profiler
                    :avatarSize="20"
                    nameClass="text-sm"
                    :popoverText="$t('okr.operator')"
                    :showUserName="false"
                    :user="objective.operator" />
            </div>
            <div class="details">
                <a-collapse :bordered="false" @change="onDetailsVisibleChange" expandIconPosition="right" class="kr-collapse">
                    <a-collapse-panel key="1" :header="$t('okr.keyResults')" >
                        <CardKeyResults
                            :loading="KRLoading"
                            :keyResults="keyResultsList" />
                    </a-collapse-panel>
                </a-collapse>
            </div>
        </div>
    </a-spin>
</template>

<script>
import ItemsMixin from '@apps/OKR/mixins/ItemsMixin'
export default {
    name: 'ObjectiveCard',
    components: {
        CardKeyResults: () => import('./CardKeyResults.vue')
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
            KRLoading: false
        }
    },
    computed: {
        department() {
            return this.objective.department ? this.objective.department.name : this.objective.organization ? this.objective.organization.name : this.$t('okr.notSpecified')
        }
    },
    methods: {
        onDetailsVisibleChange(key) {
            if (key.length) {
                this.KRLoading = true
                this.fetchKeyResults({
                    objectiveID: this.objective.id,
                    quarter: this.objective.quarter
                })
                    .finally(() => {
                        this.KRLoading = false
                    })
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.objective-card {
    background-color: #F8F9FD;
    min-width: 325px;
    border-radius: 8px;
    padding: 17px 15px;
    display: grid;
    align-items: center;
    gap: 8px;
    grid-template-columns: repeat(2, 1fr);
    grid-template-areas:
        "status actions"
        "department department"
        "objective objective"
        "progress progress"
        "period operator"
        "details details";
    .department {
        grid-area: department;
        font-weight: 400;
        font-size: 14px;
        color: #888888;
        align-self: end;
        height: 45px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .status {
        grid-area: status;
    }
    .actions {
        grid-area: actions;
        justify-self: end;
        display: flex;
        align-items: center;
        gap: 8px;
        .retro {
            color: #4777FF;
            cursor: pointer;
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 8px;
            &:hover {
                background-color: #fff;
            }
        }
    }
    .objective {
        grid-area: objective;
        font-weight: 400;
        font-size: 13px;
        line-height: 130%;
        color: #2D2D2D;
        height: 50px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        cursor: pointer;
        &:hover {
            color: #4777FF;
        }
    }
    .value_efforts {
        font-weight: 400;
        font-size: 12px;
        color: #2D2D2D;
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-height: 21px;
        &::v-deep {
            .ant-badge-status-dot {
                height: 10px;
                width: 10px;
            }
        }
    }
    .progress {
        grid-area: progress;
        .percent {
            font-weight: 400;
            font-size: 13px;
            line-height: 130%;
            color: rgba(29, 101, 192, 1);
        }
        &::v-deep {
            .ant-progress-inner {
                background-color: rgba(207, 214, 229, 1);
            }
            .ant-progress-inner {
                border-radius: 4px;
            }
            .ant-progress-bg {
                border-radius: 4px !important;
            }
        }
    }
    .operator {
        grid-area: operator;
        height: 40px;
        display: flex;
        gap: 8px;
        align-items: center;
        justify-content: end;
    }
    .period {
        grid-area: period;
        font-weight: 400;
        font-size: 12px;
        line-height: 16px;
        color: #2D2D2D;
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .details {
        grid-area: details;
        &::v-deep {
            .ant-collapse-borderless {
                background-color: unset;
                border-radius: 8px;
            }
            .ant-collapse-item {
                border-bottom: 0;
            }
            .ant-collapse-arrow {
                right: 8px;
            }
            .ant-collapse-header {
                padding-left: 8px;
            }
            .ant-collapse-content-box {
                padding-left: 8px;
                padding-right: 8px;
                padding-bottom: 8px;
            }
        }
        .kr-collapse {
            &:hover {
                background-color: #fff;
            }
        }
    }
}
</style>