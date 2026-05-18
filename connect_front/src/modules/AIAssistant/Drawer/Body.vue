<template>
    <div class="flex-grow chat_body" ref="scroller">
        <template v-if="activeMessages">
            <div v-if="loading && !activeMessages.empty" class="spinner_overlay">
                <div class="spinner_overlay__badge">
                    <a-spin size="small" />
                </div>
            </div>

            <div
                v-for="(message, index) in activeMessages.results"
                :key="message.id"
                class="chat_message_row"
                :ref="'msg-'+message.id">
                <Message :messageIndex="index" :message="message" />
            </div>

            <div v-if="activeMessages.aiLoading" class="flex items-center">
                <video
                    v-if="pendingAnimationSrc"
                    class="ai_loading__anim mr-2"
                    :src="pendingAnimationSrc"
                    autoplay
                    loop
                    muted
                    playsinline />
                {{ $t('ai_assistant.thinking') }}
            </div>

            <div v-if="activeMessages.empty" class="empty_message">
                <div class="empty_message__wrapper">
                    <div class="empty_message__media">
                        <video
                            v-if="helloBotAnimationWebmSrc || helloBotAnimationMovSrc"
                            class="empty_message__anim"
                            autoplay
                            loop
                            muted
                            playsinline>
                            <source v-if="helloBotAnimationWebmSrc" :src="helloBotAnimationWebmSrc" type="video/webm">
                            <source v-if="helloBotAnimationMovSrc" :src="helloBotAnimationMovSrc" type="video/quicktime">
                        </video>
                    </div>
                    <div class="empty_message__text">
                        <p>{{ $t('ai_assistant.intro_line_1') }}</p>
                        <!--<p>{{ $t('ai_assistant.intro_line_2') }}</p>-->
                        <p>{{ $t('ai_assistant.intro_line_3') }}</p>
                    </div>
                    <div class="actions_list empty_message__actions">
                        <a-button type="flat_primary" class="mb-1" block @click="actionHandler($t('ai_assistant.example_action_event_tomorrow'))">{{ $t('ai_assistant.example_action_event_tomorrow') }}</a-button>
                        <a-button type="flat_primary" block @click="actionHandler($t('ai_assistant.example_action_meeting'))">{{ $t('ai_assistant.example_action_meeting') }}</a-button>
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import { useInfiniteScroll, useScroll } from '@vueuse/core'
import { mapState } from 'vuex'

