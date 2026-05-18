<template>
    <div class="consolidation_ai_summary">
        <div class="consolidation_ai_summary__body">
            <a-spin :spinning="summariesLoading && !summariesList.length" class="w-full">
                <transition-group
                    v-if="firstSummary"
                    name="slide-down"
                    tag="div"
                    class="pending_list">
                    <div
                        :key="firstSummary?.id || 'first-summary'"
                        class="rounded-lg">
                        <div v-if="firstSummary?.status === 'pending'" class="summary_alert rounded-lg">
                            <video
                                v-if="pendingAnimationWebmSrc || pendingAnimationMovSrc"
                                class="summary_alert__anim"
                                autoplay
                                loop
                                muted
                                playsinline>
                                <source
                                    v-if="pendingAnimationWebmSrc"
                                    :src="pendingAnimationWebmSrc"
                                    type="video/webm" />
                                <source
                                    v-if="pendingAnimationMovSrc"
                                    :src="pendingAnimationMovSrc"
                                    type="video/quicktime" />
                            </video>
                            <div class="summary_alert__body">
                                <div>{{ $t('workplan.ai_consolidation_pending_alert') }}</div>
                                <div class="summary_alert__meta">
                                    {{ formatPendingMeta(firstSummary) }}
                                </div>
                            </div>
                        </div>
                        <div v-else class="summary_card rounded-lg">
                            <div class="summary_card__head mb-2">
                                <div class="summary_alert__meta flex items-center">
                                    <img src="@/assets/svg/ai_icons.svg" class="mr-2" />
                                    {{ formatPendingMeta(firstSummary) }}
                                </div>
                                <div class="summary_card__actions">
                                    <a-button
                                        type="link"
                                        flaticon
                                        v-tippy
                                        shape="circle"
                                        :content="$t('workplan.copy_text')"
                                        icon="fi-rr-copy-alt"
                                        @click.stop="textCopy(summaryToPlainText(firstSummary?.summary || $t('workplan.ai_consolidation_empty_summary')))" />
                                    <a-button
                                        type="link"
                                        flaticon
                                        v-tippy
                                        shape="circle"
                                        :content="$t('workplan.print_text')"
                                        icon="fi-rr-print"
                                        @click.stop="textPrint(firstSummary)" />
                                </div>
                            </div>
                            <div
                                v-if="firstSummary?.error_message"
                                class="summary_card__error mb-2"
                                v-html="firstSummary.error_message" />
                            <div
                                v-else
                                class="summary_card__text"
                                v-html="formatSummaryHtml(firstSummary?.summary || $t('workplan.ai_consolidation_empty_summary'))" />
                        </div>
                    </div>
                </transition-group>

                <div v-if="canRequest && !summariesList.length && !summariesLoading" class="summary_alert summary_alert--hint rounded-lg">
                    <img src="@/assets/svg/ai_icons.svg" class="summary_alert__icon" />
                    <div class="summary_alert__body">
                        <div>{{ emptyDescription }}</div>
                    </div>
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        scope: {
            type: String,
            default: null
        },
        relatedObjectId: {
            type: [String, Number],
            default: null
        },
        relatedObjectSummaryValue: {
            type: String,
            default: ''
        },
        startDate: {
            type: String,
            default: null
        },
        endDate: {
            type: String,
            default: null
        },
        canRequest: {
            type: Boolean,
            default: false
        },
        isMobile: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            generateLoading: false,
            summariesLoading: false,
            summariesList: [],
            summariesPageSize: 1,
            pendingAnimationWebmSrc: '',
            pendingAnimationMovSrc: ''
        }
    },
    computed: {
        filtersRequestKey() {
            return [
                this.scope || '',
                this.relatedObjectSummaryValue || '',
                this.startDate || '',
                this.endDate || ''
            ].join('|')
        },
        firstSummary() {
            return this.summariesList[0] || null
        },
        emptyDescription() {
            if (!this.scope || !this.relatedObjectSummaryValue)
                return this.$t('workplan.ai_consolidation_select_filters')
            return this.$t(`workplan.${this.generateHintKey}`)
        },
        generateHintKey() {
            const map = {
                organization: 'ai_consolidation_generate_hint_organization',
                root_organization: 'ai_consolidation_generate_hint_root_organization',
                project: 'ai_consolidation_generate_hint_project',
                workgroup: 'ai_consolidation_generate_hint_workgroup',
                user: 'ai_consolidation_generate_hint_user'
            }
            return map[this.scope] || 'ai_consolidation_generate_hint'
        }
    },
    sockets: {
        async notify({ data }) {
            if (data?.event_type !== 'new_notification') return

            const { linkType, query } = this.parseNotificationLinkData(data?.obj)
            if (linkType !== 'workplan-ai-consolidation') return
            if (!query?.related_object_id || !query?.scope) return

            const sameScope = String(this.scope || '') === String(query.scope || '')
            const sameRelatedObject = String(this.relatedObjectSummaryValue || '') === String(query.related_object_id || '')
            const sameStart = String(this.startDate || '') === String(query.start_date || '')
            const sameEnd = String(this.endDate || '') === String(query.end_date || '')

            if (sameScope && sameRelatedObject && sameStart && sameEnd)
                await this.reloadSummaries()
        }
    },
    watch: {
        filtersRequestKey: {
            immediate: true,
            handler() {
                this.fetchSummariesOnFilters()
            }
        }
    },
    created() {
        this.loadPendingAnimation()
    },
    methods: {
        async loadPendingAnimation() {
            try {
                const animationModule = await import('@/assets/animate/AI.webm')
                this.pendingAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.pendingAnimationWebmSrc = ''
            }
            this.pendingAnimationMovSrc = `${process.env.BASE_URL}animate/AI_mov.mov`
        },
        formatScope(scope) {
            const map = {
                organization: this.$t('workplan.filter_organization'),
                root_organization: this.$t('workplan.filter_root_organization'),
                project: this.$t('workplan.filter_project'),
                workgroup: this.$t('workplan.filter_team'),
                user: this.$t('workplan.filter_user')
            }
            return map[scope] || scope || '-'
        },
        formatPendingMeta(item = {}) {
            return `${this.formatScope(item?.scope)}`
        },
        hasHtmlContent(text) {
            return /<\/?[a-z][\s\S]*>/i.test(String(text || ''))
        },
        escapeHtml(text) {
            return String(text || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
        },
        formatSummaryHtml(text) {
            const summary = String(text || '')
            if (!summary) return ''
            if (this.hasHtmlContent(summary)) return summary
            return this.escapeHtml(summary).replace(/\n/g, '<br>')
        },
        summaryToPlainText(text) {
            const summary = String(text || '')
            if (!summary) return ''
            if (!this.hasHtmlContent(summary)) return summary

            const container = document.createElement('div')
            container.innerHTML = summary
            return (container.textContent || container.innerText || '').trim()
        },
        parseNotificationLinkData(notification = {}) {
            const localizedMessage = notification?.[`message_${this.$i18n.locale}`]
            const message = localizedMessage || notification?.message || ''
            if (!message) return { linkType: null, query: null }

            const typeMatch = message.match(/data-link-type='([^']+)'/) || message.match(/data-link-type="([^"]+)"/)
            const linkType = typeMatch?.[1] || null

            const queryMatch = message.match(/data-link-query='([^']+)'/) || message.match(/data-link-query="([^"]+)"/)
            const encodedQuery = queryMatch?.[1]
            if (!encodedQuery) return { linkType, query: null }

            try {
                const decodedQuery = encodedQuery
                    .replace(/&quot;/g, '"')
                    .replace(/&#39;/g, '\'')
                    .replace(/&amp;/g, '&')
                return { linkType, query: JSON.parse(decodedQuery) }
            } catch (e) {
                return { linkType, query: null }
            }
        },
        async fetchSummariesList({ page = 1, append = false } = {}) {
            if (!this.canRequest || !this.relatedObjectSummaryValue) {
                this.summariesList = []
                return
            }

            const params = {
                start: this.startDate,
                end: this.endDate,
                scope: this.scope,
                related_object: this.relatedObjectSummaryValue,
                page,
                page_size: this.summariesPageSize
            }

            try {
                this.summariesLoading = true
                const { data } = await this.$http.get('/analytics/summaries/', { params })
                const results = Array.isArray(data?.results)
                    ? data.results
                    : (Array.isArray(data) ? data : [])
                this.summariesList = append ? this.summariesList.concat(results) : results
            } catch (error) {
                this.summariesList = []
                errorHandler({ error, show: false })
            } finally {
                this.summariesLoading = false
            }
        },
        async reloadSummaries() {
            await this.fetchSummariesList({ page: 1, append: false })
        },
        async fetchSummariesOnFilters() {
            if (!this.canRequest) {
                this.summariesList = []
                return
            }
            await this.reloadSummaries()
        },
        async generateSummary() {
            if (!this.canRequest || !this.relatedObjectSummaryValue) return

            const payload = {
                start: this.startDate,
                end: this.endDate,
                related_object: this.relatedObjectSummaryValue,
                scope: this.scope
            }

            try {
                this.generateLoading = true
                this.$emit('generate-loading-change', true)
                await this.$http.post('/analytics/summaries/', payload)
                this.$message.success(this.$t('workplan.ai_consolidation_started'))
                await this.reloadSummaries()
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.generateLoading = false
                this.$emit('generate-loading-change', false)
            }
        },
        textCopy(text) {
            navigator.clipboard.writeText(text || '')
                .then(() => {
                    this.$message.success(this.$t('workplan.text_copied'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('workplan.copy_link_failed'))
                })
        },
        textPrint(item = {}) {
            const printWindow = window.open('', '_blank')
            if (!printWindow) return

            const title = this.$t('workplan.print_text')
            const heading = this.formatPendingMeta(item)
            const body = this.formatSummaryHtml(item?.summary || '-')

            printWindow.document.write(`
                <html>
                    <head>
                        <title>${title}</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                padding: 20px;
                                line-height: 1.6;
                                word-break: break-word;
                            }
                            h3 {
                                margin-bottom: 12px;
                            }
                            p {
                                margin: 0 0 12px;
                            }
                            ul, ol {
                                margin: 0 0 12px;
                                padding-left: 20px;
                            }
                            li + li {
                                margin-top: 6px;
                            }
                        </style>
                    </head>
                    <body>
                        <h3>${heading}</h3>
                        <div>${body}</div>
                    </body>
                </html>
            `)

            printWindow.document.close()
            printWindow.focus()
            printWindow.print()
            printWindow.close()
        }
    }
}
</script>

