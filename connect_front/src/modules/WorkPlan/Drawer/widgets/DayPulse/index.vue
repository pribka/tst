<template>
    <div class="day_pulse" :class="useInject && 'day_pulse_inject'">
        <div class="day_pulse__top">
            <div class="day_pulse__top_left">
                <a-button type="flat_primary" :block="isMobile" flaticon icon="fi-rr-plus" @click="openCreateModal">
                    {{ $t('workplan.day_pulse_add_block') }}
                </a-button>
            </div>
            <ai-button
                type="ui"
                class="refresh_btn"
                :block="isMobile"
                @click="openRefreshModal">
                {{ $t('workplan.day_pulse_refresh_summary') }}
            </ai-button>
        </div>

        <transition name="slide-down">
            <div v-if="showPendingAlert" class="mb-2 summary_alert rounded-lg">
                <video
                    v-if="pendingAnimationWebmSrc || pendingAnimationMovSrc"
                    class="summary_alert__anim"
                    autoplay
                    loop
                    muted
                    playsinline>
                    <source v-if="pendingAnimationWebmSrc" :src="pendingAnimationWebmSrc" type="video/webm">
                    <source v-if="pendingAnimationMovSrc" :src="pendingAnimationMovSrc" type="video/quicktime">
                </video>
                <span>{{ $t('workplan.day_pulse_pending_alert') }}</span>
            </div>
        </transition>

        <template v-if="list.page === 1 && list.loading">
            <CardLoading v-for="i in 5" :key="i" :useInject="useInject" />
        </template>
        <template v-else>
            <template v-if="list.results.length">
                <div class="notes_list">
                    <NoteCard
                        v-for="item in list.results"
                        :key="item.id"
                        :note="item"
                        :storeKey="storeKey"
                        :useInject="useInject"
                        @edit-note="openEditModal"
                        @note-deleted="onNoteDeleted" />
                </div>

                <a-button
                    v-if="list.results.length && list.next"
                    :loading="list.loading"
                    type="flat_primary"
                    block
                    @click="nextLoading">
                    {{ $t('workplan.load_more') }}
                </a-button>
            </template>

            <div v-else class="empty_wrap">
                <a-empty :description="$t('workplan.day_pulse_empty')" />
            </div>

            <div
                :key="`publish-${selectedDate || 'none'}-${notesCount}-${String(isPublished)}-${publishStateLoading ? 1 : 0}`"
                v-show="isSingleDayRange && !publishStateLoading && isPublished === false && notesCount > 0"
                class="bottom_actions">
                <a-button
                    type="primary"
                    size="large"
                    class="flex items-center justify-center publish_day_btn"
                    shape="round"
                    :loading="publishLoading"
                    @click="publishNotes">
                    {{ $t('workplan.day_pulse_publish_btn') }}
                </a-button>
            </div>
        </template>

        <NoteModal
            v-model="noteModalVisible"
            :editNote="editNote"
            :selectedDate="selectedDate"
            :storeKey="storeKey" />

        <a-modal
            :visible="refreshModalVisible"
            :width="isMobile ? '100%' : 500"
            :title="$t('workplan.day_pulse_modal_title')"
            destroyOnClose
            @cancel="closeRefreshModal">
            <component
                :is="refreshRangeComponent"
                v-model="refreshForm.range" />

            <div class="refresh_presets">
                <a-button
                    v-for="preset in refreshPresets"
                    :key="preset.label"
                    size="small"
                    type="ui"
                    v-tippy
                    :content="`${preset.range[0].format('DD.MM.YYYY')} - ${preset.range[1].format('DD.MM.YYYY')}`"
                    @click="setRefreshPreset(preset.range)">
                    {{ preset.label }}
                </a-button>
            </div>

            <template #footer>
                <div class="w-full flex items-center justify-end gap-2">
                    <a-button size="large" :block="isMobile" type="ui_ghost" @click="closeRefreshModal">{{ $t('close') }}</a-button>
                    <a-button
                        type="primary"
                        :block="isMobile"
                        size="large"
                        :loading="refreshLoading"
                        @click="refreshSummary">
                        {{ $t('workplan.day_pulse_refresh_summary') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

const listType = 'dayPulseList'

export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        AiButton: () => import('@apps/UIModules/AIButton/index.vue'),
        NoteCard: () => import('./components/NoteCard.vue'),
        NoteModal: () => import('./components/NoteModal.vue'),
        CardLoading: () => import('./components/CardLoading.vue'),
        RefreshRangeInput: () => import('./components/RefreshRangeInput.vue'),
        RefreshMobileRangeInput: () => import('./components/RefreshMobileRangeInput.vue')
    },
    data() {
        return {
            refreshLoading: false,
            publishLoading: false,
            isPublished: null,
            publishStateLoading: false,
            publishStateRequestId: 0,
            pendingCheckRequestId: 0,
            hasPendingSummary: false,
            pendingSummaries: [],
            noteModalVisible: false,
            editNote: null,
            lastLoadedListKey: '',
            refreshModalVisible: false,
            refreshForm: {
                range: []
            },
            pendingAnimationWebmSrc: '',
            pendingAnimationMovSrc: ''
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        list() {
            return this.$store.state.workplan[listType]?.[this.storeKey]
        },
        mainDate() {
            return this.$store.state.workplan.mainDate?.[this.storeKey] || []
        },
        mainDateKey() {
            const start = this.mainDate?.[0] ? this.$moment(this.mainDate[0]).format('YYYY-MM-DDTHH:mm:ss') : ''
            const end = this.mainDate?.[1] ? this.$moment(this.mainDate[1]).format('YYYY-MM-DDTHH:mm:ss') : ''
            return `${start}_${end}`
        },
        activeTab() {
            return this.$store.state.workplan.activeTab?.[this.storeKey] || 'tasks'
        },
        selectedDate() {
            if (!this.mainDate?.[0] || !this.isSingleDayRange) return null
            return this.$moment(this.mainDate[0]).format('YYYY-MM-DD')
        },
        isSingleDayRange() {
            const start = this.mainDate?.[0]
            const end = this.mainDate?.[1]
            if (!start || !end) return false
            return this.$moment(start).isSame(this.$moment(end), 'day')
        },
        user() {
            return this.$store.state.workplan.user?.[this.storeKey] || []
        },
        currentUserId() {
            return this.$store.state.user.user?.id || null
        },
        userFilterKey() {
            if(!Array.isArray(this.user) || !this.user.length) return ''
            return this.user
                .map(item => item?.id)
                .filter(Boolean)
                .sort((a, b) => Number(a) - Number(b))
                .join(',')
        },
        listRequestKey() {
            return `${this.mainDateKey}_${this.userFilterKey}`
        },
        notesCount() {
            const results = this.list && Array.isArray(this.list.results) ? this.list.results : []
            return results.length
        },
        notesStatusKey() {
            const results = this.list && Array.isArray(this.list.results) ? this.list.results : []
            if (!results.length) return ''
            return results
                .map(item => `${item?.id || ''}:${item?.status?.code || item?.status || ''}`)
                .join(',')
        },
        refreshRange() {
            const start = this.mainDate?.[0]
            const end = this.mainDate?.[1]

            if (!start || !end) return null

            return {
                start: this.$moment(start).format('YYYY-MM-DD'),
                end: this.$moment(end).format('YYYY-MM-DD')
            }
        },
        refreshFormRange() {
            const [start, end] = this.normalizeRange(this.refreshForm.range)
            return {
                start: start.format('YYYY-MM-DD'),
                end: end.format('YYYY-MM-DD')
            }
        },
        refreshRangeComponent() {
            return this.isMobile ? 'RefreshMobileRangeInput' : 'RefreshRangeInput'
        },
        refreshPresets() {
            const now = this.$moment()
            return [
                { label: this.$t('today'), range: [now.clone().startOf('day'), now.clone().endOf('day')] },
                { label: this.$t('yesterday'), range: [now.clone().subtract(1, 'day').startOf('day'), now.clone().subtract(1, 'day').endOf('day')] },
                { label: this.$t('tomorrow'), range: [now.clone().add(1, 'day').startOf('day'), now.clone().add(1, 'day').endOf('day')] },
                { label: this.$t('current_week'), range: [now.clone().startOf('week'), now.clone().endOf('week')] },
                { label: this.$t('current_month'), range: [now.clone().startOf('month'), now.clone().endOf('month')] },
                { label: this.$t('week'), range: [now.clone().startOf('day'), now.clone().add(6, 'day').endOf('day')] },
                { label: this.$t('month'), range: [now.clone().startOf('day'), now.clone().add(1, 'month').subtract(1, 'day').endOf('day')] }
            ]
        },
        showPendingAlert() {
            return this.activeTab === 'pulse' && this.hasPendingSummary
        }
    },
    watch: {
        mainDateKey: {
            immediate: true,
            handler() {
                if (this.activeTab === 'pulse') {
                    this.ensureListLoaded({ force: true })
                    this.checkPendingSummaryStatus({ force: true })
                    this.syncPublishState()
                }
            }
        },
        activeTab(value) {
            if (value === 'pulse') {
                this.ensureListLoaded()
                this.checkPendingSummaryStatus({ force: true })
                this.syncPublishState()
            }
        },
        user: {
            deep: true,
            handler() {
                if (this.activeTab === 'pulse')
                    this.ensureListLoaded({ force: true })
            }
        },
        selectedDate: {
            immediate: true,
            handler() {
                this.syncPublishState()
            }
        },
        notesCount() {
            this.syncPublishState()
        },
        notesStatusKey() {
            this.syncPublishState()
        }
    },
    sockets: {
        async notify({ data }) {
            if (data?.event_type !== 'new_notification') return
            const query = this.parseNotificationLinkQuery(data?.obj)
            if (!this.isPulseSummaryNotification(query)) return
            if (this.activeTab !== 'pulse') return

            await this.reloadList()
            await this.checkPendingSummaryStatus({ force: true })
        }
    },
    methods: {
        async loadPendingAnimation() {
            this.pendingAnimationMovSrc = `${process.env.BASE_URL}animate/AI_mov.mov`

            try {
                const animationModule = await import('@/assets/animate/AI.webm')
                this.pendingAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.pendingAnimationWebmSrc = ''
            }
        },
        parseNotificationLinkQuery(notification = {}) {
            const localizedMessage = notification?.[`message_${this.$i18n.locale}`]
            const message = localizedMessage || notification?.message || ''
            if (!message) return null

            const singleQuoteMatch = message.match(/data-link-query='([^']+)'/)
            const doubleQuoteMatch = message.match(/data-link-query="([^"]+)"/)
            const encodedQuery = singleQuoteMatch?.[1] || doubleQuoteMatch?.[1]
            if (!encodedQuery) return null

            try {
                const decodedQuery = encodedQuery
                    .replace(/&quot;/g, '"')
                    .replace(/&#39;/g, '\'')
                    .replace(/&amp;/g, '&')
                return JSON.parse(decodedQuery)
            } catch (e) {
                return null
            }
        },
        isPulseSummaryNotification(query) {
            if (!query || typeof query !== 'object') return false
            const myPlan = query.my_plan === true || query.my_plan === 'true'
            const tab = typeof query.wtab === 'string' ? query.wtab.toLowerCase() : query.wtab
            return myPlan && tab === 'pulse'
        },
        async getList({ reload = false, loading = true } = {}) {
            let success = true
            try {
                await this.$store.dispatch('workplan/getDayPulseList', {
                    storeKey: this.storeKey,
                    list: listType,
                    reload,
                    loading
                })
            } catch(error) {
                success = false
                errorHandler({error, show: false})
            }
            return success
        },
        resetList() {
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'page',
                value: 1,
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'next',
                value: true,
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'empty',
                value: false,
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'results',
                value: [],
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'page_size',
                value: 15,
                storeKey: this.storeKey,
                list: listType
            })
        },
        async reloadList() {
            this.resetList()
            const loaded = await this.getList({ reload: true })
            if(loaded) {
                this.lastLoadedListKey = this.listRequestKey
            }
            return loaded
        },
        ensureListLoaded({ force = false } = {}) {
            if(this.list?.loading) return
            if(force || this.lastLoadedListKey !== this.listRequestKey) {
                this.reloadList()
            }
        },
        nextLoading() {
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'page',
                value: this.list.page + 1,
                storeKey: this.storeKey,
                list: listType
            })
            this.getList()
        },
        openCreateModal() {
            this.editNote = null
            this.noteModalVisible = true
        },
        openEditModal(note) {
            this.editNote = note || null
            this.noteModalVisible = true
        },
        setRefreshPreset(range) {
            this.refreshForm.range = this.normalizeRange(range)
        },
        openRefreshModal() {
            this.refreshForm.range = this.normalizeRange(this.mainDate)
            this.refreshModalVisible = true
        },
        closeRefreshModal() {
            this.refreshModalVisible = false
        },
        normalizeRange(arrayLike) {
            if (!arrayLike || !arrayLike[0] || !arrayLike[1]) {
                const t = this.$moment()
                return [t.clone().startOf('day'), t.clone().endOf('day')]
            }

            return [
                this.$moment(arrayLike[0]).startOf('day'),
                this.$moment(arrayLike[1]).endOf('day')
            ]
        },
        async onNoteDeleted() {
            await this.reloadList()
        },
        async refreshSummary() {
            if (!this.refreshFormRange?.start || !this.refreshFormRange?.end || !this.currentUserId) {
                return
            }

            try {
                this.refreshLoading = true
                await this.$http.post('/analytics/summaries/', {
                    start: this.refreshFormRange.start,
                    end: this.refreshFormRange.end,
                    related_object: this.currentUserId,
                    scope: 'user_day_summary'
                })
                this.$message.success(this.$t('workplan.day_pulse_started'))
                this.refreshModalVisible = false
                await this.checkPendingSummaryStatus({ force: true })
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.refreshLoading = false
            }
        },
        async checkPendingSummaryStatus({ force = false, date = null } = {}) {
            const requestId = ++this.pendingCheckRequestId
            const targetRange = date
                ? { start: date, end: date }
                : this.refreshRange

            if (!targetRange?.start || !targetRange?.end) {
                this.hasPendingSummary = false
                this.pendingSummaries = []
                return
            }

            if (!force && this.activeTab !== 'pulse') return

            try {
                const { data } = await this.$http.get('/day_summary/note/pending/', {
                    params: {
                        start: targetRange.start,
                        end: targetRange.end
                    }
                })

                if (requestId !== this.pendingCheckRequestId) return
                const pendingItems = Array.isArray(data?.pending) ? data.pending : []
                const hasPendingInRange = pendingItems.some(item => {
                    const pendingStart = item?.start_date || item?.date
                    const pendingEnd = item?.end_date || item?.date
                    if (!pendingStart || !pendingEnd) return false

                    const pendingStartMoment = this.$moment(pendingStart).startOf('day')
                    const pendingEndMoment = this.$moment(pendingEnd).endOf('day')
                    const rangeStartMoment = this.$moment(targetRange.start).startOf('day')
                    const rangeEndMoment = this.$moment(targetRange.end).endOf('day')

                    return pendingStartMoment.isSameOrBefore(rangeEndMoment, 'day')
                        && pendingEndMoment.isSameOrAfter(rangeStartMoment, 'day')
                })

                this.pendingSummaries = pendingItems
                this.hasPendingSummary = Boolean(data?.has_pending) && hasPendingInRange
            } catch (error) {
                if (requestId !== this.pendingCheckRequestId) return
                this.hasPendingSummary = false
                this.pendingSummaries = []
            }
        },
        async publishNotes() {
            if (!this.selectedDate) return

            this.$confirm({
                title: this.$t('workplan.day_pulse_publish_confirm_title'),
                content: this.$t('workplan.day_pulse_publish_confirm_content'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('workplan.day_pulse_publish_confirm_ok'),
                onOk: async () => {
                    try {
                        this.publishLoading = true
                        await this.$http.put('/day_summary/note/publish/', {
                            date: this.selectedDate
                        })
                        this.$message.success(this.$t('workplan.day_pulse_published'))
                        await this.reloadList()
                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.publishLoading = false
                    }
                }
            })
        },
        async syncPublishState() {
            const requestId = ++this.publishStateRequestId

            if (!this.isSingleDayRange || !this.selectedDate || this.notesCount === 0) {
                this.publishStateLoading = false
                this.isPublished = null
                return
            }

            this.publishStateLoading = true
            this.isPublished = null

            try {
                const { data } = await this.$http.get('/day_summary/note/is_published/', {
                    params: {
                        date: this.selectedDate
                    }
                })

                if (requestId !== this.publishStateRequestId) return
                this.isPublished = this.normalizePublishedState(data?.is_published)
            } catch (error) {
                if (requestId !== this.publishStateRequestId) return
                this.isPublished = null
            } finally {
                if (requestId !== this.publishStateRequestId) return
                this.publishStateLoading = false
            }
        },
        normalizePublishedState(value) {
            if (value === true || value === 'true' || value === 1 || value === '1')
                return true
            if (value === false || value === 'false' || value === 0 || value === '0')
                return false
            return null
        }
    },
    created() {
        this.loadPendingAnimation()
    },
    beforeDestroy() {
        if(!this.useInject) return
        this.resetList()
    }
}
</script>

