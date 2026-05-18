<template>
    <a-spin :spinning="loading">
        <template v-if="isMobile">
            <div class="statistic-wrap statistic-wrap--mobile">
                <div class="statistic_item mobile">
                    <div class="total">
                        <div class="info">
                            <div class="label">{{ $t('invest.total') }}</div>
                            <div class="value">{{fundingSourceStatistic?.grand_total}} {{$t('invest.mlnTenge2')}}</div>
                        </div>
                        <div @click="onFRotate" :class="{ 'rotated': isFundingStatOpened }" class="circle-button">
                            <img
                                :data-src="arrow" 
                                class="lazyload" >
                        </div>
                    </div>
                    <transition
                        name="expand"
                        @enter="enter"
                        @after-enter="afterEnter"
                        @leave="leave">
                        <div ref="statGrid" class="st-grid st-grid--mobile" v-show="isFundingStatOpened">
                            <div v-for="(item, index) in fundingSourceStatistic?.statistic" :key="index" class="item">
                                <div class="progress">
                                    <div class="label label--mobile">
                                        {{ item.source }} - {{ item.value }} {{$t('invest.mlnTenge2')}}
                                    </div>
                                    <div class="pb-wrap">
                                        <a-progress
                                            class="custom-progress"
                                            :class="`trail-color-${index}`"
                                            :percent="Number(item.percent)"
                                            :show-info="false"
                                            :strokeWidth="21.45"
                                            :strokeColor="strokeColor(index)" />
                                        <div class="progress-text progress-text--mobile" :class="[
                                            {white: index === 0 || index === 3},
                                            {black: index === 1 || index === 2}
                                        ]">
                                            {{ item.percent }} %
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>
                <div class="statistic_item mobile mt-2.5">
                    <div class="total">
                        <div class="info">
                            <div class="label">{{ $t('invest.total') }}</div>
                            <div class="value">{{ `${categoryStatistic[0]?.total_count} ${projectWord(Number(categoryStatistic[0]?.total_count))}` }}</div>
                        </div>
                        <div @click="onCRotate" :class="{ rotated: isCategoryStatOpened }" class="circle-button">
                            <img
                                :data-src="arrow" 
                                class="lazyload" >
                        </div>
                    </div>
                    <transition
                        name="expand"
                        @enter="enter"
                        @after-enter="afterEnter"
                        @leave="leave">
                        <div ref="statGrid" class="st-grid st-grid--mobile" v-show="isCategoryStatOpened">
                            <div v-for="(item, index) in categoryStatistic" :key="index" class="item">
                                <div class="progress">
                                    <div class="label label--mobile">
                                        {{ item.category.name }} - {{ item.category_count }}
                                    </div>
                                    <div class="pb-wrap">
                                        <a-progress
                                            class="custom-progress"
                                            :class="`trail-color-${index}`"
                                            :percent="Number(item.category_percent)"
                                            :show-info="false"
                                            :strokeWidth="21.45"
                                            :strokeColor="strokeColor(index)" />
                                        <div class="progress-text progress-text--mobile" :class="[
                                            {white: index === 0 || index === 3},
                                            {black: index === 1 || index === 2}
                                        ]">
                                            {{ item.category_percent }} %
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>
            </div>
        </template> 
        <template v-else>
            <div class="statistic-wrap list_grid grid-cols-1 2xl:grid-cols-2">
                <div v-if="fundingSourceStatistic" class="statistic_item">
                    <div class="total">
                        <div class="label">{{ $t('invest.total') }}: </div>
                        <div class="value">
                            <div class="value__count">{{fundingSourceStatistic.grand_total}}</div>
                            <div class="value__measure">{{$t('invest.mlnTenge2')}}</div>
                        </div>
                    </div>
                    <div class="st-grid">
                        <div v-for="(item, index) in fundingSourceStatistic.statistic" :key="index" class="item">
                            <div class="progress">
                                <div class="label">
                                    <div>{{ item.source }}</div>
                                    <div>{{ item.value }} {{$t('invest.mlnTenge2')}}</div>
                                </div>
                                <div class="pb-wrap">
                                    <a-progress
                                        class="custom-progress"
                                        :class="`trail-color-${index}`"
                                        :percent="Number(item.percent)"
                                        :show-info="false"
                                        :strokeWidth="21.45"
                                        :strokeColor="strokeColor(index)" />
                                    <div class="progress-text" :class="[
                                        {white: index === 0 || index === 3},
                                        {black: index === 1 || index === 2}
                                    ]">
                                        {{ item.percent }} %
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="categoryStatistic.length" class="statistic_item">
                    <div class="total">
                        <div class="label">{{ $t('invest.total') }}: </div>
                        <div class="value">
                            <div class="value__count">{{categoryStatistic[0].total_count}}</div>
                            <div class="value__measure">{{ projectWord(Number(categoryStatistic[0].total_count)) }}</div>
                        </div>
                    </div>
                    <div class="st-grid">
                        <div v-for="(item, index) in categoryStatistic" :key="index" class="item">
                            <div class="progress">
                                <div class="label">
                                    <div>{{ item.category.name }}</div>
                                    <div>{{ item.category_count }}</div>
                                </div>
                                <div class="pb-wrap">
                                    <a-progress
                                        class="custom-progress"
                                        :class="`trail-color-${index}`"
                                        :percent="Number(item.category_percent)"
                                        :show-info="false"
                                        :strokeWidth="21.45"
                                        :strokeColor="strokeColor(index)" />
                                    <div class="progress-text" :class="[
                                        {white: index === 0 || index === 3},
                                        {black: index === 1 || index === 2},
                                    ]">
                                        {{ item.category_percent }} %
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </template> 
    </a-spin>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'Statistic',
    data() {
        return {
            categoryStatistic: [],
            fundingSourceStatistic: null,
            isCategoryStatOpened: false,
            isFundingStatOpened: false,
            loading: false,
            model: 'invest_projects_info.InvestProjectInfoModel',
            page_name: 'invest_project_list',
            showFundingStat: false,
            strokeColors: [
                '#F94A1D',
                '#80CC33',
                '#33CCCC',
                '#8941D0'
            ],
        }
    },
    created() {
        this.getStatistic()
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        arrow() {
            return require(`@/assets/images/arrow.svg`)
        },
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.statisticReload()
        })
        eventBus.$on('update_invest_project_statistic', () => {
            this.statisticReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off('update_invest_project_statistic')
    },
    methods: {
        enter(el) {
            el.style.height = 'auto'
            const height = getComputedStyle(el).height
            el.style.height = 0
            setTimeout(() => {
                el.style.height = height
            })
        },
        afterEnter(el) {
            el.style.height = 'auto'
        },
        leave(el) {
            el.style.height = getComputedStyle(el).height
            setTimeout(() => {
                el.style.height = 0
            })
        },
        onFRotate() {
            this.isFundingStatOpened = !this.isFundingStatOpened
        },
        onCRotate() {
            this.isCategoryStatOpened = !this.isCategoryStatOpened
        },
        strokeColor(index) {
            return this.strokeColors[index]
        },
        projectWord(count) {
            const lastDigit = count % 10
            const lastTwoDigits = count % 100

            if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
                return this.$t('invest.invest_proektov_s')
            }
            if (lastDigit === 1) {
                return this.$t('invest.invest_proekt_s')
            }
            if (lastDigit >= 2 && lastDigit <= 4) {
                return this.$t('invest.invest_proekta_s')
            }
            return this.$t('invest.invest_proektov_s')
        },
        statisticReload() {
            this.categoryStatistic = []
            this.fundingSourceStatistic = null
            this.getStatistic()
        },
        async getStatistic() {
            this.loading = true
            const params = {
                page_name: this.page_name
            }
            const categoryStatistics = new Promise((resolve, reject) => {
                this.$http.get('/invest_projects_info/category_statistics/', {
                    params: params
                }).then((response) => resolve(response))
            })
            const fundingSourceStatistics = new Promise((resolve, reject) => {
                this.$http.get('/invest_projects_info/funding_source_statistics/', {
                    params: params
                }).then((response) => resolve(response))
            })
            Promise.all([categoryStatistics, fundingSourceStatistics])
                .then(([categoryStatistics, fundingSourceStatistics]) => {
                    this.categoryStatistic = categoryStatistics.data
                    this.fundingSourceStatistic = fundingSourceStatistics.data
                })
                .catch(error => {
                    console.log(error)
                    this.$message.error(this.$t('invest.invest_statistika_alynbaidy'))
                })
                .finally(() => {
                    this.loading = false
                })
        },
    }
}
</script>
<style lang="scss" scoped>
.statistic-wrap{
    width: 100%;
    margin-bottom: 20px;
    min-height: 88px;
    .statistic_item{
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        padding: 10px;
        display: flex;
        gap: 14px;
        align-items: flex-end;
        .st-grid {
            display: grid;
            width: 100%;
            grid-template-columns: repeat(4, 1fr);
            align-items: flex-end;
            gap: 14px;
            @media (max-width: 1000px) {
                grid-template-columns: repeat(2, 1fr);
                grid-template-rows: repeat(2, 1fr);
            }
        }
        .st-grid--mobile{
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: auto;
            gap: 10px;
            .item:nth-child(-n+2) {
                margin-top: 15px;
            }
        }
        .expand-enter-active, .expand-leave-active {
            transition: height 0.3s;
            overflow: hidden;
        }
        .total{
            display: flex;
            flex-direction: column;
            gap: 10px;
            flex-shrink: 0;
            min-width: 12%;
            .label{
                color: #000000;
                font-size: 16px;
                font-weight: 400;
                opacity: 0.6;
            }
            .value{
                display: flex;
                flex-direction: column;
                &__count, &__measure {
                    font-weight: 400;
                }
                &__count{
                    font-size: 32px;
                    line-height: 32px;
                    text-wrap: nowrap;
                }
                &__measure{
                    font-size: 16px;
                }
            }
        }
        .item::v-deep {
            .progress{
                position: relative;
                display: inline-block;
                width: 100%;
                .label{
                    font-size: 14px;
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
                        transform: translateY(-35%);
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
    .mobile {
        background-color: rgba(255, 255, 255, 1);
        border: 1px solid rgba(235, 235, 235, 1);
        border-radius: 8px;
        padding: 15px 20px;
        min-height: 50px;
        display: block;
        .total{
            display: flex;
            width: 100%;
            justify-content: space-between;
            flex-direction: row;
            align-items: flex-end;
            .info{
                display: flex;
                gap: 0.3rem;
                font-size: 16px;
                font-weight: 400;
                line-height: 16px;
                .label {
                    color: rgba(0, 0, 0, 0.6);
                }
                .value {
                    color: rgba(29, 101, 192, 1);
                }
            }
            .circle-button {
                width: 18px;
                height: 18px;
                font-size: 14px;
                background-color: blue;
                color: white;
                border: none;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transform: rotate(-90deg);
                transition: transform 0.3s ease;
            }
            .circle-button.rotated {
                transform: rotate(0deg);
            }
        }
    }
}
.statistic-wrap--mobile{
    margin-bottom: 30px;
    min-height: unset;
}
.list_grid{
    display: grid;
    gap: 15px;
}
</style>