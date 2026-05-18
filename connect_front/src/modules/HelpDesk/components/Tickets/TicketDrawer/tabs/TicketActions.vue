<template>
    <div class="ticket-actions-v2" style="min-height: 36px;">
        <div v-if="ticket" class="w-full">
            <div v-if="!isClientView" class="w-full">
                <div v-if="actions?.change_status" class="w-full change-status-header-wrap">
                    <div class="change-status-header flex gap-2 w-full">
                        <a-button
                            v-if="showStartButton"
                            class="btn-start"
                            type="primary"
                            icon="fi-rr-play"
                            flaticon
                            :loading="statusLoader"
                            iconRight
                            @click="startExecution">
                            <span class="btn-text">{{ $t('helpdesk.start_execution') }}</span>
                        </a-button>

                        <a-button
                            v-if="showExecutionButton"
                            class="btn-exec"
                            type="green"
                            :loading="statusLoader"
                            @click="openFinishModal({ status: 'on_pause' })">
                            <div v-if="!statusLoader" class="flex items-center">
                                <span class="execution-label mr-1">{{ $t('helpdesk.execution') }}:</span>
                                <transition name="badge-fade-slide">
                                    <span v-if="!durationLoading" class="timer-text">{{ formattedTimer }}</span>
                                </transition>
                                <i
                                    class="fi fi-rr-pause ml-2"
                                    v-tippy
                                    :content="$t('helpdesk.pause')" />
                            </div>
                        </a-button>

                        <a-button
                            v-if="showFinishButton"
                            class="btn-finish"
                            type="ui"
                            ghost
                            @click="openFinishModal({ status: 'completed' })"
                            iconRight>
                            <span class="btn-text">{{ $t('helpdesk.finish') }}</span>
                        </a-button>

                        <!-- <a-popover
                            v-if="showFinishButton"
                            :getPopupContainer="getCalendarContainer"
                            trigger="click"
                            @visibleChange="resultVisibleChange"
                            transitionName="">
                            <a-button
                                type="ui"
                                ghost
                                @click="openFinishModal"
                                iconRight>
                                {{ $t('helpdesk.finish') }}
                            </a-button>
                            <template #content>
                                <div class="execution_result mb-2">
                                    <div class="execution_result__label mb-1">
                                        {{ $t('helpdesk.execution_result') }}
                                    </div>
                                    <a-textarea
                                        v-model="execution_result"
                                        ref="execution_result"
                                        inputType="bg"
                                        :placeholder="$t('helpdesk.describe_work_result')"
                                        :auto-size="{ minRows: 3, maxRows: 5 }"
                                        @keydown="onTextareaKeydown" />
                                </div>
                                <a-button
                                    type="primary"
                                    ghost
                                    block
                                    class="text_current"
                                    :loading="statusLoader"
                                    @click="changeStatus('completed', true)">
                                    {{ $t('helpdesk.confirm_completion') }}
                                </a-button>
                            </template>
                        </a-popover> -->

                        <a-button
                            v-if="showRejectbutton"
                            class="btn-reject ml-auto border-none"
                            type="danger"
                            :loading="statusLoader"
                            @click="openFinishModal({ status: 'rejected' })"
                            ghost>
                            <span class="btn-text">{{ $t('helpdesk.cancel_action') }}</span>
                        </a-button>
                    </div>
                </div>

                <template v-else>
                    <div v-if="ticket.status.code !== 'completed' && !ticket.specialist" class="mt-4 mb-2">
                        <a-alert v-if="!form.specialist" :message="$t('helpdesk.assign_responsible')" />
                    </div>
                </template>
            </div>
            <div v-else>
                <a-spin
                    :spinning="statusLoader"
                    size="small"
                    class="w-full">
                    <div class="w-full change-status-header-wrap">
                        <div class="change-status-header flex gap-2 w-full">
                            <a-button
                                v-if="isStatusAvailable('completed')"
                                type="flat_primary"
                                size="large"
                                flaticon
                                icon="fi-rr-check"
                                block
                                @click="ticketEnd()">
                                {{ $t('helpdesk.accept_result') }}
                            </a-button>

                            <a-button
                                v-if="isStatusAvailable('on_rework')"
                                type="flat_danger"
                                size="large"
                                flaticon
                                icon="fi-rr-rotate-right"
                                block
                                @click="changeStatus('on_rework')">
                                {{ availableStatusByCode.on_rework?.name || $t('helpdesk.needs_rework') }}
                            </a-button>

                            <a-button
                                v-if="isStatusAvailable('rejected')"
                                class="border-none"
                                type="danger"
                                ghost
                                @click="changeStatus('rejected')">
                                {{ $t('helpdesk.cancel_action') }}
                            </a-button>
                        </div>
                    </div>
                </a-spin>
            </div>

        </div>

        <a-modal
            v-model="finishModalVisible"
            :footer="null"
            @afterClose="finishModalAfterClose"
            @afterVisibleChange="afterVisibleChange"
            @cancel="finishModalVisible = false">
            <template #title>
                {{ stopTimerModalTitle }}
            </template>

            <div class="mt-5">
                <a-skeleton v-if="getIncompleteDurationLoading" />
                <template v-else>
                    <div class="grid md:grid-cols-3 gap-2">
                        <div class="item_block">
                            <div class="mb-1">
                                {{ $t('helpdesk.hours') }}
                            </div>
                            <a-input-number
                                v-model="customDuration.hours"
                                size="large"
                                class="w-full"
                                :min="0"
                                :precision="0"
                                :placeholder="$t('helpdesk.hours_placeholder')" />
                        </div>
                        <div class="item_block">
                            <div class="mb-1">
                                {{ $t('helpdesk.minutes') }}
                            </div>
                            <a-input-number
                                v-model="customDuration.minutes"
                                size="large"
                                class="w-full"
                                :min="0"
                                :max="59"
                                :precision="0"
                                :placeholder="$t('helpdesk.minutes_placeholder')" />
                        </div>
                        <div class="item_block">
                            <div class="mb-1">
                                {{ $t('helpdesk.seconds') }}
                            </div>
                            <a-input-number
                                v-model="customDuration.seconds"
                                size="large"
                                class="w-full"
                                :min="0"
                                :max="59"
                                :precision="0"
                                :placeholder="$t('helpdesk.seconds_placeholder')" />
                        </div>
                    </div>

                    <div class="mt-3 text-right">
                        <span class="text-muted mr-2">{{ $t('helpdesk.total_by_ticket') }}:</span>
                        <span>{{ formattedTimer }}</span>
                    </div>

                    <div v-if="stopTimerReasonStatus !== 'rejected'" class="mt-3">
                        <div class="execution_result__label mb-1">
                            {{ $t('helpdesk.description') }}
                        </div>
                        <a-textarea
                            v-model="description"
                            ref="description"
                            inputType="bg"
                            :placeholder="$t('helpdesk.print_description')"
                            :auto-size="{ minRows: 3, maxRows: 5 }" />
                    </div>

                    <div v-if="stopTimerReasonStatus === 'completed' || stopTimerReasonStatus === 'rejected'" class="mt-3">
                        <div class="execution_result__label mb-1">
                            {{ stopTimerReasonStatus === 'rejected' ? $t('helpdesk.cancellation_reason') : $t('helpdesk.execution_result') }}
                        </div>
                        <a-textarea
                            v-model="execution_result"
                            ref="execution_result"
                            inputType="bg"
                            :placeholder="stopTimerReasonStatus === 'rejected' ? $t('helpdesk.describe_cancellation_reason') : $t('helpdesk.describe_execution_result')"
                            :auto-size="{ minRows: 3, maxRows: 5 }"
                            @keydown="onTextareaKeydown" />
                    </div>

                    <template v-if="!ticket.started_timer">
                        <div class="mt-4" ref="calendarWrapRef">
                            <a-date-picker
                                v-model="accountingDate"
                                :getCalendarContainer="() => $refs.calendarWrapRef"
                                format="DD.MM.YYYY"
                                class="w-full"
                                size="large" />
                        </div>
                    </template>

                    <div class="mt-3">
                        <a-checkbox v-model="isResult">
                            {{ $t('helpdesk.is_results') }}
                        </a-checkbox>
                    </div>

                    <div class="mt-4 grid md:grid-cols-1 gap-2">
                        <a-button
                            type="primary"
                            block
                            :loading="statusLoader"
                            @click="stopTimerWithTime">
                            {{ $t('helpdesk.confirm_action') }}
                        </a-button>
                    </div>
                </template>
            </div>
        </a-modal>
        <a-modal
            title=""
            :visible="endVisible"
            :width="500"
            @cancel="closeEndVisible()">
            <div class="rew_wrapper">
                <h2>{{ $t('helpdesk.rate_service_quality') }}</h2>
                <SmileSelect v-model="rewForm.rating" class="mb-5" />
                <a-textarea
                    v-model="rewForm.description"
                    size="large"
                    :placeholder="$t('helpdesk.rating_comment')"
                    :auto-size="{ minRows: 3, maxRows: 12 }" />
            </div>
            <template #footer>
                <a-button
                    type="primary"
                    size="large"
                    block
                    :loading="completedLoading"
                    @click="completedTicket(true)">
                    {{ $t('helpdesk.accept_result') }}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import priorityMixin from '../../../../priorityMixin.js'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
