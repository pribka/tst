<template>
    <div v-if="!chatLoading" class="chat_footer">
        <div class="message_input_wrapper w-full">
            <div
                class="quick_actions_wrap"
                @mouseenter="onQuickActionsEnter"
                @mouseleave="onQuickActionsLeave">
                <a-button
                    v-if="showLeftArrow"
                    class="scroll_arrow left"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-left"
                    @mouseenter="startHoverScroll('left')"
                    @mouseleave="stopHoverScroll" />
                <a-button
                    v-if="showRightArrow"
                    class="scroll_arrow right"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-right"
                    @mouseenter="startHoverScroll('right')"
                    @mouseleave="stopHoverScroll" />
                <div
                    ref="quickActionsScroll"
                    class="quick_actions_scroll"
                    @scroll="onQuickActionsScroll">
                    <div class="quick_actions_list">
                        <a-button
                            v-for="(action, index) in quickActions"
                            :key="action.text"
                            :ref="'quickActionBtn_' + action.text"
                            type="flat_primary"
                            shape="round"
                            size="small"
                            class="quick_action_btn"
                            :class="{ 'quick_action_btn--animated': quickActionsAnimationActive }"
                            :style="{ '--quick-action-delay': `${index * 70}ms` }"
                            @click="applyQuickAction(action)">
                            {{ action.text }}
                        </a-button>
                    </div>
                </div>
            </div>
            <div class="message_row">
                <div class="message_input_box relative">
                    <template v-if="recording">
                        <div class="voice-visualizer">
                            <span v-for="n in 5" :key="n" class="bar"></span>
                            <span class="ml-2">{{ $t('ai_assistant.recording_hint') }}</span>
                        </div>
                    </template>
                    <template v-else>
                        <a-textarea
                            class="message_input"
                            :auto-size="{ minRows: 1, maxRows: 6 }"
                            v-model="message.text"
                            ref="messageInput"
                            size="large"
                            :placeholder="currentPlaceholder"
                            @keydown.enter.exact.prevent
                            @keyup.enter.exact="sendMessage" />
                    </template>
                    <div class="input_actions">
                        <a-button 
                            v-if="recording"
                            type="ui"
                            shape="circle"
                            flaticon
                            class="stop_record"
                            ghost
                            icon="fi-rr-pause"
                            @click="stopRecording" />
                        <a-button
                            v-else-if="isSupported && !blocked"
                            type="ui"
                            shape="circle"
                            ghost
                            flaticon
                            icon="n-icon-circle-microphone"
                            @click="startRecording" />
                    </div>
                </div>
                <a-button 
                    type="primary"
                    flaticon
                    class="ml-2 send_btn"
                    :loading="loading"
                    size="large"
                    icon="fi-rr-paper-plane-top"
                    @click="sendMessage()" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        addNewMessage: { type: Function, default: () => {} },
        visible: { type: Boolean, default: false },
        scrollToBottom: { type: Function, default: () => {} }
    },
    data() {
        return {
            loading: false,
            message: { text: '' },
            recording: false,
            recognition: null,
            isSupported: false,
            blocked: false,
            supportHint: '',
            baseTextBeforeDictation: '',
            resizeObserver: null,
            mutationObserver: null,
            observedTargets: [],
            rafScheduled: false,
            autoRestart: false,
            isSafari: false,
            lastResultAt: 0,
            restartTimer: null,
            quickActionsHover: false,
            canScrollLeft: false,
            canScrollRight: false,
            hoverScrollTimer: null,
            hoverScrollDir: null,
            quickActionsAnimationActive: false,
            quickActionsAnimationFrame: null,
            placeholderRotationTimer: null,
            placeholderIndex: 0,
            placeholderInitialized: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        quickActions() {
            return [
                {
                    text: this.$t('ai_assistant.quick_action_create_task'),
                    value: this.$t('ai_assistant.quick_action_create_task_value')
                },
                {
                    text: this.$t('ai_assistant.quick_action_tasks_report'),
                    value: this.$t('ai_assistant.quick_action_tasks_report_value')
                },
                {
                    text: this.$t('ai_assistant.quick_action_tickets_report'),
                    value: this.$t('ai_assistant.quick_action_tickets_report_value')
                },
                {
                    text: this.$t('ai_assistant.quick_action_worklog_report'),
                    value: this.$t('ai_assistant.quick_action_worklog_report_value')
                },
                {
                    text: this.$t('ai_assistant.quick_action_create_event'),
                    value: this.$t('ai_assistant.quick_action_create_event_value')
                },
                {
                    text: this.$t('ai_assistant.quick_action_create_meeting'),
                    value: this.$t('ai_assistant.quick_action_create_meeting_value')
                }
            ]
        },
        placeholderOptions() {
            return [
                this.$t('ai_assistant.message_placeholder_example_event_friday'),
                this.$t('ai_assistant.message_placeholder_example_task_ruslan'),
                this.$t('ai_assistant.message_placeholder_example_meeting_11'),
                this.$t('ai_assistant.message_placeholder_example_tasks_report'),
                this.$t('ai_assistant.message_placeholder_example_tickets_report'),
                this.$t('ai_assistant.message_placeholder_example_worklog_report')
            ]
        },
        currentPlaceholder() {
            return this.placeholderOptions[this.placeholderIndex] || this.$t('ai_assistant.message_placeholder')
        },
        chatLoading() {
            return this.$store.state.ai.chatLoading
        },
        showLeftArrow() {
            return !this.isMobile && this.quickActionsHover && this.canScrollLeft
        },
        showRightArrow() {
            return !this.isMobile && this.quickActionsHover && this.canScrollRight
        }
    },
    watch: {
        visible(val) {
            if (val) {
                this.inputFocus()
                this.triggerQuickActionsAnimation()
                this.syncPlaceholderRotation()
                this.$nextTick(() => this.attachObserversSafely())
                this.$nextTick(() => this.updateQuickActionArrows())
            } else {
                this.resetQuickActionsAnimation()
                this.stopPlaceholderRotation()
            }
        },
        chatLoading(val) {
            if (!val) {
                if (this.visible) this.triggerQuickActionsAnimation()
                if (this.visible) this.syncPlaceholderRotation()
                this.$nextTick(() => this.attachObserversSafely())
                this.$nextTick(() => this.updateQuickActionArrows())
            } else {
                this.stopPlaceholderRotation()
                this.detachObservers()
            }
        },
        'message.text'(val) {
            if (val && val.trim()) {
                this.stopPlaceholderRotation()
                return
            }

            this.syncPlaceholderRotation()
        },
        isMobile() {
            this.$nextTick(() => this.updateQuickActionArrows())
        }
    },
    mounted() {
        this.inputFocus()
        if (this.visible && !this.chatLoading) this.triggerQuickActionsAnimation()
        this.syncPlaceholderRotation()
        this.$nextTick(() => this.attachObserversSafely())
        this.$nextTick(() => this.updateQuickActionArrows())
        window.addEventListener('resize', this.updateQuickActionArrows)
        const hasRecognition = !!(window.SpeechRecognition || window.webkitSpeechRecognition)
        const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
        const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1'
        this.isSupported = hasRecognition && hasMedia && isSecure
        if (!this.isSupported) return
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        const sr = new SR()
        const ua = navigator.userAgent.toLowerCase()
        this.isSafari = ua.includes('safari') && !ua.includes('chrome') && !ua.includes('edg')
        sr.lang = 'ru-RU'
        sr.continuous = !this.isSafari
        sr.interimResults = true
        sr.onresult = e => {
            let finalText = ''
            let interimText = ''
            for (let i = e.resultIndex; i < e.results.length; i++) {
                const res = e.results[i]
                if (res.isFinal) finalText += res[0].transcript + ' '
                else interimText += res[0].transcript
            }
            const prefix = this.baseTextBeforeDictation ? this.baseTextBeforeDictation + (this.baseTextBeforeDictation.endsWith(' ') ? '' : ' ') : ''
            this.message.text = (prefix + finalText + interimText).trim()
            this.lastResultAt = Date.now()
        }
        sr.onerror = e => {
            this.recording = false
            const code = e && e.error ? e.error : 'unknown'
            if (code === 'aborted') return
            if (code === 'not-allowed' || code === 'service-not-allowed' || code === 'audio-capture') {
                this.blocked = true
                this.autoRestart = false
                if (code === 'audio-capture') this.$message && this.$message.error(this.$t('ai_assistant.microphone_not_found'))
                else this.$message && this.$message.error(this.$t('ai_assistant.microphone_access_denied'))
                return
            }
            if ((code === 'no-speech' || code === 'network' || code === 'bad-grammar' || code === 'language-not-supported') && this.autoRestart) {
                clearTimeout(this.restartTimer)
                this.restartTimer = setTimeout(() => {
                    try { this.recognition && this.recognition.start() } catch {}
                }, 200)
                return
            }
            this.$message && this.$message.error(this.$t('ai_assistant.speech_recognition_error', { code }))
        }
        sr.onend = () => {
            if (this.autoRestart && !this.blocked) {
                clearTimeout(this.restartTimer)
                this.restartTimer = setTimeout(() => {
                    try { this.recognition && this.recognition.start() } catch {}
                }, 150)
            } else {
                this.recording = false
            }
        }
        this.recognition = sr
        setInterval(() => {
            if (this.recording && this.autoRestart && !this.blocked) {
                const idle = Date.now() - this.lastResultAt
                if (idle > 10000) {
                    try { this.recognition.stop() } catch {}
                }
            }
        }, 3000)
    },
    methods: {
        resetQuickActionsAnimation() {
            this.quickActionsAnimationActive = false
            if (this.quickActionsAnimationFrame) {
                cancelAnimationFrame(this.quickActionsAnimationFrame)
                this.quickActionsAnimationFrame = null
            }
        },
        initPlaceholderIndex() {
            if (this.placeholderInitialized || !this.placeholderOptions.length) return
            this.placeholderIndex = Math.floor(Math.random() * this.placeholderOptions.length)
            this.placeholderInitialized = true
        },
        stopPlaceholderRotation() {
            if (this.placeholderRotationTimer) {
                clearInterval(this.placeholderRotationTimer)
                this.placeholderRotationTimer = null
            }
        },
        startPlaceholderRotation() {
            if (this.placeholderRotationTimer || !this.placeholderOptions.length) return
            this.placeholderRotationTimer = setInterval(() => {
                this.placeholderIndex = (this.placeholderIndex + 1) % this.placeholderOptions.length
            }, 5000)
        },
        syncPlaceholderRotation() {
            const hasText = this.message.text && this.message.text.trim()
            if (!this.visible || this.chatLoading || hasText) {
                this.stopPlaceholderRotation()
                return
            }

            this.initPlaceholderIndex()
            this.startPlaceholderRotation()
        },
        triggerQuickActionsAnimation() {
            this.resetQuickActionsAnimation()
            this.quickActionsAnimationFrame = requestAnimationFrame(() => {
                this.quickActionsAnimationActive = true
                this.quickActionsAnimationFrame = null
            })
        },
        onQuickActionsEnter() {
            this.quickActionsHover = true
            this.$nextTick(() => this.updateQuickActionArrows())
        },
        onQuickActionsLeave() {
            this.quickActionsHover = false
            this.stopHoverScroll()
        },
        onQuickActionsScroll() {
            this.updateQuickActionArrows()
        },
        getQuickActionsScrollEl() {
            return this.$refs.quickActionsScroll
        },
        updateQuickActionArrows() {
            const el = this.getQuickActionsScrollEl()
            if (!el || this.isMobile) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollLeft = left > eps
            this.canScrollRight = left < max - eps
        },
        startHoverScroll(dir) {
            if (this.isMobile || !this.quickActionsHover) return

            const el = this.getQuickActionsScrollEl()
            if (!el) return

            this.stopHoverScroll()
            this.hoverScrollDir = dir

            const step = 8
            const tick = 16

            this.hoverScrollTimer = setInterval(() => {
                if (!this.quickActionsHover) {
                    this.stopHoverScroll()
                    return
                }

                const max = el.scrollWidth - el.clientWidth
                if (max <= 0) {
                    this.updateQuickActionArrows()
                    this.stopHoverScroll()
                    return
                }

                let next = el.scrollLeft
                if (this.hoverScrollDir === 'left') next -= step
                if (this.hoverScrollDir === 'right') next += step

                if (next < 0) next = 0
                if (next > max) next = max

                el.scrollLeft = next
                this.updateQuickActionArrows()

                if (next === 0 || next === max) this.stopHoverScroll()
            }, tick)
        },
        stopHoverScroll() {
            if (this.hoverScrollTimer) {
                clearInterval(this.hoverScrollTimer)
                this.hoverScrollTimer = null
            }
            this.hoverScrollDir = null
        },
        applyQuickAction(action) {
            this.message.text = action.value
            this.inputFocus()
            this.$nextTick(() => this.centerQuickAction(action.text))
        },
        centerQuickAction(actionText) {
            const container = this.getQuickActionsScrollEl()
            const refEl = this.$refs['quickActionBtn_' + actionText]
            const button = Array.isArray(refEl) ? refEl[0] : refEl
            const el = button ? (button.$el || button) : null

            if (!container || !el) return

            const targetLeft = el.offsetLeft - (container.clientWidth - el.offsetWidth) / 2
            const max = container.scrollWidth - container.clientWidth
            const nextLeft = Math.max(0, Math.min(targetLeft, max))

            if (typeof container.scrollTo === 'function') {
                container.scrollTo({ left: nextLeft, behavior: 'smooth' })
            } else {
                container.scrollLeft = nextLeft
            }

            this.$nextTick(() => this.updateQuickActionArrows())
        },
        clearText() {
            this.clearInput()
            this.inputFocus()
        },
        inputFocus() {
            this.$nextTick(() => {
                const comp = this.$refs.messageInput
                if (comp && typeof comp.focus === 'function') comp.focus()
            })
        },
        async ensureMicPermission() {
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true })
                return true
            } catch (e) {
                this.blocked = true
                this.$message && this.$message.error(this.$t('ai_assistant.microphone_access_denied'))
                return false
            }
        },
        async startRecording() {
            if (!this.recognition || this.recording) return
            const ok = await this.ensureMicPermission()
            if (!ok) return
            this.baseTextBeforeDictation = this.message.text || ''
            this.autoRestart = true
            this.recording = true
            this.lastResultAt = Date.now()
            clearTimeout(this.restartTimer)
            try {
                this.recognition.start()
            } catch (e) {
                this.recording = false
                this.autoRestart = false
                this.$message && this.$message.error(this.$t('ai_assistant.speech_start_failed'))
            }
        },
        stopRecording() {
            if (!this.recognition) return
            this.autoRestart = false
            clearTimeout(this.restartTimer)
            try {
                this.recognition.stop()
                setTimeout(() => {
                    this.inputFocus()
                }, 200)
            } catch (e) {}
            this.recording = false
        },
        actionHandler(injectMessage) {
            this.sendMessage({ injectMessage })
        },
        clearInput() {
            this.message = { text: '' }
        },
        async sendMessage({ injectMessage = '' } = {}) {
            try {
                if (!this.loading) {
                    const text = (injectMessage.length ? injectMessage : this.message.text || '').trim()
                    if (!text)
                        return

                    this.inputFocus()
                    this.$store.commit('ai/CHANGE_MESSAGES_FILED', { field: 'aiLoading', value: true })
                    this.loading = true
                    const data = await this.$store.dispatch('ai/sendMessage', { 
                        text,
                        addNewMessage: this.addNewMessage,
                        clearInput: this.clearInput
                    })
                    if (data?.assistant_message) {
                        this.inputFocus()
                        this.addNewMessage(data.assistant_message)
                    }
                }
            } catch (error) {
                console.log(error)
            } finally {
                this.loading = false
                this.$store.commit('ai/CHANGE_MESSAGES_FILED', { field: 'aiLoading', value: false })
            }
        },
        getTextareaTargets() {
            const comp = this.$refs.messageInput
            if (!comp) return []
            const root = comp.$el || comp
            if (!root) return []
            const ta = root.querySelector('textarea')
            const wrapper = root.querySelector('.ant-input-textarea, .ant-input-affix-wrapper-textarea-with-clear-btn') || root
            const targets = []
            if (ta) targets.push(ta)
            if (wrapper && wrapper !== ta) targets.push(wrapper)
            return targets
        },
        attachObserversSafely() {
            const tryAttach = () => {
                const ok = this.attachObservers()
                if (!ok) {
                    this.$nextTick(() => {
                        const ok2 = this.attachObservers()
                        if (!ok2) {
                            setTimeout(() => this.attachObservers(), 50)
                        }
                    })
                }
            }
            tryAttach()
        },
        attachObservers() {
            const targets = this.getTextareaTargets()
            if (!targets.length) return false
            this.detachObservers()
            this.observedTargets = targets
            return true
        },
        detachObservers() {
            if (this.resizeObserver) {
                try { this.resizeObserver.disconnect() } catch {}
                this.resizeObserver = null
            }
            if (this.mutationObserver) {
                try { this.mutationObserver.disconnect() } catch {}
                this.mutationObserver = null
            }
            this.observedTargets = []
        }
    },
    beforeDestroy() {
        this.resetQuickActionsAnimation()
        this.stopPlaceholderRotation()
        this.stopHoverScroll()
        window.removeEventListener('resize', this.updateQuickActionArrows)
        this.detachObservers()
    }
}
</script>

