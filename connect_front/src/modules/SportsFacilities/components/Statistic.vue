<template>
    <a-spin :spinning="loading" class="stat_spin">
        <div class="sports_facilities_stat md:grid md:gap-4 grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            <div class="stat_card" @click="openStatDrawer()">
                <div class="stat_card__info">
                    <div class="count">{{ statInfo.count }}</div>
                    <div class="label">{{$t('sports.all_object')}}</div>
                </div>
                <div v-if="!isMobile" class="stat_card__button">
                    <div class="flex items-center more_btn">
                        {{ $t('sports.more') }}
                        <i class="fi fi-rr-arrow-up-right ml-3 text-xs"></i>
                    </div>
                </div>
            </div>
            <div class="stat_card" @click="openStatDrawer()">
                <div class="stat_card__info">
                    <div class="count">{{ statInfo.renovation_info ? priceFormatter(statInfo.renovation_info.amount_sum) : 0 }}</div>
                    <div class="label">{{ $t('sports.repair_price') }}</div>
                </div>
                <div v-if="!isMobile" class="stat_card__button">
                    <div class="flex items-center more_btn">
                        {{ $t('sports.more') }}
                        <i class="fi fi-rr-arrow-up-right ml-3 text-xs"></i>
                    </div>
                </div>
            </div>
            <div class="stat_card" @click="openStatDrawer()">
                <div class="stat_card__info">
                    <div class="count">{{ statInfo.count_facility_types }}</div>
                    <div class="label">{{ $t('sports.all_sport_object') }}</div>
                </div>
                <div v-if="!isMobile" class="stat_card__button">
                    <div class="flex items-center more_btn">
                        {{ $t('sports.more') }}
                        <i class="fi fi-rr-arrow-up-right ml-3 text-xs"></i>
                    </div>
                </div>
            </div>
        </div>
    </a-spin>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { priceFormatter } from '@/utils/index'
export default {
    props: {
        statusFilter: {
            type: String,
            default: ''
        },
        page_name: {
            type: String,
            default: ''
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            statInfo: {
                count: 0,
                count_facility_types: 0,
                renovation_amount: 0
            }
        }
    },
    methods: {
        priceFormatter,
        openStatDrawer() {
            eventBus.$emit('viewStatDrawer', this.statInfo)
        },
        async getStat() {
            try {
                this.loading = true
                const params = {
                    page_name: this.page_name
                }
                if(this.statusFilter) {
                    params.filters = {
                        status: this.statusFilter
                    }
                }
                const { data } = await this.$http.get('/sports_facilities/aggregate/', { params })
                if(data) {
                    this.statInfo = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        this.getStat()
    }
}
</script>

<style lang="scss" scoped>
.stat_spin{
    @media (max-width: 767.98px) {
        margin-left: -15px;
        margin-right: -15px;
    }
}
.sports_facilities_stat{
    @media (max-width: 767.98px) {
        display: -webkit-box;
        margin-bottom: 0;
        overflow-x: scroll;
        padding-left: 15px;
        padding-right: 15px;
        width: 100%;
        -ms-overflow-style: none;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
    }
    @media (min-width: 768px) {
        padding-bottom: 20px;
    }
    .stat_card{
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        background: #FFF3EC;
        border-radius: 8px;
        padding: 10px;
        color: var(--text);
        cursor: pointer;
        @media (max-width: 767.98px) {
            min-width: 310px;
            &:not(:last-child){
                margin-right: 8px;
            }
        }
        @media (min-width: 768px) {
            padding: 15px;
        }
        .count{
            font-size: 24px;
            font-weight: 400;
            line-height: 24px;
            color: #EF7B16;
            margin-bottom: 5px;
        }
        .more_btn{
            cursor: pointer;
            .fi{
                font-size: 10px;
            }
        }
    }
}
</style>