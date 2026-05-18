<template>
    <div class="card">
        <div class="status" :style="`background-color: ${item.status.hex_color}`">
            {{ $t('invest.status') }}: {{ item.status.name }}
        </div>
        <div class="project-name">{{ item.project_name }}</div>
        <div class="info">
            <div v-if="item.date_start && item.dead_line">
                <div class="name">{{ $t('invest.projectPeriod') }}:</div>
                <div class="value">{{ $moment(item.date_start).format('DD MMMM YYYY') }}г. - {{ $moment(item.dead_line).format('DD MMMM YYYY') }}г.</div>
            </div>
            <div v-if="item.location_full_name">
                <div class="name">{{ $t('invest.projectRegion') }}:</div>
                <div class="value">{{ item.location_full_name }}</div>
            </div>
            <div v-if="item.funds">
                <div class="name">{{ $t('invest.projectCost') }}:</div>
                <div class="value">{{ item.funds }} {{ $t('invest.mlnTenge') }}</div>
            </div>
        </div>
        <div class="funding-sources">
            <div v-for="(each, index) in item.funding_sources" :key="index" class="item">
                <div class="progress">
                    <div class="label label--mobile">
                        {{ each.funding_source.short_name }} - {{ each.amount }} {{ $t('invest.mlnTenge') }}
                    </div>
                    <div class="pb-wrap">
                        <a-progress
                            class="custom-progress"
                            :class="`trail-color-${getIndex(index)}`"
                            :percent="Number(percent(each.amount, item.funds))"
                            :show-info="false"
                            :strokeWidth="21.45"
                            :strokeColor="strokeColor(getIndex(index))" />
                        <div class="progress-text progress-text--mobile" :class="[
                            {white: getIndex(index) === 0 || getIndex(index) === 3},
                            {black: getIndex(index) === 1 || getIndex(index) === 2}
                        ]">
                            {{ percent(each.amount, item.funds) }} %
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'MobileCard',
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            strokeColors: [
                '#F94A1D',
                '#80CC33',
                '#33CCCC',
                '#8941D0'
            ],
        }
    },
    methods: {
        strokeColor(index) {
            return this.strokeColors[index]
        },
        percent(sourceAmount, total) {
            const percent = (parseFloat(sourceAmount) / parseFloat(total)) * 100
            return percent.toFixed(1)
        },
        getIndex(index) {
            return index % 4
        }
    }
}
</script>
<style lang="scss" scoped>
.card{
    padding: 15px;
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    display: flex;
    flex-direction: column;
    background: #ffffff;
    .status{
        height: 30px;
        font-size: 13px;
        font-weight: 400;
        line-height: 13px;
        text-align: center;
        color: rgba(255, 255, 255, 1);
        width: max-content;
        padding-left: 15px;
        padding-right: 15px;
        border-radius: 4px;
        display: flex;
        align-items: center;
    }
    .project-name{
        margin-top: 15px;
        font-size: 16px;
        font-weight: 400;
        line-height: 22.4px;
        color: rgba(0, 0, 0, 1)
    }
    .info{
        margin-top: 15px;
        font-weight: 400;
        color: rgba(0, 0, 0);
        display: flex;
        flex-direction: column;
        gap: 15px;
        .name{
            font-size: 14px;
            line-height: 14px;
            opacity: 0.6;
        }
        .value{
            margin-top: 5px;
            font-size: 13px;
            line-height: 13px;
            opacity: 1;
        }
    }
    .funding-sources{
        margin-top: 15px;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        align-items: end;
        gap: 15px;
        .item::v-deep {
            .progress{
                position: relative;
                display: inline-block;
                width: 100%;
                .label{
                    font-size: 13px;
                    font-weight: 400;
                    color: #000000;
                }
                .label--mobile{
                    font-size: 13px;
                    font-weight: 400;
                    line-height: 13px;
                    margin-top: 5px;
                    margin-bottom: 5px;
                }
                .pb-wrap {
                    position: relative;
                    .progress-text {
                        position: absolute;
                        top: 50%;
                        transform: translateY(-50%);
                        left: 10px;
                        font-weight: 400;
                    }
                    .progress-text--mobile{
                        font-size: 12px;
                        line-height: 12px;
                        transform: translateY(-40%);
                    }
                    .white{
                        color: #ffffff;
                    }
                    .black{
                        color: #000000;
                    }
                }
                
            }
            .ant-progress-inner {
                border-radius: 4px;
            }
            .ant-progress-bg {
                border-radius: 4px !important;
            }
        }
        .trail-color-0::v-deep {
            .ant-progress-inner {
                background-color: #F94A1D33;
            }
        }
        .trail-color-1::v-deep {
            .ant-progress-inner {
                background-color: #80CC3333;
            }
        }
        .trail-color-2::v-deep {
            .ant-progress-inner {
                background-color: #33CCCC33;
            }
        }
        .trail-color-3::v-deep {
            .ant-progress-inner {
                background-color: #8941D033;
            }
        }
    }
}
</style>