<style lang="scss" scoped>
.consolidation_ai_summary{
    margin-bottom: 18px;
}

.pending_list{
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.summary_alert{
    background: linear-gradient(135deg, rgb(249, 239, 255) 46%, rgb(240, 216, 255) 100%);
    padding: 10px 15px;
    border: 1px solid #f1dcff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.summary_card{
    background: linear-gradient(135deg, rgba(249,239,255,1) 46%, rgba(240,216,255,1) 100%);
    padding: 10px 15px;
    border: 1px solid #f1dcff;
}

.summary_card__head{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.summary_card__actions{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

.summary_card__text{
    margin: 0;
    word-break: break-word;
    line-height: 1.6;
    &::v-deep{
        p{
            margin: 0 0 12px;
        }
        ul, ol{
            margin: 0 0 12px;
            padding-left: 20px;
        }
        li + li{
            margin-top: 6px;
        }
        strong{
            font-weight: 600;
        }
        p:last-child,
        ul:last-child,
        ol:last-child{
            margin-bottom: 0;
        }
    }
}

.summary_card__error{
    padding: 8px 10px;
    border-radius: 8px;
    background: #fff2f2;
    color: #b42318;
    white-space: pre-wrap;
    word-break: break-word;
}

.summary_alert--hint{
    align-items: center;
}

.summary_alert__icon{
    width: 26px;
    max-width: 26px;
    flex: 0 0 26px;
}

.summary_alert__anim{
    width: 22px;
    height: 22px;
    object-fit: contain;
    flex: 0 0 22px;
}

.summary_alert__body{
    min-width: 0;
}

.summary_alert__meta{
    margin-top: 2px;
    color: var(--text_grey);
    font-size: 12px;
    img{
        max-width: 26px;
    }
}

.slide-down-enter-active,
.slide-down-leave-active {
    transition: opacity .25s ease, transform .25s ease;
}

.slide-down-enter,
.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-14px);
}

</style>
