<template>
    <div class="intent_card" :class="item.collapse && 'active'">
        <div class="intent_card__header flex items-center justify-between truncate rounded-lg" @click="toggleCollapse(index)">
            <div class="truncate">
                <div class="font-semibold truncate">{{ item.meeting.name }}</div>
                <div 
                    v-if="item.intents && item.intents.length" 
                    class="mt-1 intents_card_desc"
                    v-html="cardIntentsDescription" />
            </div>
            <div class="ml-2 flex items-center gap-2">
                <a-button 
                    v-if="item.meeting && item.meeting.id"
                    type="link" 
                    flaticon 
                    v-tippy
                    :content="$t('workplan.open_meeting')"
                    shape="circle"
                    icon="fi-rr-arrow-up-right-from-square"
                    @click.stop="openMeeting()" />
                <i class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5; font-size: 16px;" />
            </div>
        </div>
        <div v-if="item.collapse" class="intent_card__body">
            <Segmented 
                v-if="isMobile"
                block
                class="mb-2"
                v-model="viewType" 
                :options="listType" />
            <a-row :gutter="isMobile ? 0 : 30">
                <a-col v-if="showTranscribe" :sm="isMobile ? 24 : 12" :lg="isMobile ? 24 : 12" :xl="isMobile ? 24 : 12" :xxl="isMobile ? 24 : 12" :order="isMobile ? 1 : 0">
                    <div v-if="!isMobile" class="card_row_label flex items-center" style="opacity: 0.8;">
                        <i class="fi fi-rr-poll-h mr-2" />
                        {{ $t('workplan.transcribe_tab') }}
                    </div>
                    <div class="text_card rounded-lg">
                        <component 
                            v-if="item.summary" 
                            :is="summaryBlockComp"
                            :summary="item.summary" 
                            useCollapse 
                            :useMore="false" 
                            smallBlock />
                        <template v-if="item.transcribe">
                            <TranscribeListItem 
                                v-for="record in item.records" 
                                :key="record.id" 
                                :meeting="item.meeting" 
                                :detail="record" />
                        </template>
                        <a-empty v-else :description="$t('workplan.transcribe_none')" class="mb-4" />
                    </div>
                </a-col>
                <a-col v-if="showIntents" :sm="isMobile ? 24 : 12" :lg="isMobile ? 24 : 12" :xl="isMobile ? 24 : 12" :xxl="isMobile ? 24 : 12" :order="isMobile ? 0 : 1">
                    <div v-if="!isMobile" class="card_row_label flex items-center" style="opacity: 0.8;">
                        <i class="fi fi-rr-list-check mr-2" />
                        {{ $t('workplan.intents_found_title') }} <template v-if="item.intents.length">({{ item.intents.length }})</template>
                    </div>
                    <div v-if="item.intents && item.intents.length" class="intents_sw_list">
                        <component 
                            v-for="(intents, index) in item.intents" 
                            :is="IntentsSwitchComp"
                            useInject
                            :key="intents.id"
                            :injectDelete="deleteHandler"
                            :messageIndex="index"
                            :injectUpdate="injectUpdate"
                            :injectCreated="createdHandler"
                            :injectChangeField="handlerChangeField"
                            :intents="intents"
                            :intentIndex="index"
                            :message="{name: 'message'}" />
                    </div>
                    <div v-else class="text_card rounded-lg">
                        <a-empty :description="$t('workplan.intents_none')" class="mb-4" />
                    </div>
                </a-col>
            </a-row>
        </div>
    </div>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        index: {
            type: Number,
            default: 0
        },
        toggleCollapse: {
            type: Function,
            default: () => {}
        },
        intentDelete: {
            type: Function,
            default: () => {}
        },
        intentChangeField: {
            type: Function,
            default: () => {}
        },
        intentEditField: {
            type: Function,
            default: () => {}
        },
        createdHandler: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        TranscribeListItem: () => import('../widgets/MeetingList/TranscribeListItem.vue')
    },
    data() {
        return {
            viewType: "intents",
            listType: [
                {
                    key: 'intents',
                    title: this.$t('workplan.intents_tab')
                },
                {
                    key: 'transcribe',
                    title: this.$t('workplan.transcribe_tab')
                }
            ]
        }
    },
    computed: {
        summaryBlockComp() {
            if(this.item.summary)
                return () => import('../widgets/MeetingList/SummaryBlock.vue')
            return null
        },
        IntentsSwitchComp() {
            if(this.item.collapse)
                return () => import('@apps/AIAssistant/Drawer/Message/IntentsSwitch.vue')
            return null
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        showIntents() {
            if(!this.isMobile) return true
            else
                return this.viewType === 'intents' ? true : false
        },
        showTranscribe() {
            if(!this.isMobile) return true
            else
                return this.viewType === 'transcribe' ? true : false
        },
        cardIntentsDescription() {
            return `${this.$t('workplan.intents_found', { count: `<span>${this.item.intents.length}</span> ${declOfNum(this.item.intents.length, [this.$t('workplan.intent_one'), this.$t('workplan.intent_few'), this.$t('workplan.intent_many')])}` })}`
        }
    },
    methods: {
        injectUpdate({ widgetKey, index, intentIndex, messageIndex, value, useRepr }) {
            this.intentEditField({
                widgetKey,
                index,
                listIndex: this.index,
                intentIndex,
                messageIndex,
                value,
                useRepr
            })
        },
        openMeeting() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.meeting = this.item.meeting.id
            this.$router.push({ query })
        },
        meetingReload() {
            this.$store.dispatch('workplan/updateItem', {
                item: this.item.meeting,
                list: 'meetingList'
            })
        },
        deleteHandler({ intentId }) {
            this.meetingReload()
            this.intentDelete({ listIndex: this.index, intentId })
        },
        handlerChangeField({ intentId, value, field }) {
            this.meetingReload()
            this.intentChangeField({ intentId, value, field, listIndex: this.index })
        }
    }
}
</script>

<style lang="scss" scoped>
.intents_card_desc{
    opacity: 0.8;
    font-size: 13px;
    &::v-deep{
        span{
            font-weight: 600;
        }
    }
}
.card_row_label{
    font-weight: 600;
    margin-bottom: 15px;
}
.text_card{
    padding: 15px;
    background: #fff;
    @media (min-width: 768px) {
        padding: 20px;
    }
}
.intents_sw_list{
    &::v-deep{
        .intents_card{
            border-radius: 0.5rem;
            &:not(:last-child){
                @media (min-width: 768px) {
                    margin-bottom: 15px;
                }
            }
        }
    }
}
.intent_card{
    &:not(:last-child){
        margin-bottom: 15px;
    }
    &__header{
        padding: 15px;
        cursor: pointer;
        background: #fff;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    &__body{
        padding-top: 15px;
        @media (min-width: 768px) {
            padding-top: 20px;
        }
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.active{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
}
</style>
