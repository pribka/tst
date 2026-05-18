<template>
    <div v-if="shouldShowCallLayer" class="meeting-call-layer">
        <transition-group name="call-window-transition">
            <div
                v-for="(item, index) in callWindows"
                :key="item.id"
                ref="callWindow"
                class="call-window"
                :class="[
                    `call-window--${item.type}`,
                    { 'call-window--meeting': isMeetingEmbedded(item) && !shouldHideMeetingIframe(item) }
                ]"
                :style="getWindowStyle(item, index)"
                @mousedown="bringToFront(item.id)">
                <div
                    class="call-window__header"
                    :class="{ 'call-window__header--active': isCallInProgress(item) }"
                    @mousedown.prevent="startDrag($event, item.id)">
                    <div class="call-window__drag-handle"></div>
                    <div class="call-window__header-icon">
                        <i :class="item.type === 'incoming' ? 'fi fi-rr-call-incoming' : 'fi fi-rr-call-outgoing'" />
                    </div>
                    <div>
                        <div class="call-window__header-title">
                            {{ item.type === 'incoming' ? $t('meeting.incoming_call') : $t('meeting.outgoing_call') }}
                        </div>
                        <div class="call-window__header-status">
                            {{ getCallStatusText(item) }}
                        </div>
                    </div>
                </div>

                <div
                    class="call-window__body"
                    :class="{ 'call-window__body--meeting': isMeetingEmbedded(item) && !shouldHideMeetingIframe(item) }">
                    <iframe
                        v-if="shouldRenderMeetingIframe(item)"
                        :ref="`meetingIframe-${item.id}`"
                        :key="`meeting-iframe-${item.id}-${item.meetingIframeRenderKey || 0}`"
                        class="call-window__iframe"
                        :class="{ 'call-window__iframe--hidden': shouldHideMeetingIframe(item) }"
                        :src="item.embeddedMeetingUrl"
                        frameborder="0"
                        scrolling="auto"
                        :allow="getMeetingIframeAllow(item.embeddedMeetingUrl)"
                        @load="handleMeetingIframeLoad(item)">
                    </iframe>
                    <div
                        v-if="getMeetingOverlayText(item)"
                        class="call-window__meeting-overlay">
                        <div class="call-window__meeting-overlay-card">
                            {{ getMeetingOverlayText(item) }}
                        </div>
                    </div>
                    <template v-if="item.transferMode">
                        <div class="call-window__transfer">
                            <div class="call-window__transfer-head">
                                <div class="call-window__transfer-title">
                                    {{ $te('meeting.transfer_call') ? $t('meeting.transfer_call') : 'Передать звонок' }}
                                </div>
                                <a-button
                                    type="ui"
                                    ghost
                                    size="small"
                                    shape="circle"
                                    icon="fi-rr-cross-small"
                                    flaticon
                                    class="call-window__transfer-close"
                                    @click="closeTransferMode(item)" />
                            </div>
                            <div v-if="item.transferLoading" class="call-window__transfer-state">
                                <a-spin />
                            </div>
                            <a-empty
                                v-else-if="!item.transferUsers.length"
                                :description="$te('meeting.transfer_users_empty') ? $t('meeting.transfer_users_empty') : 'Нет специалистов для передачи'" />
                            <div
                                v-else
                                class="call-window__transfer-list">
                                <button
                                    v-for="userItem in item.transferUsers"
                                    :key="userItem.id"
                                    type="button"
                                    class="call-window__transfer-user"
                                    :disabled="item.transferSubmittingId === userItem.id"
                                    @click="transferCall(item, userItem)">
                                    <a-avatar
                                        :size="36"
                                        :src="getUserAvatar(userItem)"
                                        icon="user">
                                        {{ getUserInitials(userItem) }}
                                    </a-avatar>
                                    <div class="call-window__transfer-user-main">
                                        <div class="call-window__transfer-user-name">
                                            {{ getDisplayName(userItem) }}
                                        </div>
                                        <div v-if="userItem.job_title" class="call-window__transfer-user-subtitle">
                                            {{ userItem.job_title }}
                                        </div>
                                    </div>
                                    <a-spin v-if="item.transferSubmittingId === userItem.id" size="small" />
                                </button>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <div class="call-window__user">
                            <div
                                v-if="item.meetingRecordingActive"
                                class="call-window__recording-badge">
                                {{ getRecordingBadgeText() }}
                            </div>
                            <a-avatar
                                :key="getDisplayUserAvatarKey(item)"
                                :size="72"
                                :src="getUserAvatar(getDisplayUser(item))"
                                icon="user">
                                {{ getUserInitials(getDisplayUser(item)) }}
                            </a-avatar>
                            <div class="call-window__name">
                                {{ getDisplayName(getDisplayUser(item)) }}
                            </div>
                            <div v-if="getCallDurationText(item)" class="call-window__subtitle">
                                {{ getCallDurationText(item) }}
                            </div>
                        </div>
                        <div
                            v-if="getBodyStatusText(item)"
                            class="call-window__body-status">
                            {{ getBodyStatusText(item) }}
                        </div>
                        <div
                            v-if="getEndedCallDurationText(item)"
                            class="call-window__ended-duration">
                            <div class="call-window__ended-duration-label">
                                {{ $te('meeting.call_duration') ? $t('meeting.call_duration') : 'Длительность разговора' }}
                            </div>
                            <div class="call-window__ended-duration-value">
                                {{ getEndedCallDurationText(item) }}
                            </div>
                        </div>

                        <div class="call-window__footer">
                            <div v-if="isCallEnded(item)" class="call-window__ended-buttons">
                                <a-button
                                    v-if="hasCallTicket(item)"
                                    type="primary"
                                    size="large"
                                    block
                                    class="call-window__ticket-btn"
                                    @click="openTicket(item)">
                                    {{ $t('meeting.open_ticket') }}
                                </a-button>
                                <a-button
                                    v-if="shouldShowChatButton(item)"
                                    size="large"
                                    shape="round"
                                    block
                                    class="call-window__chat-btn"
                                    @click="writeInChat(item)">
                                    {{ $t('meeting.write_in_chat') }}
                                </a-button>
                            </div>
                            <div
                                v-if="shouldShowTicketLink(item)"
                                class="call-window__ticket-link"
                                @click="openTicket(item)">
                                {{ $t('meeting.open_ticket') }}
                            </div>
                            <div v-if="canTransferCall(item)" class="flex justify-center">
                                <a-button
                                    size="large"
                                    shape="round"
                                    class="call-window__chat-btn"
                                    @click="openTransferMode(item)">
                                    {{ $te('meeting.transfer_call') ? $t('meeting.transfer_call') : 'Передать звонок' }}
                                </a-button>
                            </div>
                            <div
                                class="call-window__actions"
                                :class="getActionsClass(item)">
                                <template v-if="item.awaitingMicrophoneAccess">
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="flat_danger"
                                            size="large"
                                            block
                                            :loading="item.actionLoading === 'end'"
                                            @click="endCall(item.id)">
                                            {{ $t('meeting.reject_call') }}
                                        </a-button>
                                    </div>
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="flat_primary"
                                            size="large"
                                            block
                                            :loading="item.actionLoading === 'microphone'"
                                            @click="requestCallMicrophoneAccess(item.id)">
                                            {{ $te('meeting.allow_microphone') ? $t('meeting.allow_microphone') : 'Разрешить микрофон' }}
                                        </a-button>
                                    </div>
                                </template>
                                <template v-else-if="isCallInProgress(item)">
                                    <div class="call-window__action-slot">
                                        <a-button
                                            :type="item.meetingSelfMuted ? 'ui_ghost' : 'flat_primary'"
                                            size="large"
                                            shape="circle"
                                            :icon="item.meetingSelfMuted ? 'fi-rr-volume-mute' : 'fi-rr-microphone'"
                                            :disabled="!item.embeddedMeetingUrl || (!item.meetingReadyToConnect && !item.meetingAudioJoined)"
                                            flaticon
                                            class="flex items-center justify-center ico_btn"
                                            v-tippy
                                            :content="getToggleMicrophoneText(item)"
                                            @click="toggleMeetingMute(item)">
                                        </a-button>
                                    </div>
                                    <!--
                                    <div class="call-window__action-slot">
                                        <a-button
                                            :type="item.meetingRecordingActive ? 'flat_danger' : 'flat_primary'"
                                            size="large"
                                            shape="circle"
                                            icon="fi-rr-dot-circle"
                                            :disabled="!item.embeddedMeetingUrl || (!item.meetingReadyToConnect && !item.meetingAudioJoined)"
                                            :loading="item.actionLoading === 'recording'"
                                            flaticon
                                            class="flex items-center justify-center ico_btn"
                                            v-tippy
                                            :content="getToggleRecordingText(item)"
                                            @click="toggleMeetingRecording(item)">
                                        </a-button>
                                    </div>
                                    -->
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="flat_danger"
                                            size="large"
                                            shape="circle"
                                            icon="fi-rr-phone-slash"
                                            flaticon
                                            class="flex items-center justify-center ico_btn"
                                            v-tippy
                                            :content="getEndCallText()"
                                            :loading="item.actionLoading === 'end'"
                                            @click="endCall(item.id)">
                                        </a-button>
                                    </div>
                                </template>
                                <template v-else-if="isCallEnded(item)">
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="ui_ghost"
                                            size="large"
                                            block
                                            @click="removeCallWindow(item.id)">
                                            {{ $t('meeting.close') }}
                                        </a-button>
                                    </div>
                                </template>
                                <template v-else-if="item.type === 'incoming'">
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="flat_danger"
                                            size="large"
                                            shape="circle"
                                            icon="fi-rr-phone-slash"
                                            flaticon
                                            class="flex items-center justify-center ico_btn"
                                            v-tippy
                                            :content="$t('meeting.reject_call')"
                                            :loading="item.actionLoading === 'reject'"
                                            @click="rejectCall(item.id)">
                                        </a-button>
                                    </div>
                                    <div class="call-window__action-slot">
                                        <a-button
                                            type="green"
                                            size="large"
                                            shape="circle"
                                            icon="fi-rr-phone-call"
                                            flaticon
                                            class="flex items-center justify-center ico_btn"
                                            v-tippy
                                            :content="$t('meeting.accept_call')"
                                            :loading="item.actionLoading === 'accept'"
                                            @click="acceptCall(item.id)">
                                        </a-button>
                                    </div>
                                </template>
                                <template v-else>
                                    <template v-if="canRetryCall(item)">
                                        <div class="call-window__action-slot">
                                            <a-button
                                                type="ui_ghost"
                                                size="large"
                                                block
                                                @click="removeCallWindow(item.id)">
                                                {{ getRetryDismissText(item) }}
                                            </a-button>
                                        </div>
                                        <div class="call-window__action-slot">
                                            <a-button
                                                type="flat_primary"
                                                size="large"
                                                block
                                                :loading="item.actionLoading === 'retry'"
                                                @click="retryCall(item.id)">
                                                {{ $t('meeting.call_again') }}
                                            </a-button>
                                        </div>
                                    </template>
                                    <div v-else class="call-window__action-slot">
                                        <a-button
                                            type="flat_danger"
                                            size="large"
                                            block
                                            :loading="item.actionLoading === 'cancel'"
                                            @click="cancelCall(item.id)">
                                            {{ $t('meeting.reject_call') }}
                                        </a-button>
                                    </div>
                                </template>
                            </div>
                            <div v-if="!isCallEnded(item)" class="flex justify-center">
                                <a-button
                                    v-if="shouldShowChatButton(item)"
                                    size="large"
                                    shape="round"
                                    class="call-window__chat-btn"
                                    @click="writeInChat(item)">
                                    {{ $t('meeting.write_in_chat') }}
                                </a-button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </transition-group>
    </div>
</template>

<script>
import axios from '@/config/axios'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import SoundMaster from '@/utils/soundMaster'
import ChatEventBus from '@apps/vue2ChatComponent/utils/ChatEventBus'
import { getNotificationSoundEnabled } from '@/modules/Notifications/soundSettings'
import { mapState } from 'vuex'
import { REMOTE_ACCESS_AGENT_STATUSES } from '@/utils/remoteAccess'
import { CALL_RESTORE_EVENT, CALL_START_EVENT, ensureMicrophoneAccess } from '../utils/call'
import CallPopupChannel from '@/utils/callPopupChannel'
import visibilityHub from '@/utils/visibilityHub'
import {
    CALL_RECEIVER_PRESENCE_TIMEOUT,
    CALL_REMINDER_INTERVAL,
    CALL_WINDOW_GAP,
    CALL_WINDOW_HEIGHT,
    CALL_WINDOW_MARGIN,
    CALL_WINDOW_WIDTH,
    CALL_WINDOW_Z_INDEX,
    MEETING_IFRAME_ALLOWED_ORIGINS,
    MEETING_IFRAME_HEALTHCHECK_TIMEOUT,
    MEETING_IFRAME_ORIGIN,
    MEETING_IFRAME_RETRY_DELAY,
    MEETING_RECORDING_POLL_INTERVAL,
    MEETING_RECORDING_START_GRACE_PERIOD,
    MEETING_RECORDING_STOP_CONFIRMATIONS,
    OUTGOING_SOUND_OWNER_STORAGE_KEY
} from './constants'