<style lang="scss" scoped>
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}
.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.input_actions {
  position: absolute;
  top: 2px;
  right: 5px;
  display: flex;
  align-items: center;
  z-index: 10;
  &::v-deep{
    .ant-btn-ui{
      &.stop_record{
        color: #FF5C5C!important;
      }
    }
    .ant-btn-ui{
      &.ant-btn-background-ghost{
        background: transparent!important;
        border-color: transparent!important;
      }
    }
  }
}
.send_btn.ant-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}
.send_btn.ant-btn.ant-btn-lg {
  height: 40px;
}
.chat_footer {
  padding: 5px 20px 20px 20px;
  display: block;
}
.message_input_wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.message_row {
  display: flex;
  align-items: flex-end;
}
.message_input_box {
  position: relative;
  flex: 1;
  min-width: 0;
}
.quick_actions_wrap {
  position: relative;
}
.quick_actions_scroll {
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
  &::-webkit-scrollbar {
    display: none;
  }
}
.quick_actions_list {
  display: flex;
  width: max-content;
  min-width: 100%;
  gap: 5px;
  padding: 0 1px;
}
.quick_action_btn.ant-btn {
  flex-shrink: 0;
  opacity: 1;
  transform: translateX(0);
  will-change: opacity, transform;
}
.quick_action_btn--animated.ant-btn {
  animation: quickActionReveal .45s cubic-bezier(.22, 1, .36, 1) both;
  animation-delay: var(--quick-action-delay, 0ms);
}
.scroll_arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  &.left {
    left: -10px;
  }
  &.right {
    right: -10px;
  }
}
.chat_footer .message_input {
  min-height: 40px !important;
  resize: none;
  border-color: #fff;
  padding-right: 50px;
}
.chat_footer .message_input:focus {
  box-shadow: initial;
}
.voice-visualizer {
  display: flex;
  align-items: center;
  height: 40px;
  padding: 0 12px;
  background: #fff;
  border-radius: 6px;
}
.voice-visualizer .bar {
  width: 4px;
  height: 16px;
  margin: 0 2px;
  background: #1890ff;
  animation: bounce 1s infinite ease-in-out;
}
.voice-visualizer .bar:nth-child(2) { animation-delay: .1s; }
.voice-visualizer .bar:nth-child(3) { animation-delay: .2s; }
.voice-visualizer .bar:nth-child(4) { animation-delay: .3s; }
.voice-visualizer .bar:nth-child(5) { animation-delay: .4s; }
@keyframes bounce {
  0%, 100% { transform: scaleY(.3); }
  50% { transform: scaleY(1); }
}
@keyframes quickActionReveal {
  from {
    opacity: 0;
    transform: translateX(28px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@media (max-width: 768px) {
  .message_input_wrapper {
    gap: 8px;
  }
  .quick_actions_wrap {
    margin-right: 0;
  }
}
</style>
