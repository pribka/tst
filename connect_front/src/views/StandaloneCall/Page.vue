<template>
    <div class="sc-page">
        <div
            v-for="item in calls"
            :key="item.id"
            class="sc-window">
            <div
                class="sc-header"
                :class="{ 'sc-header--active': item.statusCode === 'in_call' }">
                <div class="sc-drag-handle"></div>
                <div class="sc-header-icon">
                    <i :class="item.type === 'incoming' ? 'fi fi-rr-call-incoming' : 'fi fi-rr-call-outgoing'" />
                </div>
                <div>
                    <div class="sc-header-title">
                        {{ item.type === 'incoming' ? 'Входящий звонок' : 'Исходящий звонок' }}
                    </div>
                    <div class="sc-header-status">{{ getStatusText(item) }}</div>
                </div>
            </div>

            <div class="sc-body">
                <div class="sc-user">
                    <a-avatar
                        :size="72"
                        :src="item.displayUser && item.displayUser.avatarUrl"
                        icon="user">
                        {{ getInitials(item.displayUser) }}
                    </a-avatar>
                    <div class="sc-name">{{ item.displayUser ? item.displayUser.full_name : '—' }}</div>
                    <div v-if="item.statusCode === 'in_call' && item.startedAt" class="sc-subtitle">
                        {{ formatDuration(item.startedAt) }}
                    </div>
                </div>

                <div class="sc-footer">
                    <!-- in_call buttons -->
                    <template v-if="item.statusCode === 'in_call'">
                        <div class="sc-actions sc-actions--in-call">
                            <div class="sc-action-slot">
                                <a-button
                                    :type="item.meetingSelfMuted ? 'ui_ghost' : 'flat_primary'"
                                    size="large"
                                    shape="circle"
                                    :icon="item.meetingSelfMuted ? 'fi-rr-volume-mute' : 'fi-rr-microphone'"
                                    flaticon
                                    class="sc-icon-btn"
                                    @click="sendAction('mute', item.id)" />
                            </div>
                            <div class="sc-action-slot">
                                <a-button
                                    type="flat_danger"
                                    size="large"
                                    shape="circle"
                                    icon="fi-rr-phone-slash"
                                    flaticon
                                    :loading="item.actionLoading === 'end'"
                                    class="sc-icon-btn"
                                    @click="sendAction('end', item.id)" />
                            </div>
                        </div>
                        <div v-if="item.canTransfer" class="sc-transfer-row">
                            <a-button
                                size="large"
                                shape="round"
                                block
                                @click="sendAction('transfer', item.id)">
                                Передать звонок
                            </a-button>
                        </div>
                    </template>

                    <!-- incoming ringing buttons -->
                    <template v-else-if="item.type === 'incoming'">
                        <div class="sc-actions sc-actions--incoming">
                            <div class="sc-action-slot">
                                <a-button
                                    type="flat_danger"
                                    size="large"
                                    shape="circle"
                                    icon="fi-rr-phone-slash"
                                    flaticon
                                    :loading="item.actionLoading === 'reject'"
                                    class="sc-icon-btn"
                                    @click="sendAction('reject', item.id)" />
                            </div>
                            <div class="sc-action-slot">
                                <a-button
                                    type="green"
                                    size="large"
                                    shape="circle"
                                    icon="fi-rr-phone-call"
                                    flaticon
                                    :loading="item.actionLoading === 'accept'"
                                    class="sc-icon-btn"
                                    @click="sendAction('accept', item.id)" />
                            </div>
                        </div>
                    </template>

                    <!-- outgoing ringing button -->
                    <template v-else>
                        <div class="sc-actions sc-actions--single">
                            <div class="sc-action-slot">
                                <a-button
                                    type="flat_danger"
                                    size="large"
                                    block
                                    :loading="item.actionLoading === 'cancel'"
                                    @click="sendAction('cancel', item.id)">
                                    Отменить
                                </a-button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>

        <div v-if="!calls.length" class="sc-empty">
            Нет активных звонков
        </div>
    </div>
</template>

<script>
import CallPopupChannel from '@/utils/callPopupChannel'

