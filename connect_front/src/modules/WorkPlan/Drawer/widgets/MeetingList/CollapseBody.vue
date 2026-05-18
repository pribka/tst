<template>
    <div>
        <a-tabs v-model="tab" class="collapse_tabs">
            <a-tab-pane v-if="detail" key="summary" :tab="$t('workplan.day_results')">
                <a-row :gutter="30" type="flex">
                    <a-col :span="isMobile ? 24 : 16" :order="isMobile ? 2 : 1">
                        <div v-if="detail.summary" class="summary_card rounded-lg">
                            <div class="summary_card__header select-none flex items-center justify-between truncate">
                                <h4 class="summary_card__label truncate font-semibold mb-0">
                                    <i class="fi fi-rr-pen-field mr-2" />
                                    {{ $t('workplan.summary_short') }}
                                </h4>
                                <a-button
                                    v-if="canRegenerateSummary"
                                    type="link"
                                    shape="circle"
                                    flaticon
                                    v-tippy
                                    :content="$t('workplan.update_summary')"
                                    icon="fi-rr-rotate-right"
                                    class="summary_card__action ml-2"
                                    :loading="regenerateSummaryLoading"
                                    @click.stop="regenerateSummary" />
                            </div>
                            <div v-html="summaryHtml" @click.stop class="mt-3 mb-2 summary_text" />
                        </div>
                        <div v-else class="summary_card rounded-lg">
                            <div class="summary_card__header select-none flex items-center justify-between truncate">
                                <h4 class="summary_card__label truncate font-semibold mb-0">
                                    <i class="fi fi-rr-pen-field mr-2" />
                                    {{ $t('workplan.summary_short') }}
                                </h4>
                            </div>
                            <div class="mt-3 mb-2 summary_text">
                                <template v-if="detail.records && detail.records.length">
                                    <div class="flex items-center">
                                        <video
                                            v-if="pendingAnimationSrc"
                                            class="summary_alert__anim mr-2 lg:mr-3"
                                            :src="pendingAnimationSrc"
                                            autoplay
                                            loop
                                            muted
                                            playsinline />
                                        <span>{{ $t('workplan.processing_record_summary') }}</span>
                                    </div>
                                </template>
                                <template v-else>
                                    {{ $t('workplan.summary_for_recorded_only') }}
                                </template>
                            </div>
                        </div>
                        <component 
                            v-if="actions && actions.update_intents && actions.update_intents.availability" 
                            :is="intentsComp" 
                            :item="item"
                            :useLocalStore="useLocalStore"
                            :createdHandler="createdHandler"
                            :intentsChangeField="intentsChangeField"
                            :intentDelete="intentDelete"
                            :handlerChangeField="handlerChangeField"
                            :storeKey="storeKey"
                            :detail="detail"  />
                    </a-col>
                    <a-col :span="isMobile ? 24 : 8" :order="isMobile ? 1 : 2">
                        <MembersInfo :detail="detail" :actions="actions" :changeDetailField="changeDetailField" />
                    </a-col>
                </a-row>
            </a-tab-pane>
            <a-tab-pane v-if="detail && detail.summary && detail.records && detail.records.length" key="transcribe" :tab="$t('workplan.transcribe_tab')">
                <TranscribeListItem 
                    v-for="record in detail.records" 
                    :key="record.id" 
                    :meeting="item" 
                    :detail="record" />
            </a-tab-pane>
            <a-tab-pane key="accounting" :tab="$t('workplan.ticket_accounting_tab')">
                <Accounting
                    :meeting="item"
                    :actions="actions"
                    :canReassign="!!(actions && actions.update && actions.update.availability)"
                    @change="changeHandler"
                    @project-reassigned="onProjectReassigned" />
            </a-tab-pane>
        </a-tabs>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