export default {
    name: 'MeetingCall',
    data() {
        return {
            callWindows: [],
            dragData: null,
            zIndexCounter: CALL_WINDOW_Z_INDEX,
            outgoingReminderIntervals: {},
            incomingPresenceIntervals: {},
            receiverPresenceTimeouts: {},
            incomingSoundActive: false,
            outgoingSoundActive: false,
            incomingSoundSyncToken: 0,
            callDurationNow: Date.now(),
            callDurationTimer: null,
            activeTabId: `meeting-call-tab-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            outgoingSoundOwnerId: null,
            meetingIframeRetryTimeouts: {},
            meetingIframeHealthcheckTimeouts: {},
            meetingRecordingStatusIntervals: {},
            unloadIframeRestoreTimeout: null,
            unloadAttemptActive: false,
            // Call popup window (shown when user leaves the tab)
            isCallPopupMode: typeof window !== 'undefined' && window.name === 'meeting-call-popup',
            callPopupWindow: null,
            callPopupCheckTimer: null,
            callPopupChannelUnsubscribe: null
        }
    },
    watch: {
        callWindows: {
            deep: true,
            immediate: true,
            handler() {
                this.syncCallPopupState()
                this.syncUnloadProtectionFlag()
            }
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile,
            windowWidth: state => state.windowWidth,
            windowHeight: state => state.windowHeight,
            remoteAccessAgentStatus: state => state.remoteAccess.agentStatus
        }),
        shouldShowCallLayer() {
            return this.remoteAccessAgentStatus !== REMOTE_ACCESS_AGENT_STATUSES.CONNECTED
        }
    },
    methods: {
        restoreCalls(calls = []) {
            if (!Array.isArray(calls) || !calls.length)
                return

            calls.forEach(call => {
                this.handleCallUpdate({
                    ...call,
                    __restoredFromBootstrap: true
                })
            })
        },
        async startCall({
            payload = {},
            context = null,
            setLoading = null,
            onSuccess = null,
            onError = null,
            onFinally = null
        } = {}) {
            if (!payload || typeof payload !== 'object' || Array.isArray(payload))
                return

            const callContext = this.normalizeCallContext({ payload, context })
            const existingItem = this.findWindowByContext(callContext)

            if (existingItem) {
                const statusCode = this.getStatusCode(existingItem.call)

                if (existingItem.type === 'incoming' || statusCode === 'ringing')
                    return

                if (existingItem.type === 'outgoing' && ['cancelled_by_receiver', 'missed'].includes(statusCode)) {
                    try {
                        if (typeof setLoading === 'function')
                            setLoading(true)

                        await this.retryCall(existingItem.id)
                    } finally {
                        if (typeof setLoading === 'function')
                            setLoading(false)
                    }
                    return
                }
            }

            try {
                if (typeof setLoading === 'function')
                    setLoading(true)

                const { data } = await axios.post('/meetings/calls/start/', payload)
                this.handleCallUpdate(data, 'outgoing', payload, null, callContext)

                if (typeof onSuccess === 'function')
                    onSuccess(data)
            } catch (error) {
                errorHandler({ error })

                if (typeof onError === 'function')
                    onError(error)
            } finally {
                if (typeof setLoading === 'function')
                    setLoading(false)

                if (typeof onFinally === 'function')
                    onFinally()
            }
        },
        async cancelCall(id) {
            await this.submitCallAction(id, 'cancel', 'cancel')
            this.removeCallWindow(id)
        },
        async retryCall(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item?.retryPayload)
                return

            this.setActionLoading(id, 'retry')
            this.$set(item, 'replacing', true)
            let nextCallId = id

            try {
                const { data } = await axios.post('/meetings/calls/start/', item.retryPayload)
                nextCallId = data?.id || id
                this.upsertCallWindow(data, 'outgoing', item.retryPayload, id, item.startContext)
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.setActionLoading(nextCallId, null)
                const nextItem = this.callWindows.find(windowItem => windowItem.id === nextCallId)
                if (nextItem)
                    this.$set(nextItem, 'replacing', false)
            }
        },
        async acceptCall(id) {
            this.setActionLoading(id, 'accept')

            try {
                const hasMicrophoneAccess = await ensureMicrophoneAccess()
                if (!hasMicrophoneAccess)
                    return

                const data = await this.submitCallAction(id, 'accept', null)
                if (data?.status?.code === 'in_call')
                    this.finishCall(data)
            } finally {
                this.setActionLoading(id, null)
            }
        },
        async rejectCall(id) {
            await this.submitCallAction(id, 'reject', 'reject')
            this.removeCallWindow(id)
        },
        async endCall(id) {
            await this.submitCallAction(id, 'end', 'end')
        },
        async requestCallMicrophoneAccess(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item?.call)
                return

            this.setActionLoading(id, 'microphone')

            try {
                const hasMicrophoneAccess = await ensureMicrophoneAccess()
                if (!hasMicrophoneAccess)
                    return

                this.$set(item, 'awaitingMicrophoneAccess', false)
                this.finishCall(item.call)
            } finally {
                this.setActionLoading(id, null)
            }
        },
        setPendingMicrophoneAccess(call) {
            if (!call?.id)
                return

            if (!this.callWindows.some(item => item.id === call.id))
                this.upsertCallWindow(call, this.resolveCallType(call) || 'incoming')

            const item = this.callWindows.find(windowItem => windowItem.id === call.id)
            if (!item)
                return

            this.$set(item, 'call', call)
            this.$set(item, 'embeddedMeetingUrl', null)
            this.$set(item, 'meetingAudioJoined', false)
            this.$set(item, 'meetingReadyToConnect', false)
            this.$set(item, 'awaitingMicrophoneAccess', true)
        },
        async submitCallAction(id, action, loadingKey) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item)
                return null

            this.setActionLoading(id, loadingKey)

            try {
                const { data } = await axios.post(`/meetings/calls/${id}/${action}/`)
                if (data?.id) {
                    this.handleCallUpdate(data, item.type, null, null, item.startContext)
                    return data
                }

                return null
            } catch (error) {
                errorHandler({ error })
                return null
            } finally {
                this.setActionLoading(id, null)
            }
        },
        async sendCallReminder(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item
                || item.type !== 'outgoing'
                || this.shouldSkipPresenceHeartbeat({ item })
                || this.getStatusCode(item.call) !== 'ringing'
                || item.actionLoading === 'cancel'
                || item.autoCancelledByOffline) {
                return
            }

            try {
                await axios.post(`/meetings/calls/${id}/send_call_reminder/`)
            } catch (error) {
                errorHandler({ error })
            }
        },
        async reportCallReceiverOnline(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item
                || item.type !== 'incoming'
                || this.shouldSkipPresenceHeartbeat({ item })
                || this.getStatusCode(item.call) !== 'ringing') {
                return
            }

            try {
                await axios.post(`/meetings/calls/${id}/report_call_receiver_online/`)
            } catch (error) {
                errorHandler({ error })
            }
        },
        startOutgoingReminder(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item
                || item.type !== 'outgoing'
                || this.shouldSkipPresenceHeartbeat({ item })
                || this.getStatusCode(item.call) !== 'ringing'
                || item.actionLoading === 'cancel'
                || item.autoCancelledByOffline) {
                return
            }

            if (this.outgoingReminderIntervals[id])
                return

            this.sendCallReminder(id)
            this.outgoingReminderIntervals[id] = setInterval(() => {
                this.sendCallReminder(id)
            }, CALL_REMINDER_INTERVAL)
        },
        stopOutgoingReminder(id) {
            if (!this.outgoingReminderIntervals[id])
                return

            clearInterval(this.outgoingReminderIntervals[id])
            this.$delete(this.outgoingReminderIntervals, id)
        },
        startIncomingPresenceReporter(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item
                || item.type !== 'incoming'
                || this.shouldSkipPresenceHeartbeat({ item })
                || this.getStatusCode(item.call) !== 'ringing') {
                return
            }

            if (this.incomingPresenceIntervals[id])
                return

            this.reportCallReceiverOnline(id)
            this.incomingPresenceIntervals[id] = setInterval(() => {
                this.reportCallReceiverOnline(id)
            }, CALL_REMINDER_INTERVAL)
        },
        stopIncomingPresenceReporter(id) {
            if (!this.incomingPresenceIntervals[id])
                return

            clearInterval(this.incomingPresenceIntervals[id])
            this.$delete(this.incomingPresenceIntervals, id)
        },
        refreshReceiverPresenceTimeout(id) {
            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (this.shouldSkipPresenceHeartbeat({ item })) {
                this.clearReceiverPresenceTimeout(id)
                return
            }

            if (this.receiverPresenceTimeouts[id]) {
                clearTimeout(this.receiverPresenceTimeouts[id])
                this.$delete(this.receiverPresenceTimeouts, id)
            }

            this.receiverPresenceTimeouts[id] = setTimeout(() => {
                const item = this.callWindows.find(windowItem => windowItem.id === id)
                if (!item || item.type !== 'outgoing' || this.getStatusCode(item.call) !== 'ringing')
                    return

                this.$delete(this.receiverPresenceTimeouts, id)
                this.handleReceiverOffline(item)
            }, CALL_RECEIVER_PRESENCE_TIMEOUT)
        },
        async handleReceiverOffline(item) {
            if (!item?.id || item.type !== 'outgoing')
                return

            this.$set(item, 'actionLoading', 'cancel')
            this.$set(item, 'receiverPresenceState', 'offline')
            this.$set(item, 'autoCancelledByOffline', true)
            this.stopOutgoingReminder(item.id)
            this.clearReceiverPresenceTimeout(item.id)

            try {
                await axios.post(`/meetings/calls/${item.id}/cancel/`)
            } catch (error) {
                errorHandler({ error })
            }

            this.$set(item, 'call', {
                ...item.call,
                status: {
                    ...(item.call?.status || {}),
                    code: 'receiver_offline',
                    name: this.getStatusLabel('receiver_offline', item.call?.status?.name)
                }
            })
            this.$set(item, 'actionLoading', null)
        },
        clearReceiverPresenceTimeout(id) {
            if (!this.receiverPresenceTimeouts[id])
                return

            clearTimeout(this.receiverPresenceTimeouts[id])
            this.$delete(this.receiverPresenceTimeouts, id)
        },
        setMeetingRecordingState(item, isActive, reason, extra = {}) {
            if (!item?.id)
                return

            const nextValue = !!isActive
            const previousValue = !!item.meetingRecordingActive

            console.log('[Meeting recording][state]', {
                callId: item.id,
                from: previousValue,
                to: nextValue,
                reason,
                extra,
                at: new Date().toISOString()
            })

            this.$set(item, 'meetingRecordingActive', nextValue)
        },
        logMeetingIframeState(item, reason, extra = {}) {
            if (!item?.id)
                return

            console.log('[Meeting iframe][state]', {
                callId: item.id,
                reason,
                meetingSourceUrl: item.meetingSourceUrl || null,
                embeddedMeetingUrl: item.embeddedMeetingUrl || null,
                meetingReadyToConnect: !!item.meetingReadyToConnect,
                meetingAudioJoined: !!item.meetingAudioJoined,
                meetingRecordingActive: !!item.meetingRecordingActive,
                meetingRecordingIntent: item.meetingRecordingIntent || null,
                meetingRecordingRequestedAt: item.meetingRecordingRequestedAt || null,
                meetingIframeChecking: !!item.meetingIframeChecking,
                meetingIframeRetryAttempt: item.meetingIframeRetryAttempt || 0,
                extra,
                at: new Date().toISOString()
            })
        },
        syncCallActivity(item) {
            if (!item?.id)
                return

            const isRinging = this.getStatusCode(item.call) === 'ringing'

            if (item.type === 'outgoing' && isRinging) {
                this.startOutgoingReminder(item.id)
                this.refreshReceiverPresenceTimeout(item.id)
            } else {
                this.stopOutgoingReminder(item.id)
                this.clearReceiverPresenceTimeout(item.id)
            }

            if (item.type === 'incoming' && isRinging)
                this.startIncomingPresenceReporter(item.id)
            else
                this.stopIncomingPresenceReporter(item.id)
        },
        clearAllCallActivity() {
            Object.keys(this.outgoingReminderIntervals).forEach(id => this.stopOutgoingReminder(id))
            Object.keys(this.incomingPresenceIntervals).forEach(id => this.stopIncomingPresenceReporter(id))
            Object.keys(this.receiverPresenceTimeouts).forEach(id => this.clearReceiverPresenceTimeout(id))
        },
        handleNotifyEvent(payload) {
            const data = payload?.data || payload
            const eventType = data?.event_type || payload?.event_type || ''
            if (eventType === 'call_receiver_presence') {
                this.handleReceiverPresenceEvent(data)
                return
            }

            if (eventType === 'call_receiver_joined_bbb') {
                this.handleReceiverJoinedBbbEvent(data)
                return
            }

            const call = data?.call || data

            if (!call?.id)
                return

            if (eventType && !eventType.includes('call') && !data?.new_status)
                return

            const nextStatusCode = data?.new_status || call?.status?.code || null
            const normalizedCall = nextStatusCode
                ? {
                    ...call,
                    status: {
                        ...(call.status || {}),
                        code: nextStatusCode,
                        name: this.getStatusLabel(nextStatusCode, call?.status?.name)
                    }
                }
                : call

            this.handleCallUpdate(normalizedCall)
        },
        handleReceiverPresenceEvent(payload) {
            const data = payload?.data || payload
            const callId = data?.call_id || data?.call?.id || null
            if (!callId)
                return

            const item = this.callWindows.find(windowItem => windowItem.id === callId)
            if (!item
                || item.type !== 'outgoing'
                || this.shouldSkipPresenceHeartbeat({ item })
                || this.getStatusCode(item.call) !== 'ringing') {
                return
            }

            this.$set(item, 'receiverPresenceState', 'online')
            this.refreshReceiverPresenceTimeout(callId)
        },
        handleReceiverJoinedBbbEvent(payload) {
            const data = payload?.data || payload
            const callId = data?.call_id || data?.call?.id || data?.id || null
            if (!callId)
                return

            const item = this.callWindows.find(windowItem => windowItem.id === callId)
            if (!item)
                return

            this.$set(item, 'receiverJoinedBbb', true)
        },
        handleCallUpdate(call, preferredType = null, retryPayload = null, currentId = null, startContext = null) {
            if (!call?.id)
                return

            const statusCode = this.getStatusCode(call)
            const existingItem = this.callWindows.find(item => item.id === (currentId || call.id)) || null
            const resolvedType = preferredType || this.resolveCallType(call)

            if (!resolvedType) {
                if (existingItem)
                    this.removeCallWindow(existingItem.id)
                return
            }

            if (statusCode === 'in_call') {
                if (existingItem?.awaitingMicrophoneAccess) {
                    this.setPendingMicrophoneAccess(call)
                    return
                }

                this.finishCall(call)
                return
            }

            if (statusCode === 'ended') {
                this.handleEndedCall(call, preferredType, retryPayload, currentId, startContext)
                return
            }

            if (existingItem?.autoCancelledByOffline && statusCode === 'cancelled_by_caller') {
                this.upsertCallWindow({
                    ...call,
                    status: {
                        ...(call.status || {}),
                        code: 'receiver_offline',
                        name: this.getStatusLabel('receiver_offline', call?.status?.name)
                    }
                }, preferredType || 'outgoing', retryPayload, currentId, startContext)
                return
            }

            if (this.shouldKeepRetryWindow(call, statusCode, existingItem)) {
                this.upsertCallWindow(call, preferredType || 'outgoing', retryPayload, currentId, startContext)
                return
            }

            if ([
                'cancelled_by_receiver',
                'cancelled_by_caller',
                'missed',
                'finished',
                'declined'
            ].includes(statusCode)) {
                this.removeCallWindow(call.id)
                return
            }

            if (statusCode !== 'ringing')
                return

            this.upsertCallWindow(call, resolvedType, retryPayload, currentId, startContext)
        },
        shouldKeepRetryWindow(call, statusCode, existingItem = null) {
            return this.isInitiatorCall(call)
                && ['cancelled_by_receiver', 'missed', 'receiver_offline'].includes(statusCode)
                || !!(existingItem?.autoCancelledByOffline && statusCode === 'cancelled_by_caller')
        },
        async syncIncomingSound() {
            const syncToken = ++this.incomingSoundSyncToken
            const hasIncomingRinging = this.callWindows.some(item => item.type === 'incoming' && this.getStatusCode(item.call) === 'ringing')

            if (!hasIncomingRinging) {
                if (this.incomingSoundActive) {
                    SoundMaster.stopLoop('call_incoming')
                    this.incomingSoundActive = false
                }
                return
            }

            if (this.incomingSoundActive)
                return

            const soundEnabled = await getNotificationSoundEnabled(this.user?.id)
            if (syncToken !== this.incomingSoundSyncToken)
                return

            const stillHasIncomingRinging = this.callWindows.some(item => item.type === 'incoming' && this.getStatusCode(item.call) === 'ringing')
            if (!stillHasIncomingRinging)
                return

            if (soundEnabled) {
                SoundMaster.startLoop('call_incoming')
                this.incomingSoundActive = true
                return
            }

            if (this.incomingSoundActive) {
                SoundMaster.stopLoop('call_incoming')
                this.incomingSoundActive = false
            }
        },
        syncOutgoingSound() {
            if (typeof window === 'undefined')
                return

            const hasOutgoingRinging = this.callWindows.some(item => item.type === 'outgoing' && this.getStatusCode(item.call) === 'ringing')
            const storedOwnerId = window.localStorage.getItem(OUTGOING_SOUND_OWNER_STORAGE_KEY)

            if (hasOutgoingRinging && !storedOwnerId)
                window.localStorage.setItem(OUTGOING_SOUND_OWNER_STORAGE_KEY, this.activeTabId)

            if (!hasOutgoingRinging && storedOwnerId === this.activeTabId)
                window.localStorage.removeItem(OUTGOING_SOUND_OWNER_STORAGE_KEY)

            this.outgoingSoundOwnerId = window.localStorage.getItem(OUTGOING_SOUND_OWNER_STORAGE_KEY)
            const shouldPlayOutgoingSound = hasOutgoingRinging && this.outgoingSoundOwnerId === this.activeTabId

            if (!shouldPlayOutgoingSound) {
                if (this.outgoingSoundActive) {
                    SoundMaster.stopLoop('call_sending')
                    this.outgoingSoundActive = false
                }
                return
            }

            if (this.outgoingSoundActive)
                return

            SoundMaster.startLoop('call_sending')
            this.outgoingSoundActive = true
        },
        handleVisibilityChange() {
            if (document.visibilityState === 'visible') {
                this.restoreMeetingIframesAfterCancelledUnload()
                // Close our own popup and notify all other tabs to close theirs too
                this.closeCallPopup()
                CallPopupChannel.post({ type: 'CALL_SITE_TAB_VISIBLE' })
            } else {
                this.scheduleCallPopupCheck()
            }
            this.syncOutgoingSound()
        },
        handleWindowFocus() {
            this.restoreMeetingIframesAfterCancelledUnload()
            this.syncOutgoingSound()
            this.closeCallPopup()
            CallPopupChannel.post({ type: 'CALL_SITE_TAB_VISIBLE' })
        },
        handleWindowBlur() {
            this.syncOutgoingSound()
            // blur fires on browser minimize and on app switch — schedule popup check
            this.scheduleCallPopupCheck()
        },

        // ---- Call popup window management ----

        /**
         * Returns the serialized state of active (non-ended) calls
         * to be displayed in the popup stub window.
         */
        getActiveCallsForPopup() {
            return this.callWindows
                .filter(item => ['ringing', 'in_call'].includes(this.getStatusCode(item.call)))
                .map(item => {
                    const user = this.getDisplayUser(item)
                    return {
                        id: item.id,
                        type: item.type,
                        statusCode: this.getStatusCode(item.call),
                        displayUser: user
                            ? {
                                full_name: this.getDisplayName(user),
                                avatarUrl: this.getUserAvatar(user) || null
                            }
                            : null,
                        startedAt: item.call?.started_at || null,
                        meetingSelfMuted: item.meetingSelfMuted || false,
                        actionLoading: item.actionLoading || null,
                        canTransfer: this.canTransferCall(item)
                    }
                })
        },

        broadcastCallState() {
            if (this.isCallPopupMode) return
            // Debounce: avoid flooding popup with rapid sequential updates
            if (this._broadcastStateTimer) {
                clearTimeout(this._broadcastStateTimer)
            }
            this._broadcastStateTimer = setTimeout(() => {
                this._broadcastStateTimer = null
                const calls = this.getActiveCallsForPopup()
                CallPopupChannel.saveState({ calls })
                CallPopupChannel.post({ type: 'CALL_STATE', calls })
            }, 150)
        },

        openCallPopup() {
            if (this.isCallPopupMode) return

            // Reuse existing open popup if possible
            if (this.callPopupWindow && !this.callPopupWindow.closed) {
                this.broadcastCallState()
                return
            }

            const url = `${window.location.origin}/call-popup`
            this.callPopupWindow = window.open(
                url,
                'meeting-call-popup',
                'width=380,height=660,resizable=yes,scrollbars=yes,status=no,menubar=no,toolbar=no,location=no'
            )
            this.broadcastCallState()
        },

        closeCallPopup() {
            if (this.isCallPopupMode) return

            if (this.callPopupWindow && !this.callPopupWindow.closed) {
                try {
                    CallPopupChannel.post({ type: 'CALL_CLOSE_POPUP' })
                    this.callPopupWindow.close()
                } catch (e) { /* noop */ }
            }
            this.callPopupWindow = null
            CallPopupChannel.clearState()
        },

        /**
         * Broadcast updated call state to the popup if it is open.
         * Closes the popup if no active calls remain.
         */
        syncCallPopupState() {
            if (this.isCallPopupMode) return
            if (!this.callPopupWindow || this.callPopupWindow.closed) return

            const calls = this.getActiveCallsForPopup()
            if (calls.length) {
                this.broadcastCallState()
            } else {
                this.closeCallPopup()
            }
        },

        /**
         * Debounced decision: should we open the popup?
         * We wait a short moment so that visibilityHub can receive
         * heartbeats from other tabs of our site that may have just
         * become visible (e.g. user switched between two of our tabs).
         */
        scheduleCallPopupCheck() {
            if (this.isCallPopupMode) return

            if (this.callPopupCheckTimer) {
                clearTimeout(this.callPopupCheckTimer)
                this.callPopupCheckTimer = null
            }

            this.callPopupCheckTimer = setTimeout(() => {
                this.callPopupCheckTimer = null

                // Only open if the tab is still hidden
                if (document.visibilityState !== 'hidden') return

                // Do NOT open if another tab of our site is visible
                if (visibilityHub.anyVisible()) return

                const activeCalls = this.getActiveCallsForPopup()
                if (activeCalls.length) {
                    this.openCallPopup()
                }
            }, 300)
        },

        /**
         * Handle messages coming from the popup stub window.
         */
        handlePopupMessage(data) {
            if (!data || !data.type) return

            // Any tab of our site became visible → close popup regardless of which tab opened it
            if (data.type === 'CALL_SITE_TAB_VISIBLE') {
                this.closeCallPopup()
                return
            }

            if (data.type === 'CALL_POPUP_READY') {
                this.broadcastCallState()
                return
            }

            if (data.type === 'CALL_ACTION') {
                const { action, callId } = data
                if (!action || !callId) return

                if (action === 'accept') { this.acceptCall(callId); return }
                if (action === 'reject') { this.rejectCall(callId); return }
                if (action === 'end') { this.endCall(callId); return }
                if (action === 'cancel') { this.cancelCall(callId); return }
                if (action === 'mute') {
                    const item = this.callWindows.find(w => w.id === callId)
                    if (item) this.toggleMeetingMute(item)
                    return
                }
                if (action === 'transfer') {
                    const item = this.callWindows.find(w => w.id === callId)
                    if (item) this.openTransferMode(item)
                }
            }
        },
        handleActiveTabStorage(event) {
            if (event.key !== OUTGOING_SOUND_OWNER_STORAGE_KEY)
                return

            this.outgoingSoundOwnerId = event.newValue || null
            this.syncOutgoingSound()
        },
        resolveCallType(call) {
            if (this.isIncomingCall(call))
                return 'incoming'

            if (this.isInitiatorCall(call))
                return 'outgoing'

            return null
        },
        isIncomingCall(call) {
            return this.getTargets(call).some(target => target?.id === this.user?.id) && !this.isInitiatorCall(call)
        },
        isInitiatorCall(call) {
            return call?.initiator?.id === this.user?.id
        },
        getTargets(call) {
            if (Array.isArray(call?.current_target))
                return call.current_target

            if (call?.current_target)
                return [call.current_target]

            return []
        },
        upsertCallWindow(call, type, retryPayload = null, currentId = null, startContext = null) {
            let index = this.callWindows.findIndex(item => item.id === (currentId || call.id))
            if (index === -1 && currentId) {
                index = this.callWindows.findIndex(item => this.isSameRetryContext(item, call, retryPayload, startContext))
            }
            if (index === -1) {
                index = this.callWindows.findIndex(item => item.replacing
                    && this.isSameRetryContext(item, call, retryPayload, startContext))
            }
            if (index === -1) {
                const normalizedContext = this.normalizeCallContext({
                    payload: retryPayload,
                    call,
                    context: startContext
                })
                index = this.callWindows.findIndex(item => this.isSameCallContext(this.normalizeCallContext({ item }), normalizedContext))
            }
            const existingItem = index >= 0 ? this.callWindows[index] : null
            const currentTargets = this.getTargets(call)
            const statusCode = this.getStatusCode(call)
            const previousStatusCode = this.getStatusCode(existingItem?.call)
            const previousDisplayUserId = this.getDisplayUserId(existingItem)
            const nextDisplayUserId = this.getDisplayUserId({ type, call, targetSnapshot: currentTargets })
            const normalizedContext = this.normalizeCallContext({
                payload: retryPayload,
                call,
                context: startContext,
                item: existingItem
            })
            const restoredFromBootstrap = !!(call?.__restoredFromBootstrap || existingItem?.restoredFromBootstrap)
            const shouldResetMeetingState = !!existingItem && (
                (previousStatusCode === 'in_call' && statusCode !== 'in_call')
                || (type === 'outgoing' && previousDisplayUserId && nextDisplayUserId && previousDisplayUserId !== nextDisplayUserId)
            )
            const meetingSourceUrl = shouldResetMeetingState
                ? null
                : (this.getMeetingUrl(call) || existingItem?.meetingSourceUrl || existingItem?.embeddedMeetingUrl || null)
            const embeddedMeetingUrl = !shouldResetMeetingState && existingItem?.meetingSourceUrl === meetingSourceUrl
                ? (existingItem?.embeddedMeetingUrl || null)
                : null
            const nextItem = {
                id: call.id,
                type,
                call: {
                    ...call,
                    current_target: currentTargets.length ? currentTargets : (existingItem?.targetSnapshot || [])
                },
                targetSnapshot: currentTargets.length ? currentTargets : (existingItem?.targetSnapshot || []),
                x: existingItem ? existingItem.x : null,
                y: existingItem ? existingItem.y : null,
                width: existingItem ? existingItem.width : CALL_WINDOW_WIDTH,
                height: existingItem ? existingItem.height : CALL_WINDOW_HEIGHT,
                manuallyMoved: existingItem ? existingItem.manuallyMoved : false,
                retryPayload: retryPayload || existingItem?.retryPayload || null,
                startContext: normalizedContext,
                replacing: existingItem ? existingItem.replacing : false,
                zIndex: existingItem ? existingItem.zIndex : this.nextZIndex(),
                actionLoading: existingItem ? existingItem.actionLoading : null,
                receiverPresenceState: existingItem ? existingItem.receiverPresenceState : 'unknown',
                meetingSourceUrl,
                embeddedMeetingUrl: shouldResetMeetingState
                    ? null
                    : (embeddedMeetingUrl || existingItem?.embeddedMeetingUrl || null),
                meetingAudioJoined: shouldResetMeetingState ? false : (existingItem?.meetingAudioJoined || false),
                meetingReadyToConnect: shouldResetMeetingState ? false : (existingItem?.meetingReadyToConnect || false),
                meetingSelfMuted: shouldResetMeetingState ? false : (typeof existingItem?.meetingSelfMuted === 'boolean' ? existingItem.meetingSelfMuted : false),
                meetingRecordingActive: shouldResetMeetingState ? false : (typeof existingItem?.meetingRecordingActive === 'boolean' ? existingItem.meetingRecordingActive : false),
                meetingRecordingIntent: shouldResetMeetingState ? null : (existingItem?.meetingRecordingIntent || null),
                meetingRecordingRequestedAt: shouldResetMeetingState ? null : (existingItem?.meetingRecordingRequestedAt || null),
                meetingRecordingStopConfirmations: shouldResetMeetingState ? 0 : (existingItem?.meetingRecordingStopConfirmations || 0),
                receiverJoinedBbb: shouldResetMeetingState ? false : (existingItem?.receiverJoinedBbb || false),
                meetingReceiverJoinedBbbReported: shouldResetMeetingState ? false : (existingItem?.meetingReceiverJoinedBbbReported || false),
                awaitingMicrophoneAccess: existingItem?.awaitingMicrophoneAccess || false,
                meetingIframeChecking: shouldResetMeetingState ? false : (existingItem?.meetingIframeChecking || false),
                meetingIframeRetryAttempt: shouldResetMeetingState ? 0 : (existingItem?.meetingIframeRetryAttempt || 0),
                meetingIframeDetachedByUnload: shouldResetMeetingState ? false : (existingItem?.meetingIframeDetachedByUnload || false),
                meetingIframeProbeToken: existingItem?.meetingIframeProbeToken || 0,
                meetingIframeRenderKey: existingItem?.meetingIframeRenderKey || 0,
                transferMode: existingItem?.transferMode || false,
                transferLoading: existingItem?.transferLoading || false,
                transferUsersLoaded: existingItem?.transferUsersLoaded || false,
                transferUsers: existingItem?.transferUsers || [],
                transferSubmittingId: existingItem?.transferSubmittingId || null,
                restoredFromBootstrap,
                autoCancelledByOffline: this.getStatusCode(call) === 'receiver_offline'
                    ? !!existingItem?.autoCancelledByOffline
                    : false
            }

            if (index >= 0) {
                this.$set(this.callWindows, index, nextItem)
                this.syncCallActivity(nextItem)
                this.syncIncomingSound()
                this.syncOutgoingSound()
                this.$nextTick(this.syncWindowMetrics)
                if (nextItem.restoredFromBootstrap && nextItem.meetingSourceUrl)
                    this.$nextTick(() => this.ensureMeetingIframeReady(this.callWindows.find(item => item.id === nextItem.id), { force: true }))
                return
            }

            const position = this.getDefaultPosition(this.callWindows.length, nextItem)
            nextItem.x = position.x
            nextItem.y = position.y
            this.callWindows.push(nextItem)
            this.syncCallActivity(nextItem)
            this.syncIncomingSound()
            this.syncOutgoingSound()
            this.$nextTick(this.syncWindowMetrics)
            if (nextItem.restoredFromBootstrap && nextItem.meetingSourceUrl)
                this.$nextTick(() => this.ensureMeetingIframeReady(this.callWindows.find(item => item.id === nextItem.id), { force: true }))
        },
        isSameRetryContext(item, call, retryPayload = null, startContext = null) {
            const left = this.normalizeCallContext({
                payload: retryPayload,
                call,
                context: startContext
            })
            const right = this.normalizeCallContext({ item })

            return this.isSameCallContext(left, right)
        },
        normalizeCallContext({ payload = null, call = null, context = null, item = null } = {}) {
            const base = context || item?.startContext || {}
            const targets = this.getTargets(call || item?.call)
            const targetSnapshot = item?.targetSnapshot || []
            const targetUser = targets[0] || targetSnapshot[0] || null
            const activeCall = call || item?.call || {}

            return {
                identities: this.collectCallIdentities({
                    payload,
                    call: activeCall,
                    context: base,
                    item
                }),
                source: base.source
                    || call?.source
                    || item?.startContext?.source
                    || ((base.ticketId || payload?.ticket_id || activeCall?.ticket_id || item?.call?.ticket_id) ? 'ticket' : null),
                targetUserId: base.targetUserId
                    || payload?.target_user_id
                    || payload?.user_id
                    || (this.isInitiatorCall(activeCall) ? targetUser?.id : activeCall?.initiator?.id)
                    || targetUser?.id
                    || null
            }
        },
        shouldSkipPresenceHeartbeat({ item = null, call = null, context = null } = {}) {
            const normalizedContext = this.normalizeCallContext({ item, call, context })

            if (normalizedContext?.source === 'ticket')
                return true

            return normalizedContext?.identities?.some(identity => identity?.key === 'ticket_id') || false
        },
        collectCallIdentities({ payload = null, call = null, context = null, item = null } = {}) {
            const identities = []
            const pushIdentity = (key, value) => {
                if (!key || !value)
                    return

                if (identities.some(identity => identity.key === key && identity.value === value))
                    return

                identities.push({ key, value })
            }

            if (Array.isArray(context?.identities)) {
                context.identities.forEach(identity => pushIdentity(identity?.key, identity?.value))
            }

            pushIdentity('chat_uid', context?.chatUid || payload?.chat_uid || call?.chat_uid || item?.call?.chat_uid)
            pushIdentity('ticket_id', context?.ticketId || payload?.ticket_id || call?.ticket_id || item?.call?.ticket_id)
            pushIdentity('request_id', context?.requestId || payload?.request_id || call?.request_id || item?.call?.request_id)

            return identities
        },
        isSameCallContext(left, right) {
            if (!left?.identities?.length || !right?.identities?.length)
                return false

            const hasSharedIdentity = left.identities.some(leftIdentity => right.identities.some(rightIdentity => rightIdentity.key === leftIdentity.key && rightIdentity.value === leftIdentity.value))
            if (!hasSharedIdentity)
                return false

            if (left.targetUserId && right.targetUserId)
                return left.targetUserId === right.targetUserId

            return true
        },
        findWindowByContext(context) {
            if (!context?.identities?.length)
                return null

            return this.callWindows.find(item => this.isSameCallContext(this.normalizeCallContext({ item }), context)) || null
        },
        removeCallWindow(id) {
            this.clearMeetingIframeRetry(id)
            this.clearMeetingIframeHealthcheck(id)
            this.stopMeetingRecordingStatusPolling(id)
            this.callWindows = this.callWindows.filter(item => item.id !== id)
            this.stopOutgoingReminder(id)
            this.stopIncomingPresenceReporter(id)
            this.clearReceiverPresenceTimeout(id)

            if (this.dragData?.id === id)
                this.dragData = null

            this.syncIncomingSound()
            this.syncOutgoingSound()
        },
        finishCall(call) {
            const canOpenMeeting = this.isInitiatorCall(call) || call?.accepted_by?.id === this.user?.id
            const externalUrl = this.getMeetingUrl(call)

            if (!canOpenMeeting) {
                this.removeCallWindow(call.id)
                return
            }

            if (!this.callWindows.some(item => item.id === call.id))
                this.upsertCallWindow(call, this.resolveCallType(call) || 'incoming')

            const item = this.callWindows.find(windowItem => windowItem.id === call.id)
            if (!item)
                return

            this.$set(item, 'call', call)
            this.$set(item, 'meetingSourceUrl', externalUrl)
            this.logMeetingIframeState(item, 'finishCall:before-reset')
            this.$set(item, 'embeddedMeetingUrl', null)
            this.$set(item, 'meetingAudioJoined', false)
            this.$set(item, 'meetingReadyToConnect', false)
            this.$set(item, 'meetingSelfMuted', false)
            this.setMeetingRecordingState(item, false, 'finishCall:reset')
            this.$set(item, 'meetingRecordingIntent', null)
            this.$set(item, 'meetingRecordingRequestedAt', null)
            this.$set(item, 'meetingRecordingStopConfirmations', 0)
            this.$set(item, 'meetingReceiverJoinedBbbReported', false)
            this.$set(item, 'receiverJoinedBbb', item.type === 'incoming')
            this.$set(item, 'awaitingMicrophoneAccess', false)
            this.$set(item, 'meetingIframeChecking', false)
            this.$set(item, 'meetingIframeRetryAttempt', 0)
            this.$set(item, 'meetingIframeDetachedByUnload', false)
            this.clearMeetingIframeHealthcheck(item.id)
            this.stopMeetingRecordingStatusPolling(item.id)
            this.syncIncomingSound()
            this.syncOutgoingSound()
            this.$nextTick(this.syncWindowMetrics)
            this.$nextTick(() => this.ensureMeetingIframeReady(item, { force: true }))
        },
        handleEndedCall(call, preferredType = null, retryPayload = null, currentId = null, startContext = null) {
            if (!this.callWindows.some(item => item.id === call.id))
                this.upsertCallWindow(call, preferredType || this.resolveCallType(call) || 'outgoing', retryPayload, currentId, startContext)

            const item = this.callWindows.find(windowItem => windowItem.id === call.id)
            if (!item)
                return

            this.$set(item, 'call', call)
            this.$set(item, 'meetingSourceUrl', null)
            this.logMeetingIframeState(item, 'handleEndedCall:before-reset')
            this.$set(item, 'embeddedMeetingUrl', null)
            this.$set(item, 'meetingAudioJoined', false)
            this.$set(item, 'meetingReadyToConnect', false)
            this.$set(item, 'meetingSelfMuted', false)
            this.setMeetingRecordingState(item, false, 'handleEndedCall:reset')
            this.$set(item, 'meetingRecordingIntent', null)
            this.$set(item, 'meetingRecordingRequestedAt', null)
            this.$set(item, 'meetingRecordingStopConfirmations', 0)
            this.$set(item, 'meetingReceiverJoinedBbbReported', false)
            this.$set(item, 'receiverJoinedBbb', false)
            this.$set(item, 'awaitingMicrophoneAccess', false)
            this.$set(item, 'meetingIframeChecking', false)
            this.$set(item, 'meetingIframeRetryAttempt', 0)
            this.$set(item, 'meetingIframeDetachedByUnload', false)
            this.clearMeetingIframeRetry(item.id)
            this.clearMeetingIframeHealthcheck(item.id)
            this.stopMeetingRecordingStatusPolling(item.id)
            this.syncIncomingSound()
            this.syncOutgoingSound()
            this.$nextTick(this.syncWindowMetrics)
        },
        getMeetingUrl(call) {
            const meetingUrl = call?.meeting?.url || null

            if (!meetingUrl)
                return null

            if (process.env.NODE_ENV === 'dev')
                return meetingUrl.replace('https://bkz.centersoft.kz', 'http://d.centersoft.kz:8080')

            return meetingUrl
        },
        getMeetingIframeAllow(embeddedMeetingUrl) {
            const defaultAllow = 'camera; microphone; display-capture; autoplay; fullscreen'
            const allowedOrigins = MEETING_IFRAME_ALLOWED_ORIGINS.join(' ')

            //if (process.env.NODE_ENV === 'production')
            //return defaultAllow

            return `microphone ${allowedOrigins}; camera ${allowedOrigins}; display-capture ${allowedOrigins}; autoplay ${allowedOrigins}; fullscreen ${allowedOrigins}`
        },
        shouldRenderMeetingIframe(item) {
            return this.isMeetingEmbedded(item) && !item?.meetingIframeDetachedByUnload
        },
        clearMeetingIframeRetry(id) {
            if (!this.meetingIframeRetryTimeouts[id])
                return

            clearTimeout(this.meetingIframeRetryTimeouts[id])
            this.$delete(this.meetingIframeRetryTimeouts, id)
        },
        clearMeetingIframeHealthcheck(id) {
            if (!this.meetingIframeHealthcheckTimeouts[id])
                return

            clearTimeout(this.meetingIframeHealthcheckTimeouts[id])
            this.$delete(this.meetingIframeHealthcheckTimeouts, id)
        },
        markMeetingIframeReady(item) {
            if (!item?.id)
                return

            this.clearMeetingIframeHealthcheck(item.id)
            this.$set(item, 'meetingIframeChecking', false)
            this.$set(item, 'meetingIframeRetryAttempt', 0)
        },
        armMeetingIframeHealthcheck(item, probeToken) {
            if (!item?.id)
                return

            this.clearMeetingIframeHealthcheck(item.id)
            this.meetingIframeHealthcheckTimeouts[item.id] = setTimeout(() => {
                this.$delete(this.meetingIframeHealthcheckTimeouts, item.id)
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (!activeItem || !this.isCallInProgress(activeItem))
                    return

                if (activeItem.meetingIframeProbeToken !== probeToken || activeItem.meetingAudioJoined || activeItem.meetingReadyToConnect)
                    return

                this.$set(activeItem, 'meetingIframeChecking', false)
                this.$set(activeItem, 'meetingIframeRetryAttempt', (activeItem.meetingIframeRetryAttempt || 0) + 1)
                this.scheduleMeetingIframeRetry(activeItem)
            }, MEETING_IFRAME_HEALTHCHECK_TIMEOUT)
        },
        scheduleMeetingIframeRetry(item) {
            if (!item?.id)
                return

            this.clearMeetingIframeRetry(item.id)
            this.meetingIframeRetryTimeouts[item.id] = setTimeout(() => {
                this.$delete(this.meetingIframeRetryTimeouts, item.id)
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (!activeItem || !activeItem.meetingSourceUrl || !this.isCallInProgress(activeItem))
                    return

                this.ensureMeetingIframeReady(activeItem, { force: true })
            }, MEETING_IFRAME_RETRY_DELAY)
        },
        async ensureMeetingIframeReady(item, { force = false } = {}) {
            if (!item?.id)
                return

            const meetingUrl = item.meetingSourceUrl || this.getMeetingUrl(item.call) || null
            if (!meetingUrl) {
                this.$set(item, 'embeddedMeetingUrl', null)
                return
            }

            if (!force && item.meetingIframeChecking)
                return

            this.logMeetingIframeState(item, 'ensureMeetingIframeReady:start', { force, meetingUrl })
            const probeToken = (item.meetingIframeProbeToken || 0) + 1
            this.$set(item, 'meetingSourceUrl', meetingUrl)
            this.$set(item, 'meetingIframeProbeToken', probeToken)
            this.$set(item, 'meetingIframeChecking', true)
            this.$set(item, 'embeddedMeetingUrl', null)
            this.$set(item, 'meetingAudioJoined', false)
            this.$set(item, 'meetingReadyToConnect', false)
            this.$set(item, 'meetingSelfMuted', false)
            this.setMeetingRecordingState(item, false, 'ensureMeetingIframeReady:reset', { force, probeToken })
            this.$set(item, 'meetingRecordingIntent', null)
            this.$set(item, 'meetingRecordingRequestedAt', null)
            this.$set(item, 'meetingRecordingStopConfirmations', 0)
            this.$set(item, 'meetingIframeDetachedByUnload', false)
            this.clearMeetingIframeRetry(item.id)
            this.clearMeetingIframeHealthcheck(item.id)
            this.$set(item, 'meetingIframeRenderKey', (item.meetingIframeRenderKey || 0) + 1)
            this.$nextTick(() => {
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (!activeItem || activeItem.meetingIframeProbeToken !== probeToken || !this.isCallInProgress(activeItem))
                    return

                this.$set(activeItem, 'embeddedMeetingUrl', meetingUrl)
            })
        },
        handleMeetingIframeLoad(item) {
            if (!item?.id || !item?.embeddedMeetingUrl)
                return

            this.logMeetingIframeState(item, 'handleMeetingIframeLoad:start')
            this.$set(item, 'meetingAudioJoined', false)
            this.$set(item, 'meetingReadyToConnect', false)
            this.$set(item, 'meetingSelfMuted', false)
            this.setMeetingRecordingState(item, false, 'handleMeetingIframeLoad:reset')
            this.$set(item, 'meetingRecordingIntent', null)
            this.$set(item, 'meetingRecordingRequestedAt', null)
            this.$set(item, 'meetingRecordingStopConfirmations', 0)
            const probeToken = item.meetingIframeProbeToken
            const iframe = this.getMeetingIframe(item)

            try {
                const iframeDocument = iframe?.contentDocument
                const iframeLocation = iframe?.contentWindow?.location?.href || ''
                const iframeText = `${iframeDocument?.title || ''} ${iframeDocument?.body?.innerText || ''}`.toLowerCase()
                if (iframeLocation || iframeText) {
                    const has503State = iframeText.includes('503')
                        || iframeText.includes('service temporarily unavailable')
                        || iframeLocation.includes('/503')

                    if (has503State) {
                        this.logMeetingIframeState(item, 'handleMeetingIframeLoad:503-retry')
                        this.$set(item, 'meetingIframeChecking', false)
                        this.$set(item, 'meetingIframeRetryAttempt', (item.meetingIframeRetryAttempt || 0) + 1)
                        this.$set(item, 'embeddedMeetingUrl', null)
                        this.scheduleMeetingIframeRetry(item)
                        return
                    }
                }
            } catch (e) {}

            this.armMeetingIframeHealthcheck(item, probeToken)
            this.requestMeetingState(item)
        },
        getMeetingIframe(item) {
            const iframeRef = this.$refs[`meetingIframe-${item.id}`]
            return Array.isArray(iframeRef) ? iframeRef[0] : iframeRef
        },
        postMessageToMeeting(item, message) {
            const iframe = this.getMeetingIframe(item)
            const targetWindow = iframe?.contentWindow

            if (!targetWindow)
                return

            try {
                console.log('[Meeting iframe][outgoing]', {
                    callId: item?.id || null,
                    message,
                    at: new Date().toISOString()
                })
                targetWindow.postMessage(message, MEETING_IFRAME_ORIGIN)
            } catch (e) {}
        },
        requestMeetingAudioStatus(item) {
            this.postMessageToMeeting(item, 'get_audio_joined_status')
        },
        requestMeetingMuteStatus(item) {
            this.postMessageToMeeting(item, 'c_mute_status')
        },
        requestMeetingRecordingStatus(item) {
            this.postMessageToMeeting(item, 'c_recording_status')
        },
        requestMeetingState(item) {
            this.requestMeetingAudioStatus(item)
            this.requestMeetingMuteStatus(item)
            this.requestMeetingRecordingStatus(item)
        },
        async reportCallReceiverJoinedBbb(item) {
            if (!item?.id || item.type !== 'incoming' || item.meetingReceiverJoinedBbbReported)
                return

            this.$set(item, 'meetingReceiverJoinedBbbReported', true)

            try {
                await axios.post(`/meetings/calls/${item.id}/report_call_receiver_joined_bbb/`)
            } catch (error) {
                this.$set(item, 'meetingReceiverJoinedBbbReported', false)
                errorHandler({ error })
            }
        },
        toggleMeetingMute(item) {
            if (!item?.embeddedMeetingUrl || item?.awaitingMicrophoneAccess)
                return

            if (!item.meetingReadyToConnect && !item.meetingAudioJoined) {
                this.requestMeetingState(item)
                return
            }

            this.postMessageToMeeting(item, 'c_mute')
        },
        toggleMeetingRecording(item) {
            if (!item?.embeddedMeetingUrl || item?.awaitingMicrophoneAccess)
                return

            if (!item.meetingReadyToConnect && !item.meetingAudioJoined) {
                this.requestMeetingState(item)
                return
            }

            const nextRecordingIntent = item.meetingRecordingActive ? 'stop' : 'start'
            this.$set(item, 'meetingRecordingIntent', nextRecordingIntent)
            this.$set(item, 'meetingRecordingRequestedAt', Date.now())
            this.$set(item, 'meetingRecordingStopConfirmations', 0)
            if (nextRecordingIntent === 'start')
                this.setMeetingRecordingState(item, true, 'toggleMeetingRecording:optimistic-start')
            this.logMeetingIframeState(item, 'toggleMeetingRecording', {
                intendedAction: item.meetingRecordingIntent
            })
            this.setActionLoading(item.id, 'recording')
            this.postMessageToMeeting(item, 'c_record')
            window.setTimeout(() => {
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (!activeItem || activeItem.actionLoading !== 'recording')
                    return

                const startedRecently = activeItem.meetingRecordingIntent === 'start'
                    && activeItem.meetingRecordingRequestedAt
                    && (Date.now() - activeItem.meetingRecordingRequestedAt) < MEETING_RECORDING_START_GRACE_PERIOD
                if (startedRecently)
                    return

                this.requestMeetingRecordingStatus(activeItem)
            }, 300)
        },
        findMeetingItemByEventSource(sourceWindow) {
            return this.callWindows.find(item => this.getMeetingIframe(item)?.contentWindow === sourceWindow) || null
        },
        handleMeetingMessage(event) {
            if (event.origin !== MEETING_IFRAME_ORIGIN)
                return

            console.log('[Meeting iframe][incoming]', {
                callId: this.findMeetingItemByEventSource(event.source)?.id || null,
                data: event?.data,
                origin: event.origin,
                at: new Date().toISOString()
            })

            const response = event?.data?.response
            if (response === 'joinedAudio' || response === 'notInAudio')
                console.log('[BBB AUDIO STATE]', response, event.data)

            if (!['readyToConnect', 'joinedAudio', 'notInAudio', 'selfMuted', 'selfUnmuted', 'recordingStarted', 'recordingStopped'].includes(response))
                return

            const item = this.findMeetingItemByEventSource(event.source)
            if (!item)
                return

            this.markMeetingIframeReady(item)

            if (response === 'readyToConnect') {
                this.$set(item, 'meetingReadyToConnect', true)
                this.requestMeetingMuteStatus(item)
                this.requestMeetingRecordingStatus(item)
                this.startMeetingRecordingStatusPolling(item)
                return
            }

            if (response === 'joinedAudio') {
                this.$set(item, 'meetingAudioJoined', true)
                this.reportCallReceiverJoinedBbb(item)
                return
            }

            if (response === 'selfMuted') {
                this.$set(item, 'meetingAudioJoined', true)
                this.$set(item, 'meetingSelfMuted', true)
                return
            }

            if (response === 'selfUnmuted') {
                this.$set(item, 'meetingAudioJoined', true)
                this.$set(item, 'meetingSelfMuted', false)
                return
            }

            if (response === 'recordingStarted') {
                this.setMeetingRecordingState(item, true, 'handleMeetingMessage:recordingStarted')
                this.$set(item, 'meetingRecordingIntent', null)
                this.$set(item, 'meetingRecordingRequestedAt', null)
                this.$set(item, 'meetingRecordingStopConfirmations', 0)
                this.setActionLoading(item.id, null)
                return
            }

            if (response === 'recordingStopped') {
                const recordingIntent = item.meetingRecordingIntent || null
                const startedRecently = recordingIntent === 'start'
                    && item.meetingRecordingRequestedAt
                    && (Date.now() - item.meetingRecordingRequestedAt) < MEETING_RECORDING_START_GRACE_PERIOD
                const stopConfirmations = (item.meetingRecordingStopConfirmations || 0) + 1
                this.$set(item, 'meetingRecordingStopConfirmations', stopConfirmations)

                if (startedRecently) {
                    this.logMeetingIframeState(item, 'handleMeetingMessage:recordingStopped:ignored-during-start-grace', {
                        stopConfirmations
                    })
                    return
                }

                if (recordingIntent === 'stop') {
                    this.setMeetingRecordingState(item, false, 'handleMeetingMessage:recordingStopped:intent-stop', {
                        stopConfirmations
                    })
                    this.$set(item, 'meetingRecordingIntent', null)
                    this.$set(item, 'meetingRecordingRequestedAt', null)
                    this.$set(item, 'meetingRecordingStopConfirmations', 0)
                    this.setActionLoading(item.id, null)
                    return
                }

                if (!item.meetingRecordingActive && stopConfirmations >= MEETING_RECORDING_STOP_CONFIRMATIONS) {
                    this.$set(item, 'meetingRecordingIntent', null)
                    this.$set(item, 'meetingRecordingRequestedAt', null)
                    this.$set(item, 'meetingRecordingStopConfirmations', 0)
                    this.setActionLoading(item.id, null)
                    return
                }

                if (item.meetingRecordingActive && stopConfirmations >= MEETING_RECORDING_STOP_CONFIRMATIONS) {
                    this.setMeetingRecordingState(item, false, 'handleMeetingMessage:recordingStopped:confirmed', {
                        stopConfirmations
                    })
                    this.$set(item, 'meetingRecordingIntent', null)
                    this.$set(item, 'meetingRecordingRequestedAt', null)
                    this.$set(item, 'meetingRecordingStopConfirmations', 0)
                    this.setActionLoading(item.id, null)
                }

                return
            }

            this.$set(item, 'meetingAudioJoined', false)
        },
        isMeetingEmbedded(item) {
            return !!item?.embeddedMeetingUrl
        },
        getMeetingOverlayText(item) {
            if (!this.isMeetingEmbedded(item) && !item?.meetingIframeChecking)
                return ''

            if (item?.meetingIframeChecking || item?.meetingIframeRetryAttempt) {
                return this.$te('meeting.audio_connecting')
                    ? this.$t('meeting.audio_connecting')
                    : 'Идет подключение к аудио...'
            }

            if (item?.restoredFromBootstrap && this.isCallInProgress(item) && !item?.meetingAudioJoined) {
                return this.$te('meeting.audio_connecting')
                    ? this.$t('meeting.audio_connecting')
                    : 'Идет подключение к аудио...'
            }

            if (item.type === 'outgoing' && this.isCallInProgress(item) && !item.receiverJoinedBbb) {
                return this.$te('meeting.audio_connecting')
                    ? this.$t('meeting.audio_connecting')
                    : 'Идет подключение к аудио...'
            }

            if (item?.meetingReadyToConnect && !item?.meetingAudioJoined) {
                return this.$te('meeting.audio_connecting')
                    ? this.$t('meeting.audio_connecting')
                    : 'Идет подключение к аудио...'
            }

            return ''
        },
        getCallDurationText(item) {
            if (!this.isCallInProgress(item))
                return ''

            return this.formatCallDuration(item?.call?.started_at, this.callDurationNow)
        },
        getEndedCallDurationText(item) {
            if (!this.isCallEnded(item))
                return ''

            const call = item?.call || {}
            const endedAt = call.ended_at || call.finished_at || call.updated_at || call.status_updated_at || this.callDurationNow

            return this.formatCallDuration(call.started_at, endedAt)
        },
        formatCallDuration(startedAt, endedAt) {
            if (!startedAt)
                return '00:00:00'

            const startedAtMs = new Date(startedAt).getTime()
            const endedAtMs = new Date(endedAt).getTime()
            if (!startedAtMs || !endedAtMs)
                return '00:00:00'

            const totalSeconds = Math.max(0, Math.floor((endedAtMs - startedAtMs) / 1000))

            return this.formatDurationSeconds(totalSeconds)
        },
        formatDurationSeconds(totalSeconds) {
            const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0')
            const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0')
            const seconds = String(totalSeconds % 60).padStart(2, '0')

            return `${hours}:${minutes}:${seconds}`
        },
        isCallInProgress(item) {
            return this.getStatusCode(item?.call) === 'in_call'
        },
        isCallEnded(item) {
            return this.getStatusCode(item?.call) === 'ended'
        },
        shouldHideMeetingIframe(item) {
            if (item?.restoredFromBootstrap)
                return true

            return this.isCallInProgress(item)
        },
        getStatusCode(call) {
            return call?.status?.code || null
        },
        getStatusName(call) {
            return call?.status?.name || ''
        },
        getStatusLabel(code, fallback = '') {
            const labels = {
                ringing: this.$t('meeting.call_status_ringing'),
                in_call: this.$t('meeting.call_status_in_call'),
                ended: this.$te('meeting.call_status_ended')
                    ? this.$t('meeting.call_status_ended')
                    : 'Завершен',
                cancelled_by_receiver: this.$t('meeting.call_status_cancelled_by_receiver'),
                cancelled_by_caller: this.$t('meeting.call_status_cancelled_by_caller'),
                missed: this.$t('meeting.call_status_missed'),
                receiver_offline: this.$te('meeting.call_receiver_offline_short')
                    ? this.$t('meeting.call_receiver_offline_short')
                    : 'Собеседник не в сети'
            }

            return labels[code] || fallback || ''
        },
        getCallStatusText(item) {
            if (item.type === 'outgoing' && ['ringing', 'receiver_offline'].includes(this.getStatusCode(item.call)) && item.receiverPresenceState === 'offline') {
                return this.$te('meeting.call_receiver_offline_short')
                    ? this.$t('meeting.call_receiver_offline_short')
                    : 'Собеседник не в сети'
            }

            return this.getStatusLabel(this.getStatusCode(item.call), this.getStatusName(item.call))
        },
        getBodyStatusText(item) {
            const statusCode = this.getStatusCode(item.call)

            if (item?.awaitingMicrophoneAccess) {
                return this.$te('meeting.microphone_access_before_join')
                    ? this.$t('meeting.microphone_access_before_join')
                    : 'Разрешите доступ к микрофону, чтобы войти в звонок.'
            }

            if (item.type === 'outgoing' && ['ringing', 'receiver_offline'].includes(statusCode) && item.receiverPresenceState === 'offline') {
                return this.$te('meeting.call_receiver_offline')
                    ? this.$t('meeting.call_receiver_offline')
                    : 'Пользователь не в сети.'
            }

            if (item.type === 'outgoing' && statusCode === 'cancelled_by_receiver')
                return this.$t('meeting.call_declined_by_user')

            if (item.type === 'outgoing' && statusCode === 'missed')
                return this.$t('meeting.call_missed_by_user')

            if (statusCode === 'ended')
                return this.$te('meeting.call_ended')
                    ? this.$t('meeting.call_ended')
                    : 'Звонок завершен.'

            return ''
        },
        getEndCallText() {
            return this.$te('meeting.end_call')
                ? this.$t('meeting.end_call')
                : 'Завершить звонок'
        },
        getToggleMicrophoneText(item) {
            if (item?.meetingSelfMuted)
                return this.$te('meeting.unmute_microphone')
                    ? this.$t('meeting.unmute_microphone')
                    : 'Включить микрофон'

            return this.$te('meeting.mute_microphone')
                ? this.$t('meeting.mute_microphone')
                : 'Выключить микрофон'
        },
        getToggleRecordingText(item) {
            if (item?.meetingRecordingActive)
                return this.$te('meeting.stop_recording')
                    ? this.$t('meeting.stop_recording')
                    : 'Остановить запись'

            return this.$te('meeting.start_recording')
                ? this.$t('meeting.start_recording')
                : 'Начать запись'
        },
        getRecordingBadgeText() {
            return this.$te('meeting.recording_badge')
                ? this.$t('meeting.recording_badge')
                : 'Запись'
        },
        canRetryCall(item) {
            return item.type === 'outgoing'
                && !!item.retryPayload
                && ['cancelled_by_receiver', 'missed', 'receiver_offline'].includes(this.getStatusCode(item.call))
        },
        getRetryDismissText(item) {
            if (this.getStatusCode(item?.call) === 'receiver_offline')
                return this.$t('cancel')

            return this.$t('meeting.close')
        },
        hasHelpDeskTariff() {
            return Array.isArray(this.user?.tariff_section_codes)
                && this.user.tariff_section_codes.includes('help_desk')
        },
        canTransferCall(item) {
            if (!this.getCallTicket(item) || !this.hasHelpDeskTariff())
                return false

            if (this.isCallInProgress(item))
                return item?.call?.accepted_by?.id === this.user?.id

            return item?.type === 'incoming'
                && this.getStatusCode(item?.call) === 'ringing'
                && this.getTargets(item?.call).some(target => target?.id === this.user?.id)
        },
        getTransferCustomerCardId(item) {
            const ticket = this.getCallTicket(item)
            const ticketCustomerCard = ticket?.customer_card

            return (typeof ticketCustomerCard === 'string' ? ticketCustomerCard : null)
                || ticket?.customer_card?.id
                || ticket?.customer_card?.uid
                || ticket?.customer_card_id
                || item?.call?.customer_card?.id
                || item?.call?.customer_card?.uid
                || item?.call?.customer_card_id
                || null
        },
        async openTransferMode(item) {
            if (!this.canTransferCall(item))
                return

            this.$set(item, 'transferMode', true)

            if (item.transferUsersLoaded || item.transferLoading)
                return

            const customerCardId = this.getTransferCustomerCardId(item)
            if (!customerCardId) {
                this.$message.error(this.$te('meeting.transfer_users_error') ? this.$t('meeting.transfer_users_error') : 'Не удалось получить список специалистов')
                this.$set(item, 'transferMode', false)
                return
            }

            this.$set(item, 'transferLoading', true)

            try {
                const { data } = await axios.get(`/help_desk/customer_cards/${customerCardId}/specialists/actual/`, {
                    params: {
                        display: 'user',
                        page_size: 15,
                        page: 1
                    }
                })
                this.$set(
                    item,
                    'transferUsers',
                    Array.isArray(data?.results)
                        ? data.results.filter(userItem => userItem?.id && userItem.id !== this.user?.id)
                        : []
                )
                this.$set(item, 'transferUsersLoaded', true)
            } catch (error) {
                errorHandler({ error })
                this.$set(item, 'transferMode', false)
            } finally {
                this.$set(item, 'transferLoading', false)
            }
        },
        closeTransferMode(item) {
            if (!item?.id)
                return

            this.$set(item, 'transferMode', false)
            this.$set(item, 'transferSubmittingId', null)
        },
        async transferCall(item, userItem) {
            if (!item?.id || !userItem?.id || item.transferSubmittingId)
                return

            this.$set(item, 'transferSubmittingId', userItem.id)

            try {
                await axios.post(`/meetings/calls/${item.id}/transfer/`, {
                    to_profile_id: userItem.id
                })
                this.removeCallWindow(item.id)
                this.$message.success(this.$te('meeting.transfer_call_success') ? this.$t('meeting.transfer_call_success') : 'Звонок передан')
            } catch (error) {
                errorHandler({ error })
            } finally {
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (activeItem)
                    this.$set(activeItem, 'transferSubmittingId', null)
            }
        },
        getActionsClass(item) {
            if (item?.awaitingMicrophoneAccess)
                return 'call-window__actions--double'

            if (this.isCallEnded(item))
                return 'call-window__actions--single'

            if (item.type === 'incoming')
                return 'call-window__actions--incoming'

            if (this.isCallInProgress(item))
                return 'call-window__actions--triple'

            if (this.canRetryCall(item))
                return 'call-window__actions--double'

            return 'call-window__actions--single'
        },
        shouldShowChatButton(item) {
            if (!item?.call?.chat_uid)
                return false

            if (this.isCallEnded(item))
                return true

            return item.type === 'incoming' && this.getStatusCode(item.call) === 'ringing'
        },
        getCallTicket(item) {
            const ticket = item?.call?.ticket

            if (!ticket || typeof ticket !== 'object' || Array.isArray(ticket) || !ticket.id)
                return null

            return ticket
        },
        hasCallTicket(item) {
            return !!this.getCallTicket(item)
        },
        shouldShowTicketLink(item) {
            return !this.isCallEnded(item) && this.hasCallTicket(item)
        },
        openTicket(item) {
            const ticket = this.getCallTicket(item)
            if (!ticket?.id)
                return

            const query = { ...this.$route.query }
            if (!query.requestView) {
                query.requestView = ticket.id
                this.$router.push({ query }).catch(() => {})
                return
            }

            eventBus.$emit('ticket_request_drawer_close')
            setTimeout(() => {
                this.$router.push({
                    query: {
                        ...this.$route.query,
                        requestView: ticket.id
                    }
                }).catch(() => {})
            }, 500)
        },
        isCurrentChat(chatUid) {
            if (!chatUid)
                return false

            if (this.isMobile)
                return this.$route.name === 'chat-body' && this.$route.params.id === chatUid

            return this.$route.name === 'chat' && this.$route.query?.chat_id === chatUid
        },
        async writeInChat(item) {
            const chatUid = item?.call?.chat_uid
            if (!chatUid)
                return

            this.removeCallWindow(item.id)

            if (!this.isCurrentChat(chatUid))
                this.openChat(chatUid)
        },
        openChat(chatUid) {
            if (!chatUid)
                return

            if (this.isMobile) {
                const sameChat = this.$route.name === 'chat-body' && this.$route.params.id === chatUid

                if (sameChat) {
                    ChatEventBus.$emit('arreaScrollDown')
                    return
                }

                this.$router.push({
                    name: 'chat-body',
                    params: { id: chatUid }
                }).catch(() => {})

                return
            }

            const nextQuery = JSON.parse(JSON.stringify(this.$route.query || {}))
            const sameChat = this.$route.name === 'chat' && nextQuery.chat_id === chatUid
            nextQuery.chat_id = chatUid

            if (this.$route.name === 'chat') {
                this.$router.replace({ query: nextQuery })
                    .then(() => {
                        if (sameChat) {
                            ChatEventBus.$emit('arreaScrollDown')
                        } else
                            eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                    })
                    .catch(() => {})
                return
            }

            this.$router.push({ name: 'chat', query: { chat_id: chatUid } })
                .then(() => {
                    eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                })
                .catch(() => {})
        },
        getDisplayUser(item) {
            if (!item)
                return null

            if (item.type === 'incoming')
                return item.call?.initiator || null

            return this.getTargets(item.call)[0] || item.targetSnapshot?.[0] || null
        },
        getDisplayUserId(item) {
            const user = this.getDisplayUser(item)

            return user?.id || user?.uid || null
        },
        getDisplayUserAvatarKey(item) {
            const displayUserId = this.getDisplayUserId(item)

            return `call-window-avatar-${item?.id || 'unknown'}-${displayUserId || 'unknown'}`
        },
        getDisplayName(user) {
            if (!user)
                return this.$t('meeting.unknown_user')

            if (user.full_name)
                return user.full_name

            return [user.last_name, user.first_name, user.middle_name].filter(Boolean).join(' ') || user.username || this.$t('meeting.unknown_user')
        },
        getUserAvatar(user) {
            return user?.avatar?.path || user?.avatar || null
        },
        getUserInitials(user) {
            const name = this.getDisplayName(user)
            const parts = name.split(' ').filter(Boolean)

            return parts.slice(0, 2).map(part => part.charAt(0).toUpperCase()).join('') || '?'
        },
        getWindowStyle(item, index) {
            if (this.isMobile) {
                return {
                    top: '0',
                    right: '0',
                    bottom: '0',
                    left: '0',
                    width: '100vw',
                    height: '100dvh',
                    zIndex: 2147483646
                }
            }

            const position = item.x === null || item.y === null
                ? this.getDefaultPosition(index, item)
                : { x: item.x, y: item.y }

            return {
                left: `${position.x}px`,
                top: `${position.y}px`,
                zIndex: item.zIndex
            }
        },
        getDefaultPosition(index, item = {}) {
            const width = this.windowWidth || window.innerWidth
            const height = this.windowHeight || window.innerHeight
            const itemWidth = item.width || CALL_WINDOW_WIDTH
            const itemHeight = item.height || CALL_WINDOW_HEIGHT
            const columns = Math.max(1, Math.floor((width - (CALL_WINDOW_MARGIN * 2) + CALL_WINDOW_GAP) / (itemWidth + CALL_WINDOW_GAP)))
            const columnIndex = index % columns
            const rowIndex = Math.floor(index / columns)
            const x = Math.max(0, width - CALL_WINDOW_MARGIN - itemWidth - (columnIndex * (itemWidth + CALL_WINDOW_GAP)))
            const y = Math.max(0, height - CALL_WINDOW_MARGIN - itemHeight - (rowIndex * (itemHeight + CALL_WINDOW_GAP)))

            return { x, y }
        },
        syncWindowMetrics() {
            const refs = Array.isArray(this.$refs.callWindow) ? this.$refs.callWindow : [this.$refs.callWindow].filter(Boolean)
            const viewportWidth = this.windowWidth || window.innerWidth
            const viewportHeight = this.windowHeight || window.innerHeight

            refs.forEach((el, index) => {
                const item = this.callWindows[index]
                if (!el || !item)
                    return

                const rect = el.getBoundingClientRect()
                const width = Math.round(rect.width)
                const height = Math.round(rect.height)
                const widthChanged = item.width !== width
                const heightChanged = item.height !== height

                if (widthChanged)
                    this.$set(item, 'width', width)

                if (heightChanged)
                    this.$set(item, 'height', height)

                if (!item.manuallyMoved && (widthChanged || heightChanged)) {
                    const nextPosition = this.getDefaultPosition(index, {
                        width,
                        height
                    })
                    this.$set(item, 'x', nextPosition.x)
                    this.$set(item, 'y', nextPosition.y)
                    return
                }

                const maxX = Math.max(0, viewportWidth - width)
                const maxY = Math.max(0, viewportHeight - height)

                if (item.x > maxX)
                    this.$set(item, 'x', maxX)

                if (item.y > maxY)
                    this.$set(item, 'y', maxY)
            })
        },
        nextZIndex() {
            this.zIndexCounter += 1
            return this.zIndexCounter
        },
        bringToFront(id) {
            const index = this.callWindows.findIndex(item => item.id === id)
            if (index === -1)
                return

            this.$set(this.callWindows[index], 'zIndex', this.nextZIndex())
        },
        startDrag(event, id) {
            if (this.isMobile)
                return

            const item = this.callWindows.find(windowItem => windowItem.id === id)
            if (!item)
                return

            this.bringToFront(id)
            this.$set(item, 'manuallyMoved', true)
            this.dragData = {
                id,
                offsetX: event.clientX - item.x,
                offsetY: event.clientY - item.y
            }
        },
        onDrag(event) {
            if (!this.dragData)
                return

            const index = this.callWindows.findIndex(item => item.id === this.dragData.id)
            if (index === -1)
                return

            const viewportWidth = this.windowWidth || window.innerWidth
            const viewportHeight = this.windowHeight || window.innerHeight
            const item = this.callWindows[index]
            const itemWidth = item?.width || CALL_WINDOW_WIDTH
            const itemHeight = item?.height || CALL_WINDOW_HEIGHT
            const maxX = Math.max(0, viewportWidth - itemWidth)
            const maxY = Math.max(0, viewportHeight - itemHeight)
            const nextX = Math.min(Math.max(0, event.clientX - this.dragData.offsetX), maxX)
            const nextY = Math.min(Math.max(0, event.clientY - this.dragData.offsetY), maxY)

            this.$set(this.callWindows[index], 'x', nextX)
            this.$set(this.callWindows[index], 'y', nextY)
        },
        stopDrag() {
            this.dragData = null
        },
        setActionLoading(id, actionLoading) {
            const index = this.callWindows.findIndex(item => item.id === id)
            if (index === -1)
                return

            this.$set(this.callWindows[index], 'actionLoading', actionLoading)
        },
        hasUnloadProtectedCall() {
            return this.callWindows.some(item => ['ringing', 'in_call'].includes(this.getStatusCode(item.call)))
        },
        syncUnloadProtectionFlag() {
            if (typeof window === 'undefined')
                return

            window.__meetingCallUnloadProtected__ = this.hasUnloadProtectedCall()
        },
        detachMeetingIframesForUnloadAttempt() {
            const hasMeetingIframe = this.callWindows.some(item => this.isCallInProgress(item) && (item.meetingSourceUrl || item.embeddedMeetingUrl))
            if (!hasMeetingIframe)
                return

            this.unloadAttemptActive = true
            this.callWindows.forEach(item => {
                if (!this.isCallInProgress(item) || !(item.meetingSourceUrl || item.embeddedMeetingUrl))
                    return

                this.clearMeetingIframeHealthcheck(item.id)
                this.stopMeetingRecordingStatusPolling(item.id)
                this.$set(item, 'meetingIframeDetachedByUnload', true)
                this.$set(item, 'embeddedMeetingUrl', null)
                this.$set(item, 'meetingAudioJoined', false)
                this.$set(item, 'meetingReadyToConnect', false)
                this.$set(item, 'meetingSelfMuted', false)
                this.setMeetingRecordingState(item, false, 'detachMeetingIframesForUnloadAttempt:reset')
                this.$set(item, 'meetingRecordingIntent', null)
                this.$set(item, 'meetingRecordingRequestedAt', null)
                this.$set(item, 'meetingRecordingStopConfirmations', 0)
            })
        },
        startMeetingRecordingStatusPolling(item) {
            if (!item?.id || this.meetingRecordingStatusIntervals[item.id])
                return

            this.requestMeetingRecordingStatus(item)
            this.meetingRecordingStatusIntervals[item.id] = setInterval(() => {
                const activeItem = this.callWindows.find(windowItem => windowItem.id === item.id)
                if (!activeItem || !this.isCallInProgress(activeItem) || !activeItem.embeddedMeetingUrl)
                    return

                const startedRecently = activeItem.meetingRecordingIntent === 'start'
                    && activeItem.meetingRecordingRequestedAt
                    && (Date.now() - activeItem.meetingRecordingRequestedAt) < MEETING_RECORDING_START_GRACE_PERIOD
                if (startedRecently)
                    return

                this.requestMeetingRecordingStatus(activeItem)
            }, MEETING_RECORDING_POLL_INTERVAL)
        },
        stopMeetingRecordingStatusPolling(id) {
            if (!this.meetingRecordingStatusIntervals[id])
                return

            clearInterval(this.meetingRecordingStatusIntervals[id])
            this.$delete(this.meetingRecordingStatusIntervals, id)
        },
        scheduleMeetingIframeRestoreAfterUnloadPrompt() {
            if (this.unloadIframeRestoreTimeout)
                clearTimeout(this.unloadIframeRestoreTimeout)

            this.unloadIframeRestoreTimeout = setTimeout(() => {
                this.unloadIframeRestoreTimeout = null
                this.restoreMeetingIframesAfterCancelledUnload()
            }, 50)
        },
        restoreMeetingIframesAfterCancelledUnload() {
            if (!this.unloadAttemptActive)
                return

            this.unloadAttemptActive = false
            this.callWindows.forEach(item => {
                if (!item?.meetingIframeDetachedByUnload || !item?.meetingSourceUrl || !this.isCallInProgress(item))
                    return

                this.$set(item, 'meetingIframeDetachedByUnload', false)
                this.ensureMeetingIframeReady(item, { force: true })
            })
        },
        handleBeforeUnload(event) {
            if (!this.hasUnloadProtectedCall())
                return undefined

            this.detachMeetingIframesForUnloadAttempt()
            this.scheduleMeetingIframeRestoreAfterUnloadPrompt()
            event.preventDefault()
            event.returnValue = ''
            return ''
        },
        handleReloadShortcut(event) {
            if (!this.hasUnloadProtectedCall())
                return

            const isF5 = event.key === 'F5'
            const isReloadCombination = (event.ctrlKey || event.metaKey) && String(event.key).toLowerCase() === 'r'

            if (!isF5 && !isReloadCombination)
                return

            event.preventDefault()
            event.stopPropagation()
            this.detachMeetingIframesForUnloadAttempt()

            const message = this.$te('meeting.call_leave_warning')
                ? this.$t('meeting.call_leave_warning')
                : 'Сейчас идет звонок. Если перезагрузить страницу, звонок может прерваться.'

            if (!window.confirm(message)) {
                this.restoreMeetingIframesAfterCancelledUnload()
                return
            }

            if (typeof window !== 'undefined')
                window.__meetingCallUnloadProtected__ = false

            if (window.onbeforeunload === this.handleBeforeUnload)
                window.onbeforeunload = this.previousBeforeUnload || null

            window.removeEventListener('beforeunload', this.handleBeforeUnload)
            window.location.reload()
        }
    },
    sockets: {
        notify(data) {
            if (this.isCallPopupMode) return
            this.handleNotifyEvent(data)
        },
        call_updated(data) {
            if (this.isCallPopupMode) return
            this.handleNotifyEvent(data)
        },
        call_created(data) {
            if (this.isCallPopupMode) return
            this.handleNotifyEvent(data)
        },
        call_receiver_presence(data) {
            if (this.isCallPopupMode) return
            this.handleReceiverPresenceEvent(data)
        }
    },
    mounted() {
        // In popup mode we are a stub — skip all call logic
        if (this.isCallPopupMode) return

        // Cross-window channel for popup stub communication
        CallPopupChannel.init()
        this.callPopupChannelUnsubscribe = CallPopupChannel.onMessage(this.handlePopupMessage)

        eventBus.$on(CALL_START_EVENT, this.startCall)
        eventBus.$on(CALL_RESTORE_EVENT, this.restoreCalls)
        if (Array.isArray(window.__meetingActiveCallsBootstrap__) && window.__meetingActiveCallsBootstrap__.length) {
            this.restoreCalls(window.__meetingActiveCallsBootstrap__)
            window.__meetingActiveCallsBootstrap__ = []
        }
        this.callDurationTimer = setInterval(() => {
            this.callDurationNow = Date.now()
        }, 1000)
        this.syncUnloadProtectionFlag()
        this.syncOutgoingSound()
        window.addEventListener('mousemove', this.onDrag)
        window.addEventListener('mouseup', this.stopDrag)
        window.addEventListener('resize', this.syncWindowMetrics)
        window.addEventListener('keydown', this.handleReloadShortcut, true)
        window.addEventListener('message', this.handleMeetingMessage)
        document.addEventListener('visibilitychange', this.handleVisibilityChange)
        window.addEventListener('focus', this.handleWindowFocus)
        window.addEventListener('blur', this.handleWindowBlur)
        window.addEventListener('storage', this.handleActiveTabStorage)
        window.addEventListener('beforeunload', this.handleBeforeUnload)
        this.previousBeforeUnload = window.onbeforeunload
        window.onbeforeunload = this.handleBeforeUnload
    },
    beforeDestroy() {
        // Popup stub mode — nothing was initialized
        if (this.isCallPopupMode) return

        // Cleanup popup channel subscription
        if (typeof this.callPopupChannelUnsubscribe === 'function')
            this.callPopupChannelUnsubscribe()
        if (this.callPopupCheckTimer)
            clearTimeout(this.callPopupCheckTimer)
        if (this._broadcastStateTimer)
            clearTimeout(this._broadcastStateTimer)
        this.closeCallPopup()
        CallPopupChannel.destroy()

        if (this.incomingSoundActive)
            SoundMaster.stopLoop('call_incoming')
        if (this.outgoingSoundActive)
            SoundMaster.stopLoop('call_sending')
        if (this.callDurationTimer)
            clearInterval(this.callDurationTimer)
        this.clearAllCallActivity()
        Object.keys(this.meetingIframeRetryTimeouts).forEach(id => this.clearMeetingIframeRetry(id))
        Object.keys(this.meetingIframeHealthcheckTimeouts).forEach(id => this.clearMeetingIframeHealthcheck(id))
        Object.keys(this.meetingRecordingStatusIntervals).forEach(id => this.stopMeetingRecordingStatusPolling(id))
        if (this.unloadIframeRestoreTimeout)
            clearTimeout(this.unloadIframeRestoreTimeout)
        if (typeof window !== 'undefined')
            window.__meetingCallUnloadProtected__ = false
        eventBus.$off(CALL_START_EVENT, this.startCall)
        eventBus.$off(CALL_RESTORE_EVENT, this.restoreCalls)
        window.removeEventListener('mousemove', this.onDrag)
        window.removeEventListener('mouseup', this.stopDrag)
        window.removeEventListener('resize', this.syncWindowMetrics)
        window.removeEventListener('keydown', this.handleReloadShortcut, true)
        window.removeEventListener('message', this.handleMeetingMessage)
        document.removeEventListener('visibilitychange', this.handleVisibilityChange)
        window.removeEventListener('focus', this.handleWindowFocus)
        window.removeEventListener('blur', this.handleWindowBlur)
        window.removeEventListener('storage', this.handleActiveTabStorage)
        window.removeEventListener('beforeunload', this.handleBeforeUnload)
        if (window.localStorage.getItem(OUTGOING_SOUND_OWNER_STORAGE_KEY) === this.activeTabId)
            window.localStorage.removeItem(OUTGOING_SOUND_OWNER_STORAGE_KEY)
        if (window.onbeforeunload === this.handleBeforeUnload)
            window.onbeforeunload = this.previousBeforeUnload || null
    }
}
</script>

<style scoped lang="scss">
.ico_btn{
    font-size: 18px;
}
.meeting-call-layer {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 12000;
}

.call-window {
    position: fixed;
    width: 320px;
    background: #fff;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 18px 48px rgba(16, 24, 40, 0.22);
    pointer-events: auto;
    user-select: none;
}

.call-window--meeting {
    width: min(960px, calc(100vw - 32px));
}

.call-window-transition-enter-active,
.call-window-transition-leave-active {
    transition: opacity .24s ease, transform .24s ease;
}

.call-window-transition-enter,
.call-window-transition-leave-to {
    opacity: 0;
    transform: translateY(24px);
}

.call-window__header {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 16px 14px;
    color: #fff;
    background: linear-gradient(135deg, #2b59ff 0%, #3554d1 100%);
    transition: background .28s ease;
    cursor: move;
}

.call-window__header--active {
    background: linear-gradient(135deg, #00c94d 0%, #00a63f 100%);
}

.call-window__drag-handle {
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 28px;
    height: 3px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.55);
}

.call-window__header-icon {
    width: 40px;
    height: 40px;
    flex: 0 0 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.call-window__header-title {
    font-size: 16px;
    font-weight: 700;
    line-height: 1.2;
}

.call-window__header-status {
    margin-top: 2px;
    font-size: 13px;
    line-height: 1.2;
    opacity: 0.8;
}

.call-window__body {
    position: relative;
    padding: 20px 16px 16px;
}

.call-window__footer {
    margin-top: 20px;
}

.call-window__ended-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: center;
}

.call-window__body--meeting {
    padding: 0;
    height: min(640px, calc(100vh - 140px));
}

.call-window__user {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.call-window__recording-badge {
    margin-bottom: 10px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(220, 38, 38, 0.12);
    color: #b91c1c;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.2;
}

.call-window__name {
    margin-top: 12px;
    font-size: 16px;
    font-weight: 700;
    line-height: 1.25;
    color: #1f2937;
    word-break: break-word;
    overflow-wrap: anywhere;
}

.call-window__subtitle {
    margin-top: 4px;
    font-size: 13px;
    line-height: 1.35;
    color: #6b7280;
}

.call-window__body-status {
    margin-top: 14px;
    text-align: center;
    font-size: 13px;
    line-height: 1.4;
    color: #4b5563;
}

.call-window__ended-duration {
    margin-top: 12px;
    text-align: center;
}

.call-window__ended-duration-label {
    font-size: 13px;
    line-height: 1.4;
    color: #6b7280;
}

.call-window__ended-duration-value {
    margin-top: 4px;
    font-size: 18px;
    font-weight: 500;
    line-height: 1.3;
    color: #374151;
}

.call-window__actions {
    display: flex;
    gap: 12px;
    margin-top: 20px;
}

.call-window__chat-btn {
    margin-top: 12px;
}

.call-window__ticket-btn {
    max-width: 220px;
}

.call-window__ended-buttons .call-window__ticket-btn,
.call-window__ended-buttons .call-window__chat-btn {
    width: 100%;
    max-width: 220px;
}

.call-window__ended-buttons .call-window__chat-btn {
    margin-top: 0;
}

.call-window__ticket-link {
    width: 100%;
    margin-top: -8px;
    margin-bottom: 0;
    text-align: center;
    color: var(--blue);
    cursor: pointer;
}

.call-window__ticket-link + .call-window__actions {
    margin-top: 5px;
}

.call-window__iframe {
    display: block;
    width: 100%;
    height: 100%;
    min-height: min(640px, calc(100vh - 140px));
    border: 0;
    background: #f3f4f6;
}

.call-window__iframe--hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    min-height: 1px;
    opacity: 0;
    pointer-events: none;
}

.call-window__meeting-overlay {
    position: absolute;
    inset: 20px;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    pointer-events: none;
    z-index: 2;
}

.call-window__meeting-overlay-card {
    margin-top: 16px;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.78);
    color: #fff;
    font-size: 13px;
    line-height: 1.3;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
}

.call-window__actions--single {
    display: block;
}

.call-window__action-slot {
    flex: 1 1 0;
}

.call-window__actions--incoming .call-window__action-slot {
    display: flex;
    justify-content: center;
    flex: 0 0 auto;
}

.call-window__actions--incoming {
    gap: 30px;
    justify-content: center;
}

.call-window__actions--incoming .call-window__action-slot .ant-btn {
    width: 52px;
    min-width: 52px;
    height: 52px;
}

.call-window__actions--double .call-window__action-slot {
    width: 50%;
}

.call-window__actions--triple {
    justify-content: center;
}

.call-window__actions--triple .call-window__action-slot {
    display: flex;
    justify-content: center;
    flex: 0 0 auto;
}

.call-window__actions--triple .call-window__action-slot .ant-btn {
    width: 52px;
    min-width: 52px;
    height: 52px;
}

.call-window__actions--single .call-window__action-slot {
    width: 100%;
}

.call-window__transfer {
    min-height: 300px;
}

.call-window__transfer-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
}

.call-window__transfer-title {
    font-size: 16px;
    font-weight: 700;
    line-height: 1.2;
    color: #111827;
}

.call-window__transfer-state {
    display: flex;
    justify-content: center;
    padding: 32px 0;
}

.call-window__transfer-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 360px;
    overflow-y: auto;
}

.call-window__transfer-user {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    background: #fff;
    text-align: left;
    transition: border-color .2s ease, background .2s ease, box-shadow .2s ease;
}

.call-window__transfer-user:hover:not(:disabled) {
    border-color: #c7d2fe;
    background: #f8faff;
    box-shadow: 0 10px 20px rgba(59, 130, 246, 0.08);
}

.call-window__transfer-user:disabled {
    cursor: default;
    opacity: 0.72;
}

.call-window__transfer-user-main {
    flex: 1 1 auto;
    min-width: 0;
}

.call-window__transfer-user-name {
    font-size: 13px;
    font-weight: 600;
    line-height: 1.35;
    color: #111827;
    word-break: break-word;
}

.call-window__transfer-user-subtitle {
    margin-top: 2px;
    font-size: 12px;
    line-height: 1.3;
    color: #6b7280;
}

@media (max-width: 640px) {
    .meeting-call-layer {
        z-index: 2147483646;
    }

    .call-window {
        inset: 0;
        width: 100vw;
        height: 100dvh;
        border-radius: 0;
        box-shadow: none;
    }

    .call-window--meeting {
        width: 100vw;
    }

    .call-window__header {
        padding: 16px;
        cursor: default;
    }

    .call-window__drag-handle {
        display: none;
    }

    .call-window__header-title {
        font-size: 18px;
    }

    .call-window__header-status {
        font-size: 14px;
    }

    .call-window__body {
        display: flex;
        flex-direction: column;
        min-height: calc(100dvh - 72px);
        padding: 28px 20px 20px;
    }

    .call-window__body--meeting {
        height: calc(100dvh - 72px);
    }

    .call-window__iframe {
        min-height: calc(100dvh - 72px);
    }

    .call-window__user {
        flex: 1 1 auto;
        justify-content: center;
    }

    .call-window__user :deep(.ant-avatar) {
        width: 88px !important;
        height: 88px !important;
        line-height: 88px !important;
        font-size: 30px !important;
    }

    .call-window__name {
        margin-top: 16px;
        font-size: 30px;
        line-height: 1.15;
    }

    .call-window__subtitle,
    .call-window__body-status,
    .call-window__ended-duration-label {
        font-size: 16px;
    }

    .call-window__ended-duration-value {
        font-size: 22px;
    }

    .call-window__recording-badge {
        margin-bottom: 14px;
        padding: 6px 12px;
        font-size: 13px;
    }

    .call-window__body-status {
        margin-top: 10px;
    }

    .call-window__footer {
        margin-top: auto;
        padding-top: 24px;
        padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 4px);
    }

    .call-window__actions {
        margin-top: 0;
    }

    .call-window__actions--incoming {
        gap: 40px;
    }

    .call-window__actions--incoming .call-window__action-slot .ant-btn {
        width: 64px;
        min-width: 64px;
        height: 64px;
    }

    .call-window__actions--triple .call-window__action-slot .ant-btn {
        width: 64px;
        min-width: 64px;
        height: 64px;
    }

    .call-window__action-slot :deep(.ant-btn) {
        min-height: 52px;
    }

    .call-window__chat-btn {
        margin-top: 16px;
    }

    .call-window__ticket-link {
        margin-top: 0;
        margin-bottom: 16px;
        font-size: 16px;
    }

    .call-window__transfer {
        min-height: 0;
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
    }

    .call-window__transfer-head {
        margin-bottom: 20px;
    }

    .call-window__transfer-title {
        font-size: 18px;
    }

    .call-window__transfer-list {
        flex: 1 1 auto;
        max-height: none;
    }

    .call-window__transfer-user {
        padding: 10px 12px;
    }
}
</style>