<style lang="scss" scoped>
.summary_alert{
    background: linear-gradient(135deg, rgb(249, 239, 255) 46%, rgb(240, 216, 255) 100%);
    padding: 10px 15px;
    border: 1px solid #f1dcff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.summary_alert__anim {
    width: 22px;
    height: 22px;
    object-fit: contain;
    flex: 0 0 22px;
}
.day_pulse {
    min-height: 320px;
}

.day_pulse__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 15px;
}

.day_pulse__top_left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}

.refresh_btn {
    white-space: nowrap;
}

.notes_list {
    padding-bottom: 12px;
}

.empty_wrap {
    min-height: 280px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.bottom_actions {
    position: sticky;
    bottom: 8px;
    z-index: 20;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding-top: 8px;
}

.refresh_presets {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}

.publish_day_btn {
    box-shadow: 0 10px 24px -10px var(--blue);
}

.slide-up-enter-active,
.slide-up-leave-active {
    transition: opacity .25s ease, transform .25s ease;
}

.slide-up-enter,
.slide-up-leave-to {
    opacity: 0;
    transform: translateY(12px);
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

@media (max-width: 768px) {
    .day_pulse__top {
        flex-direction: column;
        align-items: stretch;
    }

    .day_pulse__top_left {
        flex-direction: column;
        align-items: stretch;
    }

    .refresh_btn,
    .day_pulse__top_left .ant-btn,
    .bottom_actions .ant-btn {
        width: 100%;
    }

    .bottom_actions {
        bottom: calc(54px + env(safe-area-inset-bottom));
    }
}
</style>
