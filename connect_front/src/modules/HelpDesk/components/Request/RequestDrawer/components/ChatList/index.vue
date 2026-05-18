<template>
    <div class="chat_wrapper h-full flex flex-col" :class="isMobile && 'overflow-hidden'">
        <ChatHeader v-if="ticket" :ticket="ticket" :showAside="showAside" :changeShowAside="changeShowAside" :useAside="useAside" />
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
                v-if="edit && actions && actions.create_message && ticket.status && ticket.status.code !== 'completed'"
                ref="chatFooter"
                :ticket="ticket"
                :actions="actions"
                :scrollToBottom="scrollToBottom"
                :replaceMessage="replaceMessage"
                :setReplace="setReplace"
                :addNewMessage="addNewMessage" />
        </template>
    </div>
</template>

<script>
import { useInfiniteScroll, useScroll } from '@vueuse/core'
import ChatHeader from './Header.vue'
import Message from './Message.vue'
import Footer from './Footer.vue'
export default {
    name: 'ChatWidget',
    components: {
        ChatHeader,
        Message,
        Footer
    },
    props: {
        ticket: {
            type: Object,
            default: () => null
        },
        showAside: {
            type: Boolean,
            default: false
        },
        changeShowAside: {
            type: Function,
            default: () => {}
        },
        useAside: {
            type: Boolean,
            default: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
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
            initialScrollDone: false,
            messages: {
                count: 0,
                next: true,
                results: []
            }
        }
    },
    sockets: {
        notify({ data }) {
            if(data.event_type === 'help_desk_client_message_create')
                this.addNewMessage(data.obj, data.tickets || [])
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
                const scrollBottom = this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight
                this.atBottom = scrollBottom < 150
                this.stickToBottom = this.atBottom
                this.showScrollButton = scrollBottom > 150
                if (this.atBottom && this.newMessageCount) this.newMessageCount = 0
            })
        })

        this.fetchMessages().then(() => {
            this.stickToBottom = true
            this.scrollToBottomHard()
            this.initialScrollDone = true
        })

        useInfiniteScroll(this.scroller, () => {
            if (!this.loading && this.messages.next) return this.fetchMessages()
        }, { distance: 200, direction: 'top' })
    },
    methods: {
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
            if (!Array.isArray(tickets) || !tickets.includes(this.ticket.id)) return

            this.messages.results.push(data)
            this.messages.count += 1
            this.slice_count += 1
            this.replaceMessage = null

            this.$nextTick(() => {
                const scrollBottom = this.scroller.scrollHeight - this.scroller.scrollTop - this.scroller.clientHeight
                if (data.is_help_desk || scrollBottom <= 300) {
                    this.stickToBottom = true
                    this.scrollToBottom()
                } else {
                    this.newMessageCount += 1
                }
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
            if(this.ticket?.id) {
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
                    const { data } = await this.$http.get(`/help_desk/contact_persons/messages/client/list/`, {params})

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
                } catch (e) {
                    this.$message.error(this.$t('Error'))
                } finally {
                    this.loading = false
                }
            }
        }
    },
    beforeDestroy() {
        if (this.observer) this.observer.disconnect()
    }
}
</script>

<style lang="scss" scoped>
.empty_ticket{
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
    &__message{
        margin-top: 10px;
        max-width: 250px;
    }
    i{
        font-size: 56px;
    }
}
.slide-up-fade-enter-active {
  transition: all .2s ease;
}
.slide-up-fade-leave-active {
  transition: all .1s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-up-fade-enter, .slide-up-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
.scroll_down{
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
    &:hover{
        color: var(--blue);
    }
    &::v-deep{
        .ant-badge-count{
            top: -8px;
            right: -8px;
        }
    }
}
.chat_wrapper {
  background: #f7f9fc;
  border-radius: 12px;
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
</style>