const listType = 'meetingList'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        detail: {
            type: Object,
            default: () => null
        },
        changeDetailField: {
            type: Function,
            default: () => {}
        },
        intentDelete: {
            type: Function,
            default: () => {}
        },
        handlerChangeField: {
            type: Function,
            default: () => {}
        },
        createdHandler: {
            type: Function,
            default: () => {}
        },
        intentsChangeField: {
            type: Function,
            default: () => {}
        },
        useLocalStore: {
            type: Boolean,
            default: false
        },
        onProjectReassigned: {
            type: Function,
            default: () => {}
        },
    },
    components: {
        Accounting: () => import('@apps/vue2MeetingComponent/components/Accounting/index.vue'),
        TranscribeListItem: () => import('./TranscribeListItem.vue'),
        MembersInfo: () => import('./MembersInfo.vue')
    },
    computed: {
        intentsComp() {
            if(this.detail.intents?.length)
                return () => import('./IntentsBlock.vue')
            return null
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        summaryHtml() {
            if (!this.detail.summary) return ''

            return this.detail.summary
                .replace(/(^|\n)\s*(\d+\.)\s*\.?\s*_+/g, '$1$2 ')
                .replace(/_+(\s*\n|$)/g, '$1')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .trim()
                .replace(/^/, '<p>')
                .replace(/$/, '</p>')
        },
        canRegenerateSummary() {
            return Boolean(this.actions?.regenerate_summary?.availability)
        },
        actions() {
            return this.item.actions || null
        },
        tab: {
            get() {
                if(this.useLocalStore)
                    return this.localTab
                return this.item.tab || 'summary'
            },
            set(value) {
                if(this.useLocalStore) {
                    this.localTab = value
                } else {
                    this.$store.commit('workplan/CHANGE_TAB', {
                        storeKey: this.storeKey,
                        value,
                        item: this.item,
                        list: listType
                    })
                }
            }
        },
    },
    data() {
        return {
            showSummary: true,
            localTab: 'summary',
            pendingAnimationSrc: '',
            regenerateSummaryLoading: false
        }
    },
    methods: {
        async loadPendingAnimation() {
            try {
                if (this.$store.state.isSafari) {
                    this.pendingAnimationSrc = `${process.env.BASE_URL}animate/AI_mov.mov`
                    return
                }
                const animationModule = await import('@/assets/animate/AI.webm')
                this.pendingAnimationSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.pendingAnimationSrc = ''
            }
        },
        async regenerateSummary() {
            if (!this.detail?.id || this.regenerateSummaryLoading || !this.canRegenerateSummary) return

            try {
                this.regenerateSummaryLoading = true
                await this.$http.post(`/meetings/sections/${this.detail.id}/regenerate_summary/`)
                this.changeDetailField({
                    field: 'summary',
                    value: ''
                })
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.regenerateSummaryLoading = false
            }
        },
        changeHandler() {

        }
    },
    created() {
        this.loadPendingAnimation()
    }
}
</script>

<style lang="scss" scoped>
.collapse_tabs{
    &.ant-tabs.ant-tabs-top{
        &::v-deep{
            .ant-tabs-bar.ant-tabs-top-bar{
                display: block;
            }
        }
    }
    
}
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}

.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.summary_text{
    &::v-deep{
        p{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.summary_alert__anim {
    width: 22px;
    height: 22px;
    object-fit: contain;
    flex: 0 0 22px;
}
.summary_card__action{
    min-width: 28px;
    height: 28px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
}
.summary_card{
    background: linear-gradient(135deg,  rgba(249,239,255,1) 46%,rgba(240,216,255,1) 100%); /* W3C, IE10+, FF16+, Chrome26+, Opera12+, Safari7+ */
    padding: 10px 15px;
    border: 1px solid #f1dcff;
    &:not(:last-child){
        margin-bottom: 15px;
    }
    @media (min-width: 768px) {
        padding: 10px 20px;
    }
    .summary_card__label{
        display: flex;
        align-items: center;
        font-size: 16px;
        img{
            max-width: 22px;
        }
        @media (min-width: 768px) {
            font-size: 18px;
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
