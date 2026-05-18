<template>
    <a-spin class="w-full" :spinning="statisticsLoading" size="small">
        <transition name="fade">
            <div v-if="noEmpty" class="ai_intent rounded-lg select-none" @click="showDetail()">
                <div>
                    <div class="ai_intent__label">
                        <div class="flex items-center">
                            <img src="@/assets/svg/ai_icons.svg" class="mr-2" />
                            {{ $t('workplan.ai_recommendations') }}
                        </div>
                        <i v-if="isMobile" class="fi fi-rr-arrow-small-right ml-2" />
                    </div>
                    <div class="ai_intent__text" v-html="intentsText" />
                    <div v-if="!isMobile" class="ai_intent__btn">
                        <a-button type="link" size="small" class="px-0 flex items-center">
                            {{ $t('workplan.show') }}
                            <i class="fi fi-rr-arrow-small-right ml-2" />
                        </a-button>
                    </div>
                </div>
            </div>
        </transition>
        <DetailDrawer 
            :storeKey="storeKey" 
            :reloadOnKeyData="reloadOnKeyData"
            :intentsStatReload="intentsStatReload"
            ref="detailDrawer" />
    </a-spin>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        reloadOnKeyData: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        DetailDrawer: () => import('./DetailDrawer.vue')
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        dayStatistics() {
            return this.$store.state.workplan.ai_intents?.[this.storeKey]?.data || null
        },
        noEmpty() {
            return this.dayStatistics?.intents?.total && this.dayStatistics?.sections_count
        },
        statisticsLoading() {
            return this.$store.state.workplan.ai_intents?.[this.storeKey]?.loading || false
        },
        isLoading() {
            if(this.dayStatistics)
                return this.statisticsLoading
            return false
        },
        intentsText() {
            if (!this.dayStatistics) return ''
            const { intents, sections_count } = this.dayStatistics
            const parts = []

            parts.push(
                `<p>
                    ${this.$t('workplan.intents_found', { count: `<span>${intents.total}</span> ${declOfNum(intents.total, [this.$t('workplan.intent_one'), this.$t('workplan.intent_few'), this.$t('workplan.intent_many')])}` })}
                    ${this.$t('workplan.from_meetings', { count: `<span>${sections_count}</span> ${declOfNum(sections_count, [this.$t('workplan.meetings_one'), this.$t('workplan.meetings_few'), this.$t('workplan.meetings_many')])}` })}.
                </p>`
            )

            if (intents.unprocessed) {
                parts.push(
                    `<p>
                        ${this.$t('workplan.intents_unprocessed', { count: `<span>${intents.unprocessed}</span>` })}.
                    </p>`
                )
            }

            return parts.join('')
        }
    },
    methods: {
        intentsStatReload() {
            this.$store.dispatch('workplan/getAIIntents', { storeKey: this.storeKey }) 
        },
        showDetail() {
            this.$nextTick(() => {
                if(this.$refs.detailDrawer)
                    this.$refs.detailDrawer.drawerOpen()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to /* .fade-leave-active below version 2.1.8 */ {
  opacity: 0;
}
.ai_intent{
    margin-bottom: 15px;
    /* Permalink - use to edit and share this gradient: https://colorzilla.com/gradient-editor/#f9efff+46,f0d8ff+100 */
    background: linear-gradient(135deg,  rgba(249,239,255,1) 46%,rgba(240,216,255,1) 100%); /* W3C, IE10+, FF16+, Chrome26+, Opera12+, Safari7+ */
    padding: 10px 15px;
    cursor: pointer;
    border: 1px solid #f1dcff;
    @media (min-width: 768px) {
        padding: 20px;
    }
    &__label{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 18px;
        font-weight: 600;
        color: #000;
        img{
            max-width: 26px;
        }
        .fi{
            color: var(--blue);
            font-size: 24px;
        }
    }
    &__text{
        margin-bottom: 5px;
        &::v-deep{
            span{
                color: var(--blue);
                font-weight: 600;
            }
        }
    }
}
</style>