export default {
    name: 'StandaloneCallPage',
    data() {
        return {
            calls: [],
            now: Date.now(),
            durationTimer: null,
            unsubscribe: null
        }
    },
    mounted() {
        document.title = 'Звонок'

        CallPopupChannel.init()

        // Load initial state written by the main tab before opening the popup
        const saved = CallPopupChannel.readState()
        if (saved?.calls) {
            this.calls = saved.calls
        }

        // Listen for state updates from the main tab
        this.unsubscribe = CallPopupChannel.onMessage(this.handleMessage)

        // Tell the main tab we are ready so it re-sends current state
        CallPopupChannel.post({ type: 'CALL_POPUP_READY' })

        // Duration counter
        this.durationTimer = setInterval(() => {
            this.now = Date.now()
        }, 1000)
    },
    beforeDestroy() {
        if (typeof this.unsubscribe === 'function') this.unsubscribe()
        CallPopupChannel.destroy()
        if (this.durationTimer) clearInterval(this.durationTimer)
    },
    methods: {
        handleMessage(data) {
            if (!data || !data.type) return

            if (data.type === 'CALL_STATE') {
                this.calls = Array.isArray(data.calls) ? data.calls : []
                return
            }

            if (data.type === 'CALL_CLOSE_POPUP') {
                window.close()
            }
        },

        sendAction(action, callId) {
            CallPopupChannel.post({ type: 'CALL_ACTION', action, callId })
        },

        getInitials(user) {
            const name = user?.full_name || ''
            return name
                .split(' ')
                .filter(Boolean)
                .slice(0, 2)
                .map(p => p.charAt(0).toUpperCase())
                .join('') || '?'
        },

        getStatusText(item) {
            const labels = {
                ringing: 'В звонке',
                in_call: 'В звонке'
            }
            return labels[item.statusCode] || ''
        },

        formatDuration(startedAt) {
            if (!startedAt) return '00:00:00'
            const startMs = new Date(startedAt).getTime()
            if (!startMs) return '00:00:00'
            const total = Math.max(0, Math.floor((this.now - startMs) / 1000))
            const h = String(Math.floor(total / 3600)).padStart(2, '0')
            const m = String(Math.floor((total % 3600) / 60)).padStart(2, '0')
            const s = String(total % 60).padStart(2, '0')
            return `${h}:${m}:${s}`
        }
    }
}
</script>

<style lang="scss">
* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    background: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.sc-page {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

/* Multiple calls — small gap between cards */
.sc-page .sc-window + .sc-window {
    border-top: 1px solid #f0f2f5;
}

.sc-window {
    width: 100%;
    background: #fff;
    overflow: hidden;
    user-select: none;
    flex: 1 0 auto;
}

/* ---- Header ---- */
.sc-header {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 16px 14px;
    color: #fff;
    background: linear-gradient(135deg, #2b59ff 0%, #3554d1 100%);
    transition: background .28s ease;
}

.sc-header--active {
    background: linear-gradient(135deg, #00c94d 0%, #00a63f 100%);
}

.sc-drag-handle {
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 28px;
    height: 3px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.55);
}

.sc-header-icon {
    width: 40px;
    height: 40px;
    flex: 0 0 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.sc-header-title {
    font-size: 15px;
    font-weight: 700;
    line-height: 1.3;
}

.sc-header-status {
    font-size: 13px;
    opacity: 0.85;
    margin-top: 1px;
}

/* ---- Body ---- */
.sc-body {
    padding: 24px 16px 20px;
}

.sc-user {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
}

.sc-name {
    font-size: 18px;
    font-weight: 700;
    color: #1a1a2e;
    text-align: center;
}

.sc-subtitle {
    font-size: 14px;
    color: #6b7280;
    text-align: center;
    letter-spacing: 0.5px;
}

/* ---- Actions ---- */
.sc-footer {}

.sc-actions {
    display: grid;
    gap: 12px;
    margin-bottom: 10px;
}

.sc-actions--incoming {
    grid-template-columns: 1fr 1fr;
    justify-items: center;
}

.sc-actions--in-call {
    grid-template-columns: 1fr 1fr;
    justify-items: center;
}

.sc-actions--single {
    grid-template-columns: 1fr;
}

.sc-action-slot {
    display: flex;
    justify-content: center;
    width: 100%;
}

.sc-icon-btn {
    font-size: 18px;
    display: flex !important;
    align-items: center;
    justify-content: center;
}

.sc-transfer-row {
    margin-top: 8px;
}

/* ---- Empty state ---- */
.sc-empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-size: 14px;
    padding: 40px 16px;
}
</style>
