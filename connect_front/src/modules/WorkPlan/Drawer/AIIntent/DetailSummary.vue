<template>
    <div :class="isMobile ? 'mb-4' : 'mb-5'">
        <div class="block_label" v-html="intentsText" />
        <div 
            v-if="notStatEmpty" 
            class="flex items-center flex-wrap mt-1" 
            :class="isMobile ? 'gap-2' : 'gap-4'"
            :style="isMobile && 'flex-direction: column;align-items: normal;'">
            <div v-if="dayStatistics.intents.accepted" class="flex items-center">
                <i class="fi fi-rr-check-circle mr-1" style="color: #277c49;" />
                {{ $t('workplan.processed') }} <span class="ml-2" style="color: #277c49;font-weight: 700;">{{ dayStatistics.intents.accepted }}</span>
            </div>
            <div v-if="dayStatistics.intents.unprocessed" class="flex items-center">
                <i class="fi fi-rr-clock mr-1" style="color: #753611;" />
                {{ $t('workplan.unprocessed') }} <span class="ml-2" style="color: #753611;font-weight: 700;">{{ dayStatistics.intents.unprocessed }}</span>
            </div>
            <div v-if="dayStatistics.intents.deleted" class="flex items-center">
                <i class="fi fi-rr-trash mr-1" style="color: #bc1f1f;" />
                {{ $t('workplan.deleted_label') }} <span class="ml-2" style="color: #bc1f1f;font-weight: 700;">{{ dayStatistics.intents.deleted }}</span>
            </div>
        </div>
    </div>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        dayStatistics() {
            return this.$store.state.workplan.ai_intents?.[this.storeKey]?.data || null
        },
        notStatEmpty() {
            return this.dayStatistics?.intents?.accepted || this.dayStatistics?.intents?.deleted || this.dayStatistics?.intents?.unprocessed ? true : false
        },
        intentsText() {
            if (!this.dayStatistics) return ''
            const { intents, sections_count } = this.dayStatistics
            const parts = []

            parts.push(
                `<p>
                    ${this.$t('workplan.intents_found', { count: `<span>${intents.total}</span> ${declOfNum(intents.total, [this.$t('workplan.intent_one'), this.$t('workplan.intent_few'), this.$t('workplan.intent_many')])}` })}
                    ${this.$t('workplan.from_meetings', { count: `<span>${sections_count}</span> ${declOfNum(sections_count, [this.$t('workplan.meetings_one'), this.$t('workplan.meetings_few'), this.$t('workplan.meetings_many')])}` })}
                </p>`
            )

            return parts.join('')
        }
    }
}
</script>

<style lang="scss" scoped>
.block_label{
    font-weight: 600;
    font-size: 16px;
}
</style>
