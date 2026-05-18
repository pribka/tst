<template>
    <div
        class="chat_widget_root"
        :class="{ mobile_layer: isMobile && showChat }">

        <div class="chat_wrapper h-full flex flex-col" v-show="showChat">
            <ChatHeader
                :infoRouter="infoRouter"
                v-if="ticket"
                :ticket="ticket"
                :showAside="showAside"
                :changeShowAside="changeShowAside"
                :useAside="useAside"
                :showChat="showChat"
                :changeShowChat="changeShowChat" />

            <div class="chat_wrapper__body flex-grow">
                <div class="chat_message_list" ref="scroller">
                    <div class="chat_message_list__scroller">
                        <template v-if="ticket">
                            <div v-if="loading" class="spinner-wrap">
                                <a-spin size="small" />
                            </div>

                            <Message
                                v-for="message in messages.results"
                                :key="message.id"
                                :ticket="ticket"
                                :isActive="edit"
                                :actions="actions"
                                :setReplace="setReplace"
                                :message="message"
                                :onAudioLoaded="onAudioLoaded"
                                :onAudioPlay="onAudioPlay"
                                :onVideoLoaded="onVideoLoaded"
                                :onVideoPlay="onVideoPlay" />
                        </template>

                        <div v-else class="empty_ticket">
                            <div>
                                <i class="fi fi-rr-comment-dots"></i>
                                <div class="empty_ticket__message">{{ $t('helpdesk.select_appeal_to_view') }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <transition v-if="messages.results.length" name="slide-up-fade">
                    <div v-show="showScrollButton" class="scroll_down" @click="scrollToBottom()">
                        <a-badge :count="newMessageCount">
                            <i class="fi fi-rr-arrow-down" />
                        </a-badge>
                    </div>
                </transition>
            </div>

            <template v-if="ticket">
                <Footer
                    v-if="actions && actions.create_message"
                    ref="chatFooter"
                    :ticket="ticket"
                    :actions="actions"
                    :scrollToBottom="scrollToBottom"
                    :replaceMessage="replaceMessage"
                    :setReplace="setReplace"
                    :addNewMessage="addNewMessage" />
            </template>
        </div>

        <!-- collapsed bubble -->
        <a-badge
            v-show="!showChat"
            :count="newMessageCount"
            class="chat_collapse_badge"
            :class="{ 'chat_collapse_badge--attention': bubbleAttention }"
            style="height: 100%; width: 100%;">
            <a-button
                class="chat_collapse_btn"
                :class="{ 'chat_collapse_btn--attention': bubbleAttention }"
                style="font-size: 25px; height: 100%; width: 100%; justify-content: center; align-items: center; display: flex;"
                size="large"
                type="primary"
                flaticon
                shape="circle"
                icon="fi-rr-comment-dots"
                @click="changeShowChat(true)" />
        </a-badge>
    </div>
</template>

<script>
import { useInfiniteScroll, useScroll } from '@vueuse/core'
import { errorHandler } from '@/utils/index.js'
import ChatHeader from './Header.vue'
import Message from './Message.vue'
import Footer from './Footer.vue'

export default {
    name: 'ChatWidget',
    components: { ChatHeader, Message, Footer },

    props: {
        ticket: { type: Object, default: () => null },
        showAside: { type: Boolean, default: false },
        changeShowAside: { type: Function, default: () => {} },
        useAside: { type: Boolean, default: true },
        showChat: { type: Boolean, default: true },
        changeShowChat: { type: Function, default: () => {} },
        edit: { type: Boolean, default: false },
        infoRouter: {
            type: Object,
            required: false
        },
        actions: { type: Object, default: () => null }
    },

    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isClientView() {
            const q = this.$route?.query || {}
            if (q.ticketView) return false
            if (q.requestView) return true
            return false
        },

        // ✅ включаем анимацию, только когда чат свернут и есть непрочитанные
        bubbleAttention() {
            return !this.showChat && Number(this.newMessageCount || 0) > 0
        }
    },

    data() {
        return {
            resizeObs: null,

            stickToBottom: true,
            atBottom: true,

            replaceMessage: null,
            showScrollButton: false,
            scroller: null,

            page: 1,
            slice_count: 0,
            loading: false,

            newMessageCount: 0,
            countPromise: null,
            countQueued: false,

            // ✅ очередь на viewers (батчим)
            pendingReadMap: {},
            readFlushTimer: null,
            markingRead: false,

            initialScrollDone: false,
            stopWatch: null,

            messages: {
                count: 0,
                next: true,
                results: []
            }
        }
    },

    sockets: {
        notify({ data }) {
            if (data.event_type === 'help_desk_message_create')
                this.addNewMessage(data.obj, data.tickets || [])

            if(data.event_type === 'help_desk_client_message_create')
                this.addNewMessage(data.obj, data.tickets || [])
        }
    },

    watch: {
        async showChat(val) {
            this.toggleBodyLock(val && this.isMobile)

            if (val) {
                this.$nextTick(async () => {
                    this.stickToBottom = true
                    this.scrollToBottomHard()

                    await this.requestNewMessageCount()

                    const force = this.newMessageCount > 0
                    this.markAllLoadedAsRead(force)
                })
            } else {
                this.$nextTick(() => {
                    this.requestNewMessageCount()
                })
            }
        },

        isMobile(val) {
            this.toggleBodyLock(this.showChat && val)
        }
    },

    mounted() {
        this.scroller = this.$refs.scroller
        const container = this.$el.querySelector('.chat_message_list__scroller')

        if (window.ResizeObserver && container) {
            this.resizeObs = new ResizeObserver(() => {
                if (this.stickToBottom) this.scrollToBottomSync()
            })
            this.resizeObs.observe(container)
        }

        const { y } = useScroll(this.scroller)
        this.stopWatch = this.$watch(() => y.value, () => {
            this.$nextTick(() => {
                const scrollBottom =
                    this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight

                this.atBottom = scrollBottom < 150
                this.stickToBottom = this.atBottom
                this.showScrollButton = scrollBottom > 150
            })
        })

        this.fetchMessages().then(async () => {
            this.stickToBottom = true
            this.scrollToBottomHard()
            this.initialScrollDone = true

            await this.requestNewMessageCount()
            if (this.showChat) {
                const force = this.newMessageCount > 0
                this.markAllLoadedAsRead(force)
            }
        })

        useInfiniteScroll(
            this.scroller,
            () => {
                if (!this.loading && this.messages.next) return this.fetchMessages()
            },
            { distance: 200, direction: 'top' }
        )

        this.toggleBodyLock(this.showChat && this.isMobile)
    },

    methods: {
        toggleBodyLock(lock) {
            const cls = 'chat-widget-lock'
            if (lock) document.body.classList.add(cls)
            else document.body.classList.remove(cls)
        },

        getScrollBottom() {
            if (!this.scroller) return 999999
            return this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight
        },

        async requestNewMessageCount() {
            if (!this.ticket?.id) {
                this.newMessageCount = 0
                return Promise.resolve()
            }

            if (this.countPromise) {
                this.countQueued = true
                return this.countPromise
            }

            this.countPromise = (async () => {
                try {
                    const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/count/`)
                    this.newMessageCount = Number(data?.new_message_count || 0)
                } catch (error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.countPromise = null
                    if (this.countQueued) {
                        this.countQueued = false
                        this.requestNewMessageCount()
                    }
                }
            })()

            return this.countPromise
        },

        markAllLoadedAsRead(force = false) {
            if (!this.ticket?.id) return
            if (!this.showChat) return

            const list = this.messages?.results || []
            if (!list.length) return

            const ids = []
            list.forEach((m) => {
                if (!m?.id) return
                if (force || m.is_new) {
                    ids.push(m.id)
                    if (m.is_new) m.is_new = false
                }
            })

            this.enqueueRead(ids)
        },

        enqueueRead(ids = []) {
            if (!this.ticket?.id) return
            if (!Array.isArray(ids) || !ids.length) return

            ids.forEach((id) => {
                if (id) this.pendingReadMap[id] = true
            })

            if (this.readFlushTimer) return
            this.readFlushTimer = setTimeout(() => {
                this.readFlushTimer = null
                this.flushReadQueue()
            }, 120)
        },

        async flushReadQueue() {
            if (this.markingRead) return
            const ids = Object.keys(this.pendingReadMap)
            if (!ids.length) return

            this.pendingReadMap = {}
            this.markingRead = true

            try {
                const batchSize = 20
                for (let i = 0; i < ids.length; i += batchSize) {
                    const batch = ids.slice(i, i + batchSize)
                    await Promise.all(
                        batch.map((id) =>
                            this.$http.post('/viewers/', { obj: id }).catch((error) => {
                                errorHandler({ error, show: false })
                                return null
                            })
                        )
                    )
                }
            } finally {
                this.markingRead = false
                this.requestNewMessageCount()
            }
        },

        onVideoLoaded() {
            if (this.atBottom) this.scrollToBottom()
        },
        onVideoPlay(el) {
            this.scrollToEl(el)
        },
        onAudioLoaded() {
            if (this.atBottom) this.scrollToBottom()
        },
        onAudioPlay(el) {
            this.scrollToEl(el)
        },

        scrollToEl(el) {
            if (!el || !this.scroller) return
            const s = this.scroller
            const sRect = s.getBoundingClientRect()
            const elRect = el.getBoundingClientRect()
            const target = s.scrollTop + (elRect.top - sRect.top) - 80
            if (s.scrollTo) s.scrollTo({ top: target, behavior: 'smooth' })
            else s.scrollTop = target
            this.stickToBottom = false
        },

        scrollToBottomSync() {
            if (!this.scroller) return
            this.scroller.scrollTop = this.scroller.scrollHeight
        },
        scrollToBottomHard() {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    this.scrollToBottomSync()
                })
            })
        },

        setReplace(message) {
            this.replaceMessage = message
            if (message) {
                this.stickToBottom = true
                this.scrollToBottom()
            }
            this.$nextTick(() => {
                this.$refs.chatFooter.inputFocus()
            })
        },

        addNewMessage(data, tickets) {
            if (!Array.isArray(tickets) || !this.ticket?.id || !tickets.includes(this.ticket.id)) return
            if (!data?.id) return

            const scrollBottomBefore = this.getScrollBottom()
            const wasAtBottom = scrollBottomBefore < 150
            const nearBottomBefore = scrollBottomBefore <= 300

            this.messages.results.push(data)
            this.messages.count += 1
            this.slice_count += 1
            this.replaceMessage = null

            this.$nextTick(() => {
                if (!this.showChat) {
                    this.requestNewMessageCount()
                    return
                }

                const shouldAutoScroll = data?.is_help_desk || wasAtBottom || nearBottomBefore
                if (shouldAutoScroll) {
                    this.stickToBottom = true
                    this.scrollToBottomSync()
                }

                this.enqueueRead([data.id])
                data.is_new = false

                this.requestNewMessageCount()
            })
        },

        scrollToBottom() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        this.scrollToBottomSync()
                    })
                })
            })
        },

        async fetchMessages() {
            if (!this.ticket?.id) return

            this.loading = true
            const prevScrollTop = this.scroller.scrollTop
            const prevScrollHeight = this.scroller.scrollHeight

            const params = {
                page: this.page,
                page_size: 15,
                ticket: this.ticket.id
            }
            if (this.slice_count > 0) params.slice_count = this.slice_count

            try {

                var urlMessages = '/help_desk/contact_persons/messages/'
                if(this.isClientView){
                    urlMessages = `/help_desk/contact_persons/messages/client/list/`
                }
                const { data } = await this.$http.get(urlMessages, { params })

                if (data?.results?.length) {
                    this.messages.results = data.results.concat(this.messages.results)
                    this.messages.count = data.count
                    this.messages.next = data.next
                    this.page += 1
                }

                this.$nextTick(() => {
                    if (this.stickToBottom) {
                        this.scrollToBottomSync()
                    } else {
                        const newScrollHeight = this.scroller.scrollHeight
                        const heightDiff = newScrollHeight - prevScrollHeight
                        this.scroller.scrollTop = prevScrollTop + heightDiff
                    }
                })

                await this.requestNewMessageCount()

                if (this.showChat) {
                    const force = this.newMessageCount > 0
                    this.markAllLoadedAsRead(force)
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        }
    },

    beforeDestroy() {
        if (this.resizeObs) this.resizeObs.disconnect()
        if (this.stopWatch) this.stopWatch()
        if (this.readFlushTimer) clearTimeout(this.readFlushTimer)
        this.toggleBodyLock(false)
    }
}
</script>

<style lang="scss" scoped>
:global(body.chat-widget-lock) {
    overflow: hidden !important;
    touch-action: none !important;
}

@keyframes chatPulse {
    0%   { transform: scale(1);   box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.35); }
    60%  { transform: scale(1.06); box-shadow: 0 0 0 18px rgba(24, 144, 255, 0); }
    100% { transform: scale(1);   box-shadow: 0 0 0 0 rgba(24, 144, 255, 0); }
}

@keyframes chatWiggle {
    0%, 100% { transform: rotate(0deg); }
    20% { transform: rotate(-10deg); }
    40% { transform: rotate(10deg); }
    60% { transform: rotate(-6deg); }
    80% { transform: rotate(6deg); }
}

@keyframes badgePop {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.12); }
}

.chat_widget_root {
    height: 100%;
    width: 100%;
    position: relative;
}

.chat_widget_root.mobile_layer {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 10000;
    background: #f7f9fc;
}

.chat_widget_root.mobile_layer .chat_wrapper {
    border-radius: 0;
    width: 100%;
    height: 100%;
}

.empty_ticket {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    top: 0;
    left: 0;
    text-align: center;
    color: #888888;

    &__message {
        margin-top: 10px;
        max-width: 250px;
    }

    i {
        font-size: 56px;
    }
}

.slide-up-fade-enter-active {
    transition: all 0.2s ease;
}
.slide-up-fade-leave-active {
    transition: all 0.1s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-up-fade-enter,
.slide-up-fade-leave-to {
    transform: translateY(10px);
    opacity: 0;
}

.scroll_down {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    border-radius: 50%;
    position: absolute;
    bottom: 15px;
    right: 20px;
    z-index: 10;
    cursor: pointer;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.0784313725);
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    user-select: none;

    &:hover {
        color: var(--blue);
    }

    &::v-deep {
        .ant-badge-count {
            top: -8px;
            right: -8px;
        }
    }
}

.chat_wrapper {
    background: #f7f9fc;
    border-radius: 12px;
    height: 100%;

    &__body {
        overflow: hidden;
        position: relative;

        .chat_message_list {
            overflow-y: auto;
            height: 100%;
            position: relative;

            .chat_message_list__scroller {
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
            }
        }
    }
}

.spinner-wrap {
    display: flex;
    justify-content: center;
    padding: 12px 0;
}

/* ✅ attention animation for collapsed bubble */
.chat_collapse_btn {
    position: relative;
    transform: translateZ(0);
    will-change: transform;
}

.chat_collapse_btn--attention {
    animation: chatPulse 1.6s ease-in-out infinite;
}

/* анимируем иконку внутри кнопки (через deep, т.к. её рендерит библиотека) */
.chat_collapse_btn--attention::v-deep i {
    display: inline-block;
    animation: chatWiggle 1.6s ease-in-out infinite;
    transform-origin: 50% 60%;
}

/* подпрыгивание бейджа только когда attention */
.chat_collapse_badge--attention::v-deep .ant-badge-count {
    animation: badgePop 1.6s ease-in-out infinite;
}

/* оставил твой класс, вдруг где-то используется */
.chat_collapse_bar {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.0784313725);
}
</style>