let timer;
let reloadTimer;
export default {
    mixins: [priorityMixin],
    sockets: {
        notify({ data }) {
            if(data?.event_type === 'update_current_work')
                this.getTimer()
        }
    },
    props: {
        slaLoading: {
            type: Boolean,
            default: false
        },
        getSLA: {
            type: Function,
            default: () => {}
        },
        ticket: {
            type: Object,
            default: () => null
        },
        edit: {
            type: Boolean,
            default: false
        },
        listPageName: {
            type: String,
            required: true
        },
        listModel: {
            type: String,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        getTicket: {
            type: Function,
            default: () => {}
        },
        actionsTakeDelete: {
            type: Function,
            default: () => {}
        },
        tab: {
            type: String,
            default: "info"
        },
        getActions: {
            type: Function,
            default: () => {}
        },
        forceReload: {
            type: Function,
            default: () => {}
        },
        ticketType: {
            type: String,
            default: "issue"
        },
        slaInfo: {
            type: Object,
            default: () => null
        }
    },
    components: {
        SmileSelect: () => import('../../../Request/RequestDrawer/components/SmileSelect.vue'),
    },
    computed: {
        isClientView() {
            const q = this.$route?.query || {}
            if (q.ticketView) return false
            if (q.requestView) return true
            return false
        },
        availableStatuses() {
            return Array.isArray(this.actions?.change_status?.available_statuses)
                ? this.actions.change_status.available_statuses
                : []
        },
        availableStatusByCode() {
            const map = {}
            for (const st of this.availableStatuses) {
                if (st?.code) map[st.code] = st
            }
            return map
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        ...mapState({
            user: state => state.user.user
        }),
        slaComponent() {
            if(this.slaInfo)
                return () => import('../../ModalFormSLA.vue')
            return null
        },
        canStartTimer() {
            return this.actions?.can_use_timer?.availability
        },
        stopTimerModalTitle() {
            const dynamicTitle = this.availableStatusByCode?.[this.stopTimerReasonStatus]?.name
            if (dynamicTitle) {
                return dynamicTitle
            }
            const titles = {
                'on_pause': this.$t('helpdesk.on_pause'),
                'completed': this.$t('helpdesk.complete'),
                'rejected': this.$t('helpdesk.reject'),
            }
            return titles[this.stopTimerReasonStatus] || this.$t('helpdesk.stop_timer')
        },
        showStartButton() {
            if (this.ticket.status.code === 'in_work') {
                return this.canStartTimer && !this.isCurrentWorkLog
            }
            if (['new', 'on_pause', 'on_rework', 'clarification_required'].includes(this.ticket.status.code)) {
                return this.availableStatuses.some(status => status.code === 'in_work')
            }
            return false
        },
        showExecutionButton() {
            if (this.ticket.status.code !== 'in_work') { return false }
            if (!this.isCurrentWorkLog) { return false }
            return this.availableStatuses.some(status => status.code === 'on_pause')
        },
        showFinishButton() {
            return this.availableStatuses.some(status => status.code === 'completed')
        },
        canChangeStatus() {
            return this.actions?.change_status?.availability && this.availableStatuses.length
        },
        showRejectbutton() {
            const rejectButtonCode = 'rejected'
            if (this.ticket.status.code === rejectButtonCode) { return }
            if (this.canChangeStatus) {
                return this.availableStatuses.some(status => status.code === rejectButtonCode)
            }
            return false
        },
        curPriority() {
            if(this.ticket.priority) {
                const find = this.priorityList.find(f => Number(f.value) === Number(this.ticket.priority.code))
                if(find) {
                    return find
                }
            }
            return null
        },
        formattedTimer() {
            if (this.timerStop) {
                const total = Math.max(0, this.stoppedValue)
                const h = Math.floor(total / 3600)
                const m = Math.floor((total % 3600) / 60)
                const s = Math.floor(total % 60)
                const pad = n => String(n).padStart(2, '0')
                return (h > 0 ? `${pad(h)}:` : '') + `${pad(m)}:${pad(s)}`
            }
            const total = Math.max(0, this.elapsedSeconds)
            const h = Math.floor(total / 3600)
            const m = Math.floor((total % 3600) / 60)
            const s = Math.floor(total % 60)
            const pad = n => String(n).padStart(2, '0')
            return (h > 0 ? `${pad(h)}:` : '') + `${pad(m)}:${pad(s)}`
        },
        accountingPageName() {
            return `work_log_${this.ticket?.id || 'new'}`
        },
        ckEditor() {
            return () => import("@apps/CKEditor");
        },
        userSelectApi() {
            if(this.ticketType === 'lead')
                return `/contractor_permissions/app_sections/help_desk/members/?contractor=${this.ticket.customer_card.org_admin.id}`
            else
                return `/help_desk/customer_cards/${this.ticket.customer_card.id}/specialists/actual/?display=user`
        }
    },
    watch: {
        tab(val) {
            if(val === 'info') {
                this.$nextTick(() => {
                    if(this.$refs?.chatList)
                        this.$refs.chatList.scrollToBottom()
                })
            }
        },
        'ticket.status.code'() {
            if (!this.ticket?.status?.code) { return }
            this.getTimer()
        },
        'ticket.started_timer'() {
            if (this.ticket?.status?.code !== 'in_work') { return }
            this.getTimer()
        }
    },
    data() {
        return {
            initListCategory: [],
            accountingModel: 'help_desk.HelpDeskTicketWorkLogModel',
            durationLoading: true,
            duration: 0,
            accountingDate: null,
            editorGate: false,
            elapsedSeconds: 0,
            runTimerId: null,
            statusLoader: false,
            endVisible: false,
            completedLoading: false,
            rewForm: {
                description: "",
                rating: null
            },
            showAside: true,
            spamPageName: 'list_help_desk.SpamContactPersonModel',
            spamPageModel: 'help_desk.ContactPersonModel',
            execution_result: "",
            rejectReasonText: "",
            description: "",
            isResult: false,
            customDuration: {
                hours: 0,
                minutes: 0,
                seconds: 0
            },
            form: {
                metadata: {
                    visors: []
                },
                receipt_date: null,
                author: null,
                visors: [],
                category: null,
                customer_card: null,
                name: "",
                description: "",
                priority: null,
                dead_line: null
            },
            rules: {

            },
            stoppedValue: 0,
            spamLoading: false,
            finishModalVisible: false,
            getIncompleteDurationLoading: false,
            stopTimerReasonStatus: null,
            lastSessionDuration: 0,
            totalDuration: 0,
            timerStop: false,
            isCurrentWorkLog: false
        }
    },
    created() {
        this.getTimer()
        this.initEdit()
    },
    mounted() {
        eventBus.$on('ticket_open_finish_modal', ({ status=null }) => {
            this.openFinishModal({ status: status })
        })
    },
    beforeDestroy() {
        this.stopLocalTimer()
        eventBus.$off('ticket_open_finish_modal')
    },
    methods: {
        closeEndVisible() {
            this.endVisible = false
        },
        async startExecution() {
            if (this.statusLoader) { return }
            if (this.ticket.status.code === 'in_work') {
                await this.toggleTimer('in_work', false)
                await this.getTicket()
                return
            }
            this.changeStatus('in_work', false, true)
        },
        isStatusAvailable(code) {
            return !!this.availableStatusByCode?.[code]
        },
        ticketEnd() {
            this.endVisible = true
        },
        afterVisibleChange(vis) {
            if(vis) {
                requestAnimationFrame(() => {
                    this.$nextTick(() => {
                        if(this.$refs.execution_result)
                            this.$refs.execution_result.focus()
                    })
                })
            } else {
                this.timerStop = false
                this.execution_result = ""
                this.description = ""
                this.isResult = false
            }
        },
        async completedTicket(status = true) {
            try {
                this.completedLoading = true
                if(this.rewForm.rating) {
                    await this.$http.post('/vote/rating/', {
                        ...this.rewForm,
                        related_object: this.ticket.id
                    })
                }
                if(status)
                    await this.changeStatus('completed')
                else {
                    await this.getTicket()
                    this.listReload()
                }
                this.rewForm = {
                    description: "",
                    rating: null
                }
                this.endVisible = false
            } catch(error) {
                errorHandler({error})
            } finally {
                this.completedLoading = false
            }
        },
        initEdit() {
            if(this.edit) {
                const ticketForm = {...this.ticket}
                if(ticketForm.category) {
                    this.initListCategory = [{
                        ...ticketForm.category,
                        string_view: ticketForm.category.name
                    }]
                    ticketForm.category = ticketForm.category.id
                }
                if(ticketForm.customer_card)
                    ticketForm.customer_card = ticketForm.customer_card.id
                if(ticketForm.priority)
                    ticketForm.priority = Number(ticketForm.priority.code)
                if(ticketForm.dead_line)
                    ticketForm.dead_line = this.$moment(ticketForm.dead_line)
                if(ticketForm.receipt_date)
                    ticketForm.receipt_date = this.$moment(ticketForm.receipt_date)

                this.form = ticketForm

                if(this.$route.query?.in_complete) {
                    const query = JSON.parse(JSON.stringify(this.$route.query))
                    delete query.in_complete
                    this.$router.replace({query})
                    this.openFinishModal({ status: 'completed' })
                }
            }
        },
        closeFinishModal() {
            this.finishModalVisible = false
        },
        stopTimerWithTime() {
            this.changeStatus(this.stopTimerReasonStatus, true)
        },
        stopTimerWithoutTime() {
            this.changeStatus(this.stopTimerReasonStatus, true)
        },
        finishModalAfterClose() {
            this.customDuration = {
                hours: 0,
                minutes: 0,
                seconds: 0
            }
            this.accountingDate = null
            this.execution_result = ""
            this.description = ""
            this.isResult = false
            this.stopTimerReasonStatus = null
            this.lastSessionDuration = 0
            this.totalDuration = 0
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            const hours = Math.floor(t / 3600)
            const minutes = Math.floor((t % 3600) / 60)
            const seconds = t % 60
            return {
                hours,
                minutes,
                seconds,
            }
        },
        HMSToSeconds(HMS) {
            const { hours, minutes, seconds } = HMS
            return (hours * 3600) + (minutes * 60) + seconds
        },
        openFinishModal({ status=null }) {
            if (!['on_pause', 'completed', 'rejected', 'clarification_required'].includes(status) && !this.ticket.started_timer) {
                this.changeStatus(status, true)
                return
            }
            this.finishModalVisible = true
            if (!this.ticket.started_timer)
                this.accountingDate = this.$moment()
            this.getIncompleteDurationLoading = true
            this.stopTimerReasonStatus = status
            this.$http.get(`help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                .then(({ data }) => {
                    const incompleteDuration = Number(data?.duration_incomplete ?? data?.incomplete_duration ?? 0)
                    const totalDuration = Number(data?.duration ?? this.duration ?? 0)
                    this.timerStop = true
                    this.stoppedValue = Math.max(0, this.elapsedSeconds)
                    this.customDuration = this.secondsToHMS(incompleteDuration)
                    this.lastSessionDuration = incompleteDuration
                    this.totalDuration = totalDuration
                })
                .catch((error) => {
                    this.timerStop = false
                    errorHandler({error})
                })
                .finally(() => {
                    this.getIncompleteDurationLoading = false
                })
        },
        isSVG(icon) {
            return icon.endsWith('.svg')
        },
        openCreateClientModal() {
            this.$refs.clientClientModalRef.openModal(this.ticket.contact_person)
        },
        maskAsSpam(contactPerson) {
            this.spamLoading = true
            this.$http.post(`help_desk/contact_persons/${contactPerson.id}/mark_as_spam/`)
                .then(({ data }) => {
                    if(data) {
                        this.$message.success(this.$t('helpdesk.contact_marked_spam'))
                        eventBus.$emit('ticket_drawer_close')
                    }
                })
                .catch((error) => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.spamLoading = false
                })
        },
        allVisorClear() {
            this.form.metadata.visors = []
            this.form.visors = []
            this.patchField([], 'visors')
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        onTextareaKeydown(e, status='completed') {
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault()
                this.changeStatus(status, true)
            }
        },
        resultVisibleChange(vis) {
            this.$nextTick(() => {
                if(vis && this.$refs?.execution_result) {
                    this.$refs.execution_result.focus()
                }
            })
        },
        updateTimer() {
            this.getTimer()
            this.$nextTick(() => {
                if(this.$refs?.completedBanner)
                    this.$refs.completedBanner.getTimer()
            })
        },
        changeShowAside(value) {
            this.showAside = value
        },
        startLocalTimer() {
            if (!this.isCurrentWorkLog) {
                this.stopLocalTimer()
                return
            }
            this.stopLocalTimer()
            this.runTimerId = setInterval(() => {
                this.elapsedSeconds += 1
            }, 1000)
        },
        stopLocalTimer() {
            if (this.runTimerId) {
                clearInterval(this.runTimerId)
                this.runTimerId = null
            }
        },
        async getTimer() {
            if(this.ticket.status.code === 'in_work') {
                try {
                    const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                    if(data) {
                        const duration = Number(data.duration || 0)
                        const incompleteDuration = Number(data.duration_incomplete ?? data.incomplete_duration ?? 0)
                        const isCurrent = Boolean(data.is_current)

                        this.duration = duration
                        this.elapsedSeconds = isCurrent
                            ? Math.max(0, Math.floor(incompleteDuration))
                            : 0
                        this.lastSessionDuration = Math.max(0, Math.floor(incompleteDuration))
                        this.isCurrentWorkLog = isCurrent

                        if (isCurrent) this.startLocalTimer()
                        else this.stopLocalTimer()
                    } else {
                        this.isCurrentWorkLog = false
                        this.stopLocalTimer()
                    }
                } catch(error) {
                    this.isCurrentWorkLog = false
                    this.stopLocalTimer()
                    errorHandler({error, show: false})
                } finally {
                    this.durationLoading = false
                }
            } else {
                this.isCurrentWorkLog = false
                this.elapsedSeconds = 0
                this.stopLocalTimer()
                this.durationLoading = false
            }
        },

        // ✅ FIX: добавили startedTimerSnapshot, чтобы сокет не ломал ветку
        async toggleTimer(status, startedTimerSnapshot = null) {
            try {
                const wasStartedTimer =
                    startedTimerSnapshot === null ? !!this.ticket.started_timer : !!startedTimerSnapshot
                const isStopActionFromModal =
                    this.finishModalVisible && this.stopTimerReasonStatus === status
                const shouldHandleTimerStop = status !== 'in_work' && (wasStartedTimer || isStopActionFromModal)

                if(status === 'in_work') {
                    const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/start/`)
                    if(data) {
                        this.duration = Number(data.duration || 0)
                        this.isCurrentWorkLog = Boolean(data.is_current)
                        this.elapsedSeconds = this.isCurrentWorkLog
                            ? Math.max(0, Math.floor(Number(data.duration_incomplete ?? data.incomplete_duration ?? 0)))
                            : 0
                        if (this.isCurrentWorkLog) this.startLocalTimer()
                        else this.stopLocalTimer()
                        eventBus.$emit('global_timer_sync_required', {
                            entity: 'ticket',
                            entityId: this.ticket.id,
                            action: 'start_timer',
                            status
                        })
                    }
                }

                if(shouldHandleTimerStop) {
                    if (wasStartedTimer) {
                        const payload = {
                            duration_incomplete: this.HMSToSeconds(this.customDuration),
                            description: this.description,
                            is_result: this.isResult
                        }
                        const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/stop/`, payload)
                        if(data) {
                            this.duration = Number(data.duration || 0)
                            this.isCurrentWorkLog = Boolean(data.is_current)
                            this.elapsedSeconds = this.isCurrentWorkLog
                                ? Math.max(0, Math.floor(Number(data.duration_incomplete ?? data.incomplete_duration ?? 0)))
                                : 0
                            if (this.isCurrentWorkLog) this.startLocalTimer()
                            else this.stopLocalTimer()
                            eventBus.$emit('global_timer_sync_required', {
                                entity: 'ticket',
                                entityId: this.ticket.id,
                                action: 'stop_timer',
                                status
                            })
                        }
                    } else if (isStopActionFromModal) {
                        const url = `/help_desk/tickets/${this.ticket.id}/work_log/create/`
                        const totalSeconds = this.HMSToSeconds(this.customDuration)

                        // ✅ FIX: если date пустой (гонка/модалка не задавала) — ставим today
                        if (!this.accountingDate) this.accountingDate = this.$moment()

                        const payload = {
                            duration: totalSeconds,
                            date: this.accountingDate.format('YYYY-MM-DD'),
                            description: this.description,
                            is_result: this.isResult
                        }
                        await this.$http.post(url, payload)
                    }
                }
                if (status !== 'in_work') {
                    this.isCurrentWorkLog = false
                    this.stopLocalTimer()
                }
                this.durationLoading = false
            } catch(error) {
                errorHandler({error})
            }
        },
        async changeStatus(status, useText = false) {
            try {
                this.statusLoader = true

                // ✅ FIX: snapshot до запроса (до того как сокет/ответ обновит ticket)
                const startedTimerSnapshot = !!this.ticket?.started_timer

                const queryData = {
                    status
                }
                if (useText) {
                    queryData.execution_result = this.execution_result
                }

                const { data } = await this.$http.put(`/help_desk/tickets/${this.ticket.id}/status/`, queryData)
                if(data) {
                    if (!this.isClientView){
                        // ✅ FIX: передаем snapshot
                        await this.toggleTimer(status, startedTimerSnapshot)
                    }
                    await this.getTicket()
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                    eventBus.$emit(`update_filter_${this.accountingModel}_${this.accountingPageName}`)
                    this.listReload()
                    this.execution_result = ""
                    this.rejectReasonText = ''
                    eventBus.$emit('STATUS_TICKET_KANBAN', {
                        task: data,
                        status
                    })
                    eventBus.$emit('global_timer_sync_required', {
                        entity: 'ticket',
                        entityId: this.ticket.id,
                        action: 'status_changed',
                        status
                    })
                    this.closeFinishModal()
                }

                this.getActions({ ticketView: this.ticket.id })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.statusLoader = false
            }
        },
        listReload() {
            clearTimeout(reloadTimer)
            reloadTimer = setTimeout(() => {
                eventBus.$emit(`update_filter_${this.spamPageModel}_${this.spamPageName}`)
                eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
            }, 1000)
        },
        checkField({key, type = 'object'}) {
            if(this.edit)
                return true
            else {
                if(type === 'array') {
                    if(this.ticket[key]?.length)
                        return true
                } else {
                    if(this.ticket[key])
                        return true
                }
            }
            return false
        },
        dataChange({field, useTimer = false, valueKey = false, multiple = false}) {
            let value = this.form[field]
            if(valueKey) {
                if(multiple) {
                    value = this.form[field].map(fld => fld[valueKey])
                } else {
                    value = this.form[field][valueKey]
                }
            }
            if(useTimer) {
                clearTimeout(timer)
                timer = setTimeout(() => {
                    this.patchField(value, field)
                }, 600)
            } else {
                this.patchField(value, field)
            }
        },
        async patchField(value, field) {
            try {
                if(field === 'name' && !value) {
                    this.$message.warning(this.$t('helpdesk.name_required_warning'))
                    return false
                }
                const { data } = await this.$http.patch(`/help_desk/tickets/${this.ticket.id}/`, {
                    [field]: value,
                    metadata: this.form.metadata
                })
                if(data) {
                    if(field === 'specialist')
                        this.actionsTakeDelete()
                    this.listReload()
                    if(field === 'category')
                        this.getSLA()
                    if(field === 'specialist')
                        this.getActions(this.$route.query)

                    const kanbanObj = {...data}
                    if(kanbanObj.sla?.sla)
                        kanbanObj.sla = kanbanObj.sla.sla
                    eventBus.$emit('UPDATE_TICKET_KANBAN', kanbanObj)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                }
            } catch(error) {
                if(error?.non_field_errors?.length) {
                    if(error.non_field_errors[0].includes("не является ответственным")) {
                        this.forceReload(false)
                    }
                }
                errorHandler({error})
            }
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        openClient() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query.client) {
                query.client = this.ticket.customer_card.id
                this.$router.replace({query})
            } else {
                eventBus.$emit('close_client_drawer')
                setTimeout(() => {
                    query.client = this.ticket.customer_card.id
                    this.$router.replace({query})
                }, 500)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.badge-fade-slide-enter-active, .badge-fade-slide-leave-active {
    transition: all 0.3s ease
}
.badge-fade-slide-enter, .badge-fade-slide-leave-to {
    transform: translateX(-8px);
    opacity: 0
}
.description_editor{
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: 0px !important;
            z-index: 999999;
        }
        .ck{
            &.ck-toolbar__items{
                margin-right: 0px!important;
            }
            &.ck-toolbar__separator{
                opacity: 0;
                margin-right: 0px!important;
            }
            &.ck-toolbar{
                border: 0px;
                padding-left: 0px!important;
                padding-right: 0px!important;
                margin-left: -7px;
            }
            &.ck-content{
                border: 0px!important;
                box-shadow: none!important;
                padding-left: 0px!important;
                padding-right: 0px!important;
                background: transparent!important;
            }
        }
    }
}
.execution_result{
    min-width: 400px;
}
.channel_icon{
    max-width: 16px;
}
.priority_icon{
    position: relative;
    overflow: hidden;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    &__bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
    }
    i{
        position: relative;
        z-index: 5;
    }
}
.change-status-header {
    &:not(:empty) {
    }
}

::v-deep {
    .ant-modal .ant-modal-header {
        padding-top: 24px;
    }
    .ant-modal .ant-modal-body {
        padding-top: 0;
        padding-bottom: 24px;
    }
}

.aside-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(180px, 1fr));
    gap: 5px;
    align-items: flex-start;
}

/* =========================
   MOBILE: 2 rows
   Row 1: Start (or Execution) — full width
   Row 2: Finish + Cancel — adaptive width
   ========================= */
@media (max-width: 768px) {
    .change-status-header-wrap{
        position: relative;
        padding-bottom: 2px;
    }

    .change-status-header{
        flex-direction: row;
        flex-wrap: wrap; /* allows 2 rows */
        align-items: stretch;
        gap: 8px;
        padding: 2px 6px 6px;
    }

    /* base styles for all buttons inside header */
    .change-status-header ::v-deep .ant-btn{
        height: 40px;
        padding: 0 12px;
        min-width: 0;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    /* Row 1: Start / Execution take full width */
    .change-status-header ::v-deep .btn-start,
    .change-status-header ::v-deep .btn-exec{
        flex: 1 1 100%;
        width: 100%;
    }

    /* Row 2: Finish / Reject share the line; if one отсутствует — оставшаяся растянется */
    .change-status-header ::v-deep .btn-finish,
    .change-status-header ::v-deep .btn-reject{
        flex: 1 1 0;
        width: auto;
    }

    /* don't push "cancel" away on mobile */
    .change-status-header ::v-deep .btn-reject{
        margin-left: 0 !important;
    }

    /* text: allow full width (ellipsis only if совсем не влезло) */
    .btn-text{
        display: inline-block;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        vertical-align: bottom;
    }

    /* hide "Execution:" label, keep timer clean */
    .execution-label{
        display: none;
    }

    /* icons look tighter */
    .change-status-header ::v-deep .ant-btn .fi{
        font-size: 14px;
        line-height: 1;
    }

    /* timer as a badge */
    .timer-text{
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        font-variant-numeric: tabular-nums;
        letter-spacing: 0.2px;
    }

    /* prevent modal horizontal overflow */
    .execution_result{
        min-width: 0;
        width: 100%;
        max-width: 100%;
    }

    /* ===== Modal polish on mobile ===== */
    ::v-deep .ant-modal{
        width: calc(100vw - 24px) !important;
        max-width: 560px;
        margin: 12px auto !important;
        top: 12px;
        padding-bottom: 0;
    }

    ::v-deep .ant-modal-content{
        overflow: hidden;
    }

    ::v-deep .ant-modal-header{
        padding: 16px 16px 10px;
    }

    ::v-deep .ant-modal-body{
        padding: 0 16px 16px;
    }

    ::v-deep .ant-input-number-lg{
        height: 40px;
    }

    ::v-deep .ant-calendar-picker-input{
        height: 40px;
    }
}

/* extra small screens: tighter text */
@media (max-width: 380px) {
    .btn-text{
        max-width: 100%;
    }
}
@media (max-width: 768px) {
    .ticket-actions-v2{
        width: 100%;
    }
}

</style>