export default {
    components: { 
        Message: () => import('./Message/index.vue')
    },
    props: {
        actionHandler: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            activeChat: state => state.ai.activeChat,
            chatLoading: state => state.ai.chatLoading,
            chatMessages: state => state.ai.chatMessages
        }),
        activeMessages() {
            if (this.activeChat && this.chatMessages?.[this.activeChat.id]) {
                return this.chatMessages[this.activeChat.id]
            }
            return null
        }
    },
    data() {
        return {
            loading: false,
            newMessageCount: 0,
            showScrollButton: false,
            scroller: null,
            pendingAnimationSrc: '',
            helloBotAnimationWebmSrc: '',
            helloBotAnimationMovSrc: '',
            initialScrollDone: false,
            stopWatch: null,
            stopInfinite: null,
            roScroller: null,
            roLastItem: null,
            stabilizerTimer: 0,
            bottomLock: false,
            lockRO: null,
            lockMO: null,
            lockRAF: 0,
            lockStableTimer: 0,
            lockMaxTimer: 0,
            lastHeight: 0,
            lastChangeTs: 0
        }
    },
    mounted() {
        this.scroller = this.$refs.scroller

        if (this.activeChat?.id) {
            this.$store.commit('ai/RESET_CHAT_MESSAGES', this.activeChat.id)
        }

        const { y } = useScroll(this.scroller)
        this.stopWatch = this.$watch(() => y.value, () => {
            this.$nextTick(() => {
                const scrollBottom = this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight
                this.showScrollButton = scrollBottom > 150
                if (scrollBottom > 150 && this.bottomLock) this.releaseBottomLock()
                if (scrollBottom < 150 && this.newMessageCount) this.newMessageCount = 0
            })
        })

        this.$watch(
            () => this.activeMessages && this.activeMessages.results ? this.activeMessages.results.length : 0,
            len => {
                if (!this.initialScrollDone && len > 0) {
                    this.scrollToBottomImmediate()
                    this.lockBottomUntilStable({ minMs: 200, settleMs: 250, maxMs: 5000 })
                    this.initialScrollDone = true
                    this.stopInfinite = useInfiniteScroll(
                        this.scroller,
                        () => {
                            if (!this.loading && this.activeMessages && this.activeMessages.next) {
                                return this.fetchMessages(false)
                            }
                        },
                        { distance: 200, direction: 'top' }
                    )
                }
            },
            { immediate: true }
        )

        this.fetchMessages(true)
    },
    created() {
        this.loadPendingAnimation()
        this.loadHelloBotAnimation()
    },
    beforeDestroy() {
        if (typeof this.stopWatch === 'function') this.stopWatch()
        if (typeof this.stopInfinite === 'function') this.stopInfinite()
        this.releaseHeightStabilizer()
        this.releaseBottomLock()
    },
    methods: {
        isNearBottom(threshold = 150) {
            if (!this.scroller) return true
            const scrollBottom = this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight
            return scrollBottom <= threshold
        },
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
        async loadHelloBotAnimation() {
            this.helloBotAnimationMovSrc = `${process.env.BASE_URL}animate/hello_bot.mov`

            try {
                const animationModule = await import('@/assets/animate/hello_bot.webm')
                this.helloBotAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.helloBotAnimationWebmSrc = ''
            }
        },
        async addNewMessage(data) {
            const shouldAutoScroll = this.isNearBottom()
            await this.$nextTick()
            if (data && data.is_bot) {
                if (!shouldAutoScroll)
                    return

                const el = await this.waitForMessageEl(data.id)
                if (el) {
                    this.scrollIntoViewSmart(el, false)
                    this.observeMessageGrowth(el, shouldAutoScroll)
                    return
                }
            }
            this.scrollToBottom(false)
            this.armHeightStabilizer(true)
        },
        async waitForMessageEl(id, tries = 30) {
            const refKey = 'msg-' + id
            for (let i = 0; i < tries; i++) {
                const elRef = this.$refs[refKey]
                const node = Array.isArray(elRef) ? elRef[0] : elRef
                const el = node ? (node instanceof HTMLElement ? node : node.$el) : null
                if (el) return el
                await new Promise(r => requestAnimationFrame(r))
            }
            return null
        },
        observeMessageGrowth(el, shouldAutoScroll = true) {
            if (!shouldAutoScroll) return
            if (!window.ResizeObserver || !el) return
            const ro = new ResizeObserver(() => {
                this.scrollIntoViewSmart(el, false)
            })
            ro.observe(el)
            setTimeout(() => ro.disconnect(), 800)
        },
        scrollIntoViewSmart(node, smooth = false) {
            const el = node instanceof HTMLElement ? node : node.$el
            if (!el || !this.scroller) return
            const viewportH = this.scroller.clientHeight
            const itemH = el.offsetHeight
            const itemTop = el.offsetTop
            let target
            if (itemH >= viewportH * 0.9) {
                target = itemTop - 12
            } else {
                const upperBias = (viewportH - itemH) * 0.3
                target = itemTop - Math.max(12, upperBias)
            }
            const maxTop = this.scroller.scrollHeight - viewportH
            if (target < 0) target = 0
            if (target > maxTop) target = maxTop
            this.scrollTo(target, smooth)
        },
        scrollToBottomImmediate() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (!this.scroller) return
                        this.scroller.scrollTop = this.scroller.scrollHeight
                    })
                })
            })
        },
        scrollToBottom(smooth = false) {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    if (!this.scroller) return
                    const top = this.scroller.scrollHeight
                    this.scrollTo(top, smooth)
                })
            })
        },
        scrollTo(top, smooth = false) {
            if (!this.scroller) return
            if (typeof this.scroller.scrollTo === 'function') {
                this.scroller.scrollTo({ top, behavior: smooth ? 'smooth' : 'auto' })
            } else {
                this.scroller.scrollTop = top
            }
        },
        releaseHeightStabilizer() {
            if (this.roScroller) {
                this.roScroller.disconnect()
                this.roScroller = null
            }
            if (this.roLastItem) {
                this.roLastItem.disconnect()
                this.roLastItem = null
            }
            if (this.stabilizerTimer) {
                clearTimeout(this.stabilizerTimer)
                this.stabilizerTimer = 0
            }
        },
        armHeightStabilizer(isUpdate = false) {
            if (!this.scroller) return
            const last = this.getLastRow()
            this.releaseHeightStabilizer()

            let rafId = 0
            let timerId = 0
            let lastH = -1
            const stab = () => {
                cancelAnimationFrame(rafId)
                clearTimeout(timerId)
                rafId = requestAnimationFrame(() => {
                    const h = this.scroller.scrollHeight
                    if (h !== lastH) {
                        lastH = h
                        timerId = setTimeout(() => {
                            this.scrollToBottomImmediate()
                        }, 60)
                    }
                })
            }

            if (window.ResizeObserver) {
                if (last) {
                    const el = last instanceof HTMLElement ? last : last.$el
                    this.roLastItem = new ResizeObserver(() => stab())
                    this.roLastItem.observe(el)
                }
            } else {
                setTimeout(() => this.scrollToBottomImmediate(), 80)
            }

            if (!isUpdate) {
                requestAnimationFrame(() => requestAnimationFrame(() => this.scrollToBottomImmediate()))
            }

            this.stabilizerTimer = setTimeout(() => {
                this.releaseHeightStabilizer()
            }, 1200)
        },
        getLastRow() {
            if (!this.activeMessages || !this.activeMessages.results || !this.activeMessages.results.length) return null
            const lastMsg = this.activeMessages.results[this.activeMessages.results.length - 1]
            const refKey = 'msg-' + lastMsg.id
            const el = this.$refs[refKey]
            return Array.isArray(el) ? el[0] : el
        },
        async fetchMessages(isFirstLoad = false) {
            if (!this.activeChat?.id) return
            this.loading = true
            const prevScrollTop = this.scroller.scrollTop
            const prevScrollHeight = this.scroller.scrollHeight

            const params = {
                page: this.activeMessages?.page,
                page_size: 15,
                chat: this.activeChat.id
            }
            if (this.activeMessages?.slice_count > 0) params.slice_count = this.activeMessages.slice_count

            try {
                await this.$store.dispatch('ai/getMessage', params)
                this.$nextTick(() => {
                    if (isFirstLoad) {
                        this.scrollToBottomImmediate()
                        this.lockBottomUntilStable({ minMs: 200, settleMs: 250, maxMs: 5000 })
                        return
                    }
                    const newScrollHeight = this.scroller.scrollHeight
                    const heightDiff = newScrollHeight - prevScrollHeight
                    this.scroller.scrollTop = prevScrollTop + heightDiff
                })
            } catch (e) {
                this.$message.error(this.$t('Error'))
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        lockBottomUntilStable({ minMs = 200, settleMs = 250, maxMs = 5000 } = {}) {
            if (!this.scroller) return
            this.releaseBottomLock()
            this.bottomLock = true
            this.lastHeight = this.scroller.scrollHeight
            this.lastChangeTs = Date.now()
            this.scroller.scrollTop = this.scroller.scrollHeight

            if (window.ResizeObserver) {
                this.lockRO = new ResizeObserver(() => {
                    const h = this.scroller.scrollHeight
                    if (h !== this.lastHeight) {
                        this.lastHeight = h
                        this.lastChangeTs = Date.now()
                        this.scroller.scrollTop = this.scroller.scrollHeight
                    }
                })
                this.lockRO.observe(this.scroller)
            }

            this.lockMO = new MutationObserver(() => {
                const h = this.scroller.scrollHeight
                if (h !== this.lastHeight) {
                    this.lastHeight = h
                    this.lastChangeTs = Date.now()
                    this.scroller.scrollTop = this.scroller.scrollHeight
                }
            })
            this.lockMO.observe(this.scroller, { childList: true, subtree: true, attributes: true, characterData: false })

            const tick = () => {
                if (!this.bottomLock) return
                const now = Date.now()
                const sinceChange = now - this.lastChangeTs
                const sinceStart = now - (this.lockStartTs || now)
                if (!this.lockStartTs) this.lockStartTs = now
                if (sinceStart < minMs) {
                    this.scroller.scrollTop = this.scroller.scrollHeight
                    this.lockRAF = requestAnimationFrame(tick)
                    return
                }
                if (sinceChange >= settleMs || sinceStart >= maxMs) {
                    this.releaseBottomLock()
                    return
                }
                this.scroller.scrollTop = this.scroller.scrollHeight
                this.lockRAF = requestAnimationFrame(tick)
            }
            this.lockRAF = requestAnimationFrame(tick)

            this.lockMaxTimer = setTimeout(() => {
                this.releaseBottomLock()
            }, maxMs + 200)
        },
        releaseBottomLock() {
            if (!this.bottomLock) return
            this.bottomLock = false
            this.lockStartTs = null
            if (this.lockRO) {
                this.lockRO.disconnect()
                this.lockRO = null
            }
            if (this.lockMO) {
                this.lockMO.disconnect()
                this.lockMO = null
            }
            if (this.lockRAF) {
                cancelAnimationFrame(this.lockRAF)
                this.lockRAF = 0
            }
            if (this.lockStableTimer) {
                clearTimeout(this.lockStableTimer)
                this.lockStableTimer = 0
            }
            if (this.lockMaxTimer) {
                clearTimeout(this.lockMaxTimer)
                this.lockMaxTimer = 0
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.chat_message_row {
  &:not(:last-child) {
    margin-bottom: 15px;
  }
}
.actions_list {
  max-width: 300px;
  margin: 0 auto;
  padding-top: 15px;
}
.empty_message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
  &__wrapper {
    padding: 12px;
    max-width: 500px;
    text-align: center;
  }
  &__media,
  &__text,
  &__actions {
    opacity: 0;
    animation-duration: .45s;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
    animation-fill-mode: forwards;
  }
  &__media {
    animation-name: empty-message-slide-down;
  }
  &__text {
    animation-name: empty-message-fade-up;
    animation-delay: .16s;
  }
  &__actions {
    animation-name: empty-message-fade-up;
    animation-delay: .3s;
  }
  &__anim {
    display: block;
    width: 120px;
    height: 120px;
    margin: 0 auto 8px;
    object-fit: contain;
  }
}
.chat_body {
  position: relative;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}
.spinner_overlay {
  position: sticky;
  top: 12px;
  height: 0;
  display: flex;
  justify-content: center;
  z-index: 4;
  pointer-events: none;
}
.spinner_overlay__badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 6px 18px rgba(31, 57, 104, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translateY(0);
}
.ai_loading__anim {
  width: 22px;
  height: 22px;
  object-fit: contain;
  flex: 0 0 22px;
}
@keyframes empty-message-slide-down {
  from {
    opacity: 0;
    transform: translateY(-28px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes empty-message-fade-up {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
