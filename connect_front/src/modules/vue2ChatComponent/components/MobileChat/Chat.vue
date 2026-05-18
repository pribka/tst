<template>
    <div class="chat_page_wrapper">
        <div class="chat_messenger">
            <div class="chat_layer">
                <ChatBodyHeader :replySearch="replySearch" />
                <div class="chat_content">
                    <div 
                        ref="chatBodyArea"
                        class="chat_body" 
                        :class="currentPin && currentPin.results.length && 'open_pin'"
                        :data-initializing="initialViewportReady ? '0' : '1'"
                        @scroll="scrollAction"
                        @wheel.passive="handleUserScrollInteraction"
                        @touchmove.passive="handleUserScrollInteraction">
                        <template v-if="activeChat && activeChat.is_active">
                            <div v-if="reloadLoading" class="flex justify-center">
                                <a-spin />
                            </div>
                            <div
                                v-if="loading && !topInfiniteEnabled"
                                class="tp_spinner">
                                <a-spin />
                            </div>
                            <infinite-loading
                                v-if="topInfiniteEnabled && !infinitePaused && !reloadLoading && !deepLinkMode"
                                v-bind:distance="5"
                                :identifier="`${ activeChat.chat_uid }_top_${ topInfiniteKey }`"
                                direction="top"
                                @infinite="upScrollHandler">
                                <div slot="spinner">
                                    <div class="tp_spinner">
                                        <a-spin v-show="loading" />
                                    </div>
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                            <div
                                v-if="displayMessages"
                                class="chat__log"
                                ref="chatLog">
                            <div
                                v-for="(item, index) in displayMessages.value"
                                :key="item.id"
                                class="message_entry"
                                :class="getMessageAnimationClass(item)">
                                    <div
                                        v-if="shouldShowUnreadDivider(item, index)"
                                        class="chat_unread_divider">
                                        <span class="chat_unread_divider__line"></span>
                                        <span class="chat_unread_divider__label">{{ $t('chat.new_messages') }}</span>
                                        <span class="chat_unread_divider__line"></span>
                                    </div>
                                    <ChatMessage
                                        :replySearch="replySearch"
                                        :user="user"
                                        useReact
                                        :resizeEvent="resizeEventMessage"
                                        :isScrolling="isScrolling"
                                        :messageItem="item" />
                                </div>
                            </div>

                            <infinite-loading
                                v-if="bottomInfiniteEnabled && !infinitePaused && !deepLinkMode && !isSearching && canLoadBottomMore"
                                v-bind:distance="10"
                                :ref="`${ activeChat.chat_uid }_bottom`"
                                :identifier="bottomInfiniteIdentifier"
                                @infinite="downScrollHandler">
                                <div slot="spinner">
                                    <div class="bt_spinner">
                                        <a-spin />
                                    </div>
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>

                            <transition name="slide">
                                <div
                                    v-if="replyMessage"
                                    class="reply_dummy"></div>
                            </transition>
                        </template>
                        <div v-else-if="isEmptyStandaloneChatWindow" class="empty_chat_window_state">
                            <div class="empty_chat_window_state__title">
                                {{ $t('chat.empty_window_title') }}
                            </div>
                            <div class="empty_chat_window_state__text">
                                {{ $t('chat.empty_window_text') }}
                            </div>
                        </div>
                    </div>
                    <div v-show="!isSearching" class="chat_footer">
                        <ChatFooter
                            v-if="activeChat && activeChat.is_active"
                            :resizeEvent="resizeEvent"
                            :missedCount="missedCount"
                            :showDownBtn="showDownBtnSync"
                            :loadingDown="loadingDown"
                            :downAction="downAction"
                            ref="ChatFooter" />   
                    </div>
                </div>
                <div class="footer_dummy"></div>
            </div>
        </div>
    </div>
</template>

<script>
import ChatEventBus from '../../utils/ChatEventBus'
import { mapMutations, mapActions, mapState, mapGetters } from 'vuex'
import 'lazysizes'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
import { useScroll } from '@vueuse/core'
import { pauseAllVoicePlayback } from '@/utils/voicePlayback'
const key = 'searchKey'
const EMPTY_CHAT_WINDOW_ID = '00000000-0000-0000-0000-000000000000'
let wFocus,
    scrollEndTid
export default {
    components: {
        ChatBodyHeader: () => import('../ChatBodyHeader'),
        ChatFooter: () => import('../ChatFooter'),
        ChatMessage: () => import('../ChatMessage/index.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    beforeRouteLeave(to, from, next) {
        Promise.resolve(this.$refs.ChatFooter?.persistDraftByChat?.())
            .catch(() => {})
            .finally(() => next())
    },
    props: {
        task: {
            type: Boolean,
            default: false
        },
        meetings: {
            type: Boolean,
            default: false
        },
        dealerChat: {
            type: Boolean,
            default: false
        }
    },
    metaInfo() {
        return {
            htmlAttrs: {
                class: 'chat_page bg_white'
            }
        }
    },
    computed: {
        ...mapState({
            activeChat: state=> state.chat.activeChat,
            user: state => state.user.user,
            pinMessage: state => state.chat.pinMessage,
            dialogLoading: state => state.chat.dialogLoading,
            messageListPrev: state => state.chat.messageListPrev,
            isMobile: state => state.isMobile,
            sidebarInfo: state => state.chat.sidebarInfo
        }),
        ...mapGetters({
            chatMessages: 'chat/chatMessages',
            getReplyMessage: 'chat/replyMessage',
            getCountMessages: 'chat/getCountMessages',
            getChatHistoryState: 'chat/chatHistoryState'
        }),
        activeChatUid() {
            return this.activeChat?.chat_uid || null
        },
        messages() {
            return this.activeChatUid ? this.chatMessages(this.activeChatUid) : null
        },
        replyMessage() {
            return this.activeChatUid ? this.getReplyMessage(this.activeChatUid) : null
        },
        currentMessage() {
            if(this.activeChat && this.messages){
                return this.messages
            }
            else
                return false
        },
        currentPin() {
            if(this.activeChatUid && this.pinMessage[this.activeChatUid])
                return this.pinMessage[this.activeChatUid]
            else
                return false
        },
        missedCount() {
            return this.missedCountLocal
        },

        isSearching() {
            const uid = this.activeChat?.chat_uid
            if (!uid) return false
            const text = this.$store.state.chat.chatSearchTextByChat?.[uid] || ''
            const q = text.toString().trim()
            return q.length >= 3
        },
        searchMoreKey() {
            const uid = this.activeChat?.chat_uid
            if (!uid || !this.isSearching) return null
            const q = (this.$store.state.chat.chatSearchTextByChat?.[uid] || '').toString().trim()
            if (!q || q.length < 3) return null
            return `${uid}|${q}`
        },
        searchMoreScrollDone() {
            const k = this.searchMoreKey
            if (!k) return false
            return this.$store.state.chat.chatSearchMoreScrollDoneByKey?.[k] === true
        },
        searchMessages() {
            const uid = this.activeChat?.chat_uid
            if (!uid) return null

            const bucket = this.$store.state.chat.chatSearchMessageByChat?.[uid]
            if (!bucket) {
                return { value: [], hasMore: false, loading: false, page: 1, query: '' }
            }

            return {
                value: bucket.results || [],
                hasMore: !!bucket.hasMore,
                loading: !!bucket.loading,
                page: bucket.page || 1,
                query: bucket.query || ''
            }
        },
        displayMessages() {
            if (!this.activeChat) return null
            return this.isSearching ? this.searchMessages : this.messages
        },
        displayMessageIds() {
            return Array.isArray(this.displayMessages?.value)
                ? this.displayMessages.value.map(item => item.message_uid || item.id)
                : []
        },
        searchAutoKey() {
            const uid = this.activeChat?.chat_uid
            if (!uid) return null

            const q = (this.$store.state.chat.chatSearchTextByChat?.[uid] || '').toString().trim()
            if (q.length < 3) return null

            return `${uid}|${q}`
        },
        isSearchOpen() {
            const uid = this.activeChat?.chat_uid
            if (!uid) return false
            return this.$store.state.chat.chatSearchPanelOpen?.[uid] === true
        },
        showDownBtnSync() {
            if(this.displayMessages?.prev?.length)
                return true
            return this.showDownBtn
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        isEmptyStandaloneChatWindow() {
            return this.isStandaloneChatWindow && this.$route.params.id === EMPTY_CHAT_WINDOW_ID
        },
        currentHistoryState() {
            return this.activeChatUid
                ? this.getChatHistoryState(this.activeChatUid)
                : null
        },
        currentReadCreated() {
            return this.currentHistoryState?.readCursorCreated
                || this.activeChat?.my_readed_at
                || null
        },
        dividerCreated() {
            return this.currentHistoryState?.dividerCreated || null
        },
        dividerAtStart() {
            return this.currentHistoryState?.dividerAtStart === true
        },
        isUnreadEntryMode() {
            return !!this.currentHistoryState?.active
        },
        canLoadBottomMore() {
            if (this.isUnreadEntryMode) {
                // В history-режиме нижняя догрузка идет через отдельный курсор.
                return !!this.currentHistoryState?.canLoadAfter
            }

            return !!(this.displayMessages?.prev && this.displayMessages.prev.length)
        },
        bottomInfiniteIdentifier() {
            const uid = this.activeChat?.chat_uid || 'chat'
            if (this.isUnreadEntryMode) {
                return `${uid}_history_${this.currentHistoryState?.afterCreated || 'none'}_${this.currentHistoryState?.canLoadAfter ? '1' : '0'}`
            }

            return `${uid}_${this.displayMessages?.prev || ''}`
        }
    },
    data() {
        return {
            loading: false,
            emptyMessage: false,
            showDownBtn: false,
            loadingDown: false,
            init: true,
            isScrolling: false,
            reloadLoading: false,
            initChat: true,
            handleState: null,
            downLoading: false,
            scrollBlock: false,
            suppressInfiniteActivation: false,
            hasUserScrollInteraction: false,
            searchMessage: false,
            animatedMessageIds: {},
            messageAnimationTimers: {},
            infinitePaused: false,
            topInfiniteEnabled: false,
            bottomInfiniteEnabled: false,
            topInfiniteKey: 0,
            deepLinkMode: false,
            lastAnchorMessageId: null,
            lastFocusTs: 0,
            enterScrolling: false,
            replyAnchorUid: null,
            searchAutoScrollDone: {},
            topInfiniteLock: false,
            missedCountLocal: 0,
            firstMissedUid: null,
            activeChatLoadKey: 0,
            readProgressTimer: null,
            readProgressSending: false,
            pendingReadCreated: null,
            initialViewportReady: true
        }
    },
    watch: {
        searchAutoKey(newKey, oldKey) {
            if (!newKey) return
            if (newKey !== oldKey) {
                this.$set(this.searchAutoScrollDone, newKey, false)
            }
        },
        isSearching(val, old) {
            if (!old && val) {
                if (this.searchAutoKey) this.$set(this.searchAutoScrollDone, this.searchAutoKey, false)
                this.topInfiniteKey += 1
            }

            if (old && !val) {
                this.$nextTick(async () => {
                    await this.enterChatScrollBottom()
                    this.topInfiniteKey += 1
                })
            }
        },
        searchMessages: {
            deep: true,
            handler(val) {
                if (!this.isSearching) return

                const k = this.searchAutoKey
                if (!k) return

                const newLen = Array.isArray(val?.value) ? val.value.length : 0
                if (this.searchAutoScrollDone[k] === true) return

                if (newLen > 0) {
                    this.$nextTick(async () => {
                        await this.enterChatScrollBottom()
                        this.topInfiniteKey += 1
                        this.$set(this.searchAutoScrollDone, k, true)
                    })
                }
            }
        },
        displayMessageIds(newIds, oldIds) {
            this.handleNewMessageAnimations(newIds, oldIds)
        },
        activeChat(val, oldVal) {
            if (oldVal?.chat_uid && oldVal.chat_uid !== val?.chat_uid) {
                pauseAllVoicePlayback({ reason: 'mobile-chat-switch', broadcast: false })
            }

            if (!val) {
                pauseAllVoicePlayback({ reason: 'mobile-chat-cleared', broadcast: false })
                this.topInfiniteEnabled = false
                this.bottomInfiniteEnabled = false
                this.hasUserScrollInteraction = false
                this.initialViewportReady = true
            }

            clearTimeout(this.readProgressTimer)
            this.readProgressTimer = null
            this.readProgressSending = false
            this.pendingReadCreated = null

            if (val) {
                const hasLocalMessages = !!this.chatMessages(val.chat_uid)?.value?.length
                this.topInfiniteKey += 1
                this.topInfiniteEnabled = false
                this.bottomInfiniteEnabled = false
                this.hasUserScrollInteraction = false
                this.initialViewportReady = hasLocalMessages || val.no_create === true
                this.showDownBtn = false
                this.missedCountLocal = 0
                this.firstMissedUid = null
            }
        },
        '$route.params.id'(newVal, oldVal) {
            if (!newVal || newVal === oldVal) return

            if (this.$route.query?.message_id) {
                this.lastAnchorMessageId = this.$route.query.message_id
                this.deepLinkMode = true
                this.infinitePaused = true
                this.getOpenChat().then(() => this.replySearch({ message_uid: this.$route.query.message_id }))
                return
            }

            this.lastAnchorMessageId = null
            this.deepLinkMode = false
            this.infinitePaused = false
            this.getOpenChat()
        },
        '$route.query.message_id'(newVal, oldVal) {
            if (!newVal || newVal === oldVal) return
            if (!this.activeChat) return

            this.lastAnchorMessageId = newVal
            this.deepLinkMode = true
            this.infinitePaused = true
            this.replySearch({ message_uid: newVal })
        }
    },
    methods: {
        ...mapActions({
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat',
            getMessageScroll: 'chat/getMessageScroll',
            getMessage: 'chat/getMessage',
            getMessageDownScroll: 'chat/getMessageDownScroll',
            getPinMessage: 'chat/getPinMessage',
            getInitialChatMessages: 'chat/getInitialChatMessages',
            getHistoryAfterMessages: 'chat/getHistoryAfterMessages',
            updateReadProgress: 'chat/updateReadProgress'
        }),
        ...mapMutations({
            SET_ACTIVE_CHAT: 'chat/SET_ACTIVE_CHAT',
            clearMessage: "chat/clearMessage",
            setScrollToped: "chat/setScrollToped",
            CLEAR_CHAT: 'chat/CLEAR_CHAT',
            TOGGLE_INFO_SIDEBAR: 'chat/TOGGLE_INFO_SIDEBAR'
        }),
        getAnchorSnapshot() {
            const container = this.$refs.chatBodyArea
            const uid = this.replyAnchorUid
            const elem = uid ? document.getElementById(`message_${uid}`) : null
            if (!container || !elem) return null

            const containerRect = container.getBoundingClientRect()
            const elemRect = elem.getBoundingClientRect()

            return {
                topInViewport: elemRect.top - containerRect.top,
                scrollTop: container.scrollTop
            }
        },
        handleUserScrollInteraction() {
            if (this.suppressInfiniteActivation) return
            this.hasUserScrollInteraction = true
            if (!this.topInfiniteEnabled) {
                this.topInfiniteEnabled = true
                this.topInfiniteKey += 1
            }
            this.topInfiniteEnabled = true
            this.bottomInfiniteEnabled = true
        },
        async runWithInfiniteSuppressed(fn) {
            this.suppressInfiniteActivation = true
            try {
                return await fn()
            } finally {
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        this.suppressInfiniteActivation = false
                    })
                })
            }
        },
        isNearBottom(extra = 300) {
            const c = this.$refs.chatBodyArea
            if (!c) return false
            const gap = c.scrollHeight - c.scrollTop - c.clientHeight
            return gap <= extra
        },
        compareCreated(left, right) {
            if (!left && !right) return 0
            if (!left) return -1
            if (!right) return 1

            const leftTs = Date.parse(left)
            const rightTs = Date.parse(right)

            if (Number.isNaN(leftTs) || Number.isNaN(rightTs)) {
                return String(left).localeCompare(String(right))
            }
            if (leftTs === rightTs) return 0
            return leftTs > rightTs ? 1 : -1
        },
        isCreatedAfter(left, right) {
            return this.compareCreated(left, right) > 0
        },
        getFirstUnreadVisibleCreated() {
            if (!Array.isArray(this.displayMessages?.value)) return null
            if (this.dividerAtStart) return this.displayMessages.value[0]?.created || null
            if (!this.dividerCreated) return null

            const firstUnread = this.displayMessages.value.find(item => this.isCreatedAfter(item?.created, this.dividerCreated))
            return firstUnread?.created || null
        },
        getLatestVisibleReadCreated() {
            const container = this.$refs.chatBodyArea
            if (!container) return null

            const containerRect = container.getBoundingClientRect()
            const nodes = Array.from(container.querySelectorAll('.msg_item[data-created]'))
            let latestCreated = null

            nodes.forEach(node => {
                const created = node?.dataset?.created
                if (!created) return
                if (this.currentReadCreated && !this.isCreatedAfter(created, this.currentReadCreated) && !this.pendingReadCreated) {
                    return
                }

                const rect = node.getBoundingClientRect()
                const visibleHeight = Math.min(rect.bottom, containerRect.bottom) - Math.max(rect.top, containerRect.top)
                const visibilityRatio = rect.height > 0 ? visibleHeight / rect.height : 0

                if (visibilityRatio < 0.6) return
                if (!latestCreated || this.isCreatedAfter(created, latestCreated)) {
                    latestCreated = created
                }
            })

            return latestCreated
        },
        // unread двигаем только по реально видимым сообщениям.
        // Сам факт загрузки пачки ничего не означает: пользователь мог их еще не увидеть.
        scheduleReadProgressSync() {
            if (!this.activeChat?.chat_uid) return
            if (this.isSearching || this.loading || this.searchMessage) return

            const visibleCreated = this.getLatestVisibleReadCreated()
            if (!visibleCreated) return

            const currentCreated = this.pendingReadCreated || this.currentReadCreated
            if (currentCreated && !this.isCreatedAfter(visibleCreated, currentCreated)) return

            this.pendingReadCreated = visibleCreated

            if (this.readProgressSending) return
            clearTimeout(this.readProgressTimer)
            this.readProgressTimer = setTimeout(() => {
                this.flushReadProgressSync()
            }, 120)
        },
        async flushReadProgressSync() {
            if (!this.activeChat?.chat_uid || this.readProgressSending) return

            const created = this.pendingReadCreated
            if (!created) return

            this.readProgressSending = true
            let appliedCreated = null
            let unreadCount = null
            try {
                const data = await this.updateReadProgress({
                    chat_uid: this.activeChat.chat_uid,
                    created
                })

                appliedCreated = data?.my_readed_at || data?.created || null
                unreadCount = Number(data?.unread_count || 0)

                if (unreadCount <= 0) {
                    this.pendingReadCreated = null
                    clearTimeout(this.readProgressTimer)
                    this.readProgressTimer = null
                    return
                }

                if (!this.pendingReadCreated || (appliedCreated && !this.isCreatedAfter(this.pendingReadCreated, appliedCreated))) {
                    this.pendingReadCreated = null
                }
            } catch (e) {
                // noop
            } finally {
                this.readProgressSending = false

                const compareBase = appliedCreated || this.currentReadCreated
                if (unreadCount > 0 && this.pendingReadCreated && this.isCreatedAfter(this.pendingReadCreated, compareBase)) {
                    clearTimeout(this.readProgressTimer)
                    this.readProgressTimer = setTimeout(() => {
                        this.flushReadProgressSync()
                    }, 120)
                }
            }
        },
        restoreAnchorSnapshot(snapshot) {
            const container = this.$refs.chatBodyArea
            const uid = this.replyAnchorUid
            const elem = uid ? document.getElementById(`message_${uid}`) : null
            if (!snapshot || !container || !elem) return

            const containerRect = container.getBoundingClientRect()
            const elemRect = elem.getBoundingClientRect()
            const newTopInViewport = elemRect.top - containerRect.top

            const diff = newTopInViewport - snapshot.topInViewport
            if (Math.abs(diff) >= 1) {
                container.scrollTop = snapshot.scrollTop + diff
            }
        },
        isOwnMessage(item) {
            return !!(this.user?.id && item?.message_author?.id === this.user.id)
        },
        getMessageAnimationClass(item) {
            const id = item?.message_uid || item?.id
            if (!id || !this.animatedMessageIds[id]) return ''
            return this.isOwnMessage(item)
                ? 'message_entry_enter message_entry_enter_own'
                : 'message_entry_enter message_entry_enter_other'
        },
        handleNewMessageAnimations(newIds = [], oldIds = []) {
            if (this.isSearching) return
            if (!Array.isArray(newIds) || !Array.isArray(oldIds)) return
            if (!oldIds.length || newIds.length <= oldIds.length) return

            const samePrefix = oldIds.every((id, index) => newIds[index] === id)
            if (!samePrefix) return

            newIds.slice(oldIds.length).forEach(id => this.markMessageAnimated(id))
        },
        markMessageAnimated(id) {
            if (!id) return

            if (this.messageAnimationTimers[id]) {
                clearTimeout(this.messageAnimationTimers[id])
            }

            this.$set(this.animatedMessageIds, id, true)
            this.messageAnimationTimers[id] = setTimeout(() => {
                this.$delete(this.animatedMessageIds, id)
                delete this.messageAnimationTimers[id]
            }, 320)
        },
        resetMessageAnimations() {
            Object.values(this.messageAnimationTimers).forEach(timerId => clearTimeout(timerId))
            this.messageAnimationTimers = {}
            this.animatedMessageIds = {}
        },
        // Divider is anchored to the chat entry boundary and must not follow live read progress.
        // Линия "Новые сообщения" привязана к границе входа в чат.
        // Пока пользователь читает вниз, сам read-progress меняется, но линия не должна "ехать" вместе с ним.
        shouldShowUnreadDivider(item, index) {
            if (this.isSearching) return false
            if (this.dividerAtStart) return index === 0
            if (!this.dividerCreated || !item?.created) return false
            if (!this.isCreatedAfter(item.created, this.dividerCreated)) return false

            const prevItem = index > 0 ? this.displayMessages?.value?.[index - 1] : null
            return !prevItem?.created || !this.isCreatedAfter(prevItem.created, this.dividerCreated)
        },

        async ensureScrollBottom({ respectUserScroll = true } = {}) {
            await this.runWithInfiniteSuppressed(async () => {
                let tries = 16
                let stable = 0
                let lastHeight = -1

                await new Promise(resolve => {
                    const step = () => {
                        if (respectUserScroll && this.hasUserScrollInteraction) return resolve()
                        const container = this.$refs.chatBodyArea
                        if (!container) return resolve()

                        const h = container.scrollHeight
                        container.scrollTop = h

                        if (h === lastHeight) stable += 1
                        else stable = 0

                        lastHeight = h
                        tries -= 1

                        if (stable >= 3 || tries <= 0) return resolve()
                        requestAnimationFrame(step)
                    }

                    requestAnimationFrame(step)
                })
            })
        },
        async afterChatFirstRender() {
            if (this.scrollBlock) return
            if (this.infinitePaused) return
            if (this.replyAnchorUid) return
            if (this.hasUserScrollInteraction) return

            if (this.isUnreadEntryMode && this.dividerCreated) {
                await this.scrollToReadBoundary()
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        this.initialViewportReady = true
                    })
                })
                this.scheduleReadProgressSync()
                return
            }

            await this.$nextTick()
            if (this.hasUserScrollInteraction) return
            await this.ensureScrollBottom()
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    this.initialViewportReady = true
                })
            })
            this.scheduleReadProgressSync()
        },
        async enterChatScrollBottom() {
            if (this.deepLinkMode) return
            if (this.enterScrolling) return
            // Если открылись через unread-history, скроллим не в самый низ,
            // а к границе первого непрочитанного сообщения.
            if (this.isUnreadEntryMode && this.dividerCreated) {
                await this.scrollToReadBoundary()
                this.scheduleReadProgressSync()
                return
            }
            this.enterScrolling = true

            this.infinitePaused = true

            await this.$nextTick()
            await this.ensureScrollBottom()

            this.topInfiniteKey += 1
            await this.$nextTick()

            this.infinitePaused = false
            this.enterScrolling = false
            this.scheduleReadProgressSync()
        },
        infiniteTopHandler($state) {
            this.handleState = $state
            this.onScroll($state)
        },
        onScroll($state) {
            clearTimeout(scrollEndTid)
            scrollEndTid = setTimeout(() => {
                if (this.handleState) {
                    this.upScrollHandler($state)
                    this.handleState = null
                }
            }, 200)
        },
        resizeEventMessage() {
            this.resizeEvent(150)
        },
        resizeEvent(addH = 100) {
            this.$nextTick(() => {
                if (this.replyAnchorUid) return
                if(this.$refs.chatBodyArea) {
                    const c = this.$refs.chatBodyArea
                    const currScroll = c.scrollHeight - c.scrollTop
                    const checkScroll = c.clientHeight + addH

                    if(currScroll < checkScroll) {
                        this.scrollDown()
                    }
                }
            })
        },
        async getOpenChat(reload = false) {
            if (this.isEmptyStandaloneChatWindow) {
                this.CLEAR_CHAT()
                this.initialViewportReady = true
                return
            }

            try {
                const chat_id = this.$route.params.id
                const user_id = this.$route.query?.user || null
                if (this.activeChat?.no_create && String(this.activeChat.chat_uid) === String(chat_id)) {
                    this.initialViewportReady = true
                    return
                }

                if(user_id) {
                    const res = await this.getPrivateChat(user_id)
                    if (!res?.chat_uid) {
                        this.initialViewportReady = true
                        return
                    }
                    await this.$router.replace({query: {chat_id: res.chat_uid}})
                    const chat = await this.getCurrentChat(res.chat_uid)
                    if (!chat || chat.chat_uid !== res.chat_uid) return

                    if (!this.chatMessages(res.chat_uid)?.value?.length) {
                        this.clearMessage()
                    }
                    await this.getInitialChatMessages({
                        chat_uid: res.chat_uid,
                        useUnreadHistory: Number(this.activeChat?.new_message_count || 0) > 0
                    })

                    await this.getPinMessages()

                    if (!this.activeChat.is_public)
                        this.$socket.client.emit('chat_status_user', { 
                            chat_uid: this.activeChat.chat_uid, 
                            user_uid: this.activeChat.recipient.id 
                        })

                    if (!this.deepLinkMode)
                        await this.afterChatFirstRender()

                    if(this.$route.query?.chat_id) {
                        const query = JSON.parse(JSON.stringify(this.$route.query))
                        delete query.chat_id
                        this.$router.replace({query})
                    }
                } else {
                    const chat = await this.getCurrentChat(chat_id)
                    if (!chat || chat.chat_uid !== chat_id) return

                    if (!this.chatMessages(chat_id)?.value?.length) {
                        this.clearMessage()
                    }
                    await this.getInitialChatMessages({
                        chat_uid: chat_id,
                        useUnreadHistory: Number(this.activeChat?.new_message_count || 0) > 0
                    })

                    await this.getPinMessages()

                    if (!this.activeChat.is_public)
                        this.$socket.client.emit('chat_status_user', { 
                            chat_uid: this.activeChat.chat_uid, 
                            user_uid: this.activeChat.recipient.id 
                        })

                    if (!this.deepLinkMode)
                        await this.afterChatFirstRender()
                }
            } catch (error) {
                if (!this.dealerChat)
                    this.$router.push({ name: 'chat' })

                if (error.detail) {
                    if (error.detail === this.$t('chat.page_not_found')) {
                        this.$message.error(this.$t('chat.chat_not_found'))
                    } else {
                        this.$message.error(error.detail)
                    }
                }
            }
        },
        async getPinMessages() {
            try {
                await this.$store.dispatch('chat/getPinMessage', {
                    page_size: 10
                })
            } catch(e) {

            }
        },
        async downAction(){
            this.loadingDown = true

            await this.scrollTestPrev()

            if (this.missedCountLocal > 0 && this.firstMissedUid) {
                await this.scrollToMessageUid(this.firstMissedUid)
                this.missedCountLocal = 0
                this.firstMissedUid = null
            } else {
                this.scrollDown()
            }

            this.clearCount()

            this.loadingDown = false
        },
        async clearCount(){
            if (this.isUnreadEntryMode) {
                if (this.isNearBottom(40)) {
                    this.scheduleReadProgressSync()
                }
                return
            }
            if(this.missedCount > 0) { 
                this.scheduleReadProgressSync()
            }
        },
        scrollAction(){
            this.$nextTick(() => {
                let container = this.$refs.chatBodyArea
                if(container !== undefined){ 
                    this.scheduleReadProgressSync()
                    const currScroll = container.scrollHeight - container.scrollTop
                    const checkScroll = container.clientHeight + 100

                    if(currScroll >= checkScroll) {
                        this.showDownBtn = true
                        this.setScrollToped(true)
                    } else {
                        this.showDownBtn = false
                        this.setScrollToped(false)
                        this.missedCountLocal = 0
                        this.firstMissedUid = null
                        this.clearCount()
                    }
                }
            })
        },
        async onWindowFocus() {
            const now = Date.now()
            if(now - this.lastFocusTs < 800) return
            this.lastFocusTs = now

            if(this.reloadLoading || this.loading || this.downLoading || this.searchMessage) return

            if(this.lastAnchorMessageId) {
                this.deepLinkMode = true
                this.infinitePaused = true
                await this.replySearch({ message_uid: this.lastAnchorMessageId })
                return
            }

            const container = this.$refs.chatBodyArea
            if(!container) return

            const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight

            if(distanceToBottom < 120) {
                try {
                    this.downLoading = true
                    await this.getMessageDownScroll()
                } finally {
                    this.downLoading = false
                }
            }
        },

        async scrollToMessageUid(message_uid) {
            await this.$nextTick()
            await new Promise(resolve => requestAnimationFrame(() => resolve()))
            await new Promise(resolve => requestAnimationFrame(() => resolve()))

            const container = this.$refs.chatBodyArea
            const elem = document.getElementById(`message_${message_uid}`)
            if (!container || !elem) return false

            const getTargetTop = () => {
                const containerRect = container.getBoundingClientRect()
                const elemRect = elem.getBoundingClientRect()
                const elemTopInContainer = (elemRect.top - containerRect.top) + container.scrollTop
                const centerOffset = (container.clientHeight / 2) - (elemRect.height / 2)
                return Math.max(0, elemTopInContainer - centerOffset)
            }

            let tries = 14
            let last = null

            const step = () => new Promise(resolve => {
                const top = getTargetTop()
                container.scrollTo({ top, behavior: tries > 10 ? 'auto' : 'smooth' })

                const diff = last === null ? 999999 : Math.abs(top - last)
                last = top
                tries -= 1

                if (diff < 2 || tries <= 0) return resolve()
                requestAnimationFrame(() => resolve())
            })

            while (tries > 0) {
                await step()
            }

            return true
        },

        async replySearch(message) {
            this.replyAnchorUid = message.message_uid
            this.searchMessage = true
            this.infinitePaused = true
            this.scrollBlock = true

            try {
                this.lastAnchorMessageId = message.message_uid
                this.$message.loading({ content: `${this.$t('chat.loading')}...`, key })
                if(this.$route.query?.message_id) {
                    const query = JSON.parse(JSON.stringify(this.$route.query))
                    delete query.message_id
                    this.$router.replace({ query })
                }

                let localMessage = false
                if (this.currentMessage && this.currentMessage.value) {
                    localMessage = this.currentMessage.value.find(
                        item => item.message_uid === message.message_uid
                    )
                }

                if(!localMessage) {
                    await this.$store.dispatch('chat/searchMessages', message)
                }

                await this.$nextTick()
                await new Promise(r => requestAnimationFrame(r))
                await new Promise(r => requestAnimationFrame(r))

                let ok = await this.scrollToMessageUid(message.message_uid)

                if (!ok) {
                    setTimeout(async () => {
                        await this.scrollToMessageUid(message.message_uid)
                    }, 300)
                }

                const elem = document.getElementById(`message_${message.message_uid}`)
                if (elem && !elem.classList.contains('flashing')) {
                    elem.classList.add('flashing')
                    setTimeout(() => {
                        elem.classList.remove('flashing')
                    }, 1200)
                }

                ChatEventBus.$emit('CLOSE_PIN_DRAWER')
            } catch(e) {
                this.infinitePaused = false
                this.topInfiniteKey += 1
            } finally {
                this.searchMessage = false
                this.$message.destroy()

                setTimeout(() => {
                    this.scrollBlock = false
                    this.infinitePaused = false
                    this.deepLinkMode = false
                    this.topInfiniteKey += 1
                }, 200)

                setTimeout(() => {
                    this.replyAnchorUid = null
                }, 1500)
            }
        },
        async scrollDown() {
            if (this.scrollBlock) return
            if (this.deepLinkMode) return
            await this.$nextTick()
            await this.ensureScrollBottom({ respectUserScroll: false })
        },
        async scrollToReadBoundary() {
            const container = this.$refs.chatBodyArea
            if (!container) return false

            await this.$nextTick()
            await new Promise(resolve => requestAnimationFrame(resolve))

            const targetCreated = this.getFirstUnreadVisibleCreated()
            if (!targetCreated) return false

            const nodes = Array.from(container.querySelectorAll('.msg_item[data-created]'))
            const targetNode = nodes.find(node => node?.dataset?.created === targetCreated)
            if (!targetNode) return false

            const containerRect = container.getBoundingClientRect()
            const nodeRect = targetNode.getBoundingClientRect()
            const top = (nodeRect.top - containerRect.top) + container.scrollTop - 24
            container.scrollTo({ top: Math.max(0, top), behavior: 'auto' })
            return true
        },
        async scrollTestPrev() {
            if (this.isUnreadEntryMode) return
            if(this.messageListPrev)
                await this.getMessage({refresh: true})
        },
        async downScrollHandler($state) {
            if (this.isSearching) {
                $state.complete()
                return
            }
            if(this.downLoading && this.searchMessage) {
                $state.loaded()
                return
            }
            if (this.downLoading) {
                $state.loaded()
                return
            }
            if (this.isUnreadEntryMode) {
                if (!this.currentHistoryState?.canLoadAfter) {
                    $state.complete()
                    return
                }

                try {
                    this.downLoading = true
                    const data = await this.getHistoryAfterMessages({ chat_uid: this.activeChat.chat_uid })

                    await this.$nextTick()
                    await new Promise(r => requestAnimationFrame(r))

                    if (data?.has_more) {
                        $state.loaded()
                    } else {
                        $state.complete()
                        this.$nextTick(() => {
                            this.scheduleReadProgressSync()
                        })
                    }
                } catch (e) {
                    $state.complete()
                } finally {
                    this.downLoading = false
                }
                return
            }
            if(this.messages) {
                if(this.messages.prev && this.messages.prev.length) {
                    const snapshot = this.getAnchorSnapshot()

                    try {
                        this.downLoading = true
                        await this.getMessageDownScroll()

                        await this.$nextTick()
                        await new Promise(r => requestAnimationFrame(r))

                        this.restoreAnchorSnapshot(snapshot)

                        if(this.messages.bottomStatus)
                            $state.loaded()
                        else
                            $state.complete()
                    } catch(e) {
                        $state.complete()
                    } finally {
                        this.downLoading = false
                    }
                } else {
                    $state.complete()
                }
            } else {
                $state.complete()
            }
        },
        async upScrollHandler($state) {
            const container = this.$refs.chatBodyArea
            const isScrollable = container ? container.scrollHeight > container.clientHeight + 20 : false

            if (this.topInfiniteLock) {
                $state.complete()
                return
            }

            if (!this.topInfiniteEnabled || !this.hasUserScrollInteraction) {
                $state.complete()
                return
            }

            if (this.loading || this.reloadLoading || this.infinitePaused || this.deepLinkMode) {
                $state.complete()
                return
            }

            if (this.isSearching) {
                const uid = this.activeChat.chat_uid
                const bucket = this.searchMessages

                if (bucket?.hasMore && !bucket.loading) {
                    try {
                        this.topInfiniteLock = true
                        this.loading = true

                        await this.$store.dispatch('chat/searchChatMessagesMore', uid)

                        $state.loaded()
                    } catch (e) {
                        $state.complete()
                    } finally {
                        this.loading = false
                        this.topInfiniteLock = false
                    }
                    return
                }

                $state.complete()
                return
            }

            if (!this.messages) {
                try {
                    this.loading = true
                    await this.getMessage()
                    await this.$nextTick()
                    await this.enterChatScrollBottom()
                    this.initChat = false
                    await this.getPinMessage({ page_size: 10, page: 1 })

                    if (isScrollable) $state.loaded()
                    else $state.complete()
                } catch (e) {
                    $state.complete()
                } finally {
                    this.loading = false
                }
                return
            }

            if (this.messages.next === undefined) {
                try {
                    this.topInfiniteLock = true
                    this.loading = true

                    this.initChat = false
                    this.clearMessage()
                    await this.getMessage()
                    await this.getPinMessage({ page_size: 10, page: 1 })

                    if (isScrollable) $state.loaded()
                    else $state.complete()
                } catch (e) {
                    $state.complete()
                } finally {
                    this.loading = false
                    this.topInfiniteLock = false
                }
                return
            }

            if (this.messages.next && this.messages.next.length) {
                try {
                    this.topInfiniteLock = true
                    this.loading = true
                    const snapshot = this.getAnchorSnapshot()
                    await this.getMessageScroll()
                    await this.$nextTick()
                    await new Promise(r => requestAnimationFrame(r))
                    this.restoreAnchorSnapshot(snapshot)

                    if (this.messages.status) $state.loaded()
                    else $state.complete()
                } catch (e) {
                    $state.complete()
                } finally {
                    this.loading = false
                    this.topInfiniteLock = false
                }
                return
            }

            if (this.initChat) {
                this.initChat = false
                await this.$nextTick()
                await this.enterChatScrollBottom()

                if (isScrollable) $state.loaded()
                else $state.complete()
                return
            }

            $state.complete()
        },
        async getMessageCount() {
            try {
                await this.$store.dispatch('chat/getMessageCount')
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async reloadMessage() {
            try {
                this.reloadLoading = true
                await this.clearMessage()
                await this.getOpenChat(true)
                this.getMessageCount()
            } catch(e) {
                console.log(e)
            } finally {
                this.reloadLoading = false
            }
        },
        isElementVisibleInContainer(container, elem) {
            if (!container || !elem) return false
            const c = container.getBoundingClientRect()
            const e = elem.getBoundingClientRect()
            return e.bottom <= c.bottom && e.top >= c.top
        },

        onNewMessageVisibilityCheck(data) {
            if (!this.activeChat) return
            if (this.isSearching) return
            if (data?.chat_uid !== this.activeChat.chat_uid) return
            if (this.user?.id === data?.message_author?.id) return

            const run = () => {
                const container = this.$refs.chatBodyArea
                const elem = document.getElementById(`message_${data.message_uid}`)
                if (!container || !elem) return false

                if (this.isNearBottom(100)) {
                    this.missedCountLocal = 0
                    this.firstMissedUid = null
                    this.showDownBtn = false
                    this.scheduleReadProgressSync()
                    return true
                }

                const visible = this.isElementVisibleInContainer(container, elem)
                if (!visible) {
                    if (!this.firstMissedUid) this.firstMissedUid = data.message_uid
                    this.missedCountLocal += 1
                    this.showDownBtn = true
                } else {
                    if (this.isNearBottom(40)) {
                        this.missedCountLocal = 0
                        this.firstMissedUid = null
                    }
                    this.scheduleReadProgressSync()
                }

                return true
            }

            this.$nextTick(() => {
                if (run()) return
                setTimeout(() => {
                    run()
                }, 60)
            })
        }
    },
    mounted() {
        this.$store.dispatch('chat/getReactions')
        this.$nextTick(() => {
            const { isScrolling } = useScroll(this.$refs.chatBodyArea)
            this.isScrolling = isScrolling
        })

        eventBus.$on('RELOAD_ACTIVE_CHAT', () => {
            this.SET_ACTIVE_CHAT(null)
            setTimeout(() => {
                this.getOpenChat()
            }, 200)
        })
        eventBus.$on('CHAT_OPEN_SEARCH', () => {
            this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat?.chat_uid })
            if(!this.isSearchOpen) {
                this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat?.chat_uid, value: false })
                this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.activeChat?.chat_uid)
            }
        })

        eventBus.$on('CHAT_SEARCH_USER_TAGS', () => {
            if(this.$route.query?.message_id) {
                this.replySearch({
                    message_uid: this.$route.query.message_id
                })
            }
        })
        eventBus.$on('CHAT_SEARCH_SELECT_CHAT', () => {
            if(this.$route.query?.chat_id) {
                this.selectChat(this.$route.query.chat_id)
            }
        })

        ChatEventBus.$on('arreaScroll', () => {
            if (this.deepLinkMode) return
            this.scrollDown()
        })
        ChatEventBus.$on('newMessageArreaScroll', () => {
            if (this.deepLinkMode) return
            if (this.isNearBottom()) {
                this.scrollDown()
            }
        })
        ChatEventBus.$on('arreaScrollDown', () => {
            if (this.deepLinkMode) return
            this.scrollDown()
            this.clearCount()
        })
        ChatEventBus.$on('CHAT_SHOW_NEW_MESSAGE', this.onNewMessageVisibilityCheck)

        if(this.isMobile) {
            wFocus = () => this.onWindowFocus()
            window.addEventListener('focus', wFocus)
        }

        if(this.$route.query?.message_id) {
            this.lastAnchorMessageId = this.$route.query.message_id
            this.deepLinkMode = true
            this.infinitePaused = true
            this.getOpenChat().then(() => this.replySearch({ message_uid: this.$route.query.message_id }))
            return
        }

        if (this.isEmptyStandaloneChatWindow) {
            this.CLEAR_CHAT()
            this.initialViewportReady = true
            return
        }

        if(!this.activeChat?.no_create) {
            this.getOpenChat()
        }
    },
    beforeCreate() {
        this.$store.commit('SHOW_FOOTER', false)
        this.$store.commit('SHOW_HEADER', false)
    },
    beforeDestroy() {
        pauseAllVoicePlayback({ reason: 'mobile-chat-destroy', broadcast: false })
        this.resetMessageAnimations()
        clearTimeout(this.readProgressTimer)
        if(wFocus) window.removeEventListener('focus', wFocus)
        wFocus = null
        eventBus.$off('RELOAD_ACTIVE_CHAT')
        eventBus.$off('CHAT_SEARCH_USER_TAGS')
        eventBus.$off('CHAT_SEARCH_SELECT_CHAT')
        eventBus.$off('CHAT_OPEN_SEARCH')
        ChatEventBus.$off('arreaScroll')
        ChatEventBus.$off('arreaScrollDown')
        ChatEventBus.$off('newMessageArreaScroll')
        ChatEventBus.$off('CHAT_SHOW_NEW_MESSAGE', this.onNewMessageVisibilityCheck)
        this.CLEAR_CHAT()
        this.$store.commit('SHOW_FOOTER', true)
        this.$store.commit('SHOW_HEADER', true)
        wFocus = null
        this.initChat = true
        if(this.sidebarInfo)
            this.TOGGLE_INFO_SIDEBAR(false)
    }
}
</script>

<style lang="scss" scoped>
.chat_layer {
    min-height: 0;
}
.chat_content {
    min-height: 0;
}
.chat_body {
    min-height: 0;
}
.empty_chat_window_state{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    text-align: center;
    pointer-events: none;
    color: #6f7f94;
}
.empty_chat_window_state__title{
    max-width: 320px;
    margin-bottom: 8px;
    color: #2f3a4a;
    font-size: 18px;
    font-weight: 600;
}
.empty_chat_window_state__text{
    max-width: 340px;
    font-size: 14px;
    line-height: 1.45;
}
.chat_body[data-initializing="1"] {
    .chat__log,
    .bt_spinner,
    .reply_dummy {
        opacity: 0;
        pointer-events: none;
    }
}
.chat__log,
.bt_spinner,
.reply_dummy {
    transition: opacity .12s ease;
}
.chat_page_wrapper{
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    overflow: hidden;
    .chat_body{
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        height: 1px;
        overflow: auto;
        -webkit-overflow-scrolling: touch;
        transform: translateZ(0);
        position: relative;
        &::v-deep{
            .tp_spinner,
            .bt_spinner{
                .ant-spin{
                    background: #ffffff;
                    border-radius: 50%;
                    height: 35px;
                    width: 35px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,.15);
                }
            }
            .bt_spinner{
                width: 100%;
                z-index: 5;
                display: flex;
                justify-content: center;
            }
            .tp_spinner{
                position: fixed;
                top: 5px;
                left: 0;
                width: 100%;
                z-index: 5;
                display: flex;
                justify-content: center;
            }
        }
    }
    .chat_footer{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        flex-shrink: 0;
        transform: translateZ(0);
        padding-left: 15px;
        padding-right: 15px;
        padding-bottom: calc(10px + var(--safe-area-inset-bottom));
        &::v-deep{
            .chat_body__footer{
                box-shadow: 0 0 0 1px #e6e6e8;
                background: rgba(255,255,255,0.8);
                border-radius: 8px;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                .send_actions{
                    bottom: -4px;
                }
                &.reply_footer{
                    border-radius: 8px;
                }
                .left_actions{
                    padding-left: 0px;
                    bottom: -4px;
                    left: 0;
                }
            }
        }
    }
    .chat_messenger{
        height: 100%;
        position: relative;
        background-color: #f2f2f2;
        background-image: url('~@apps/vue2ChatComponent/assets/chat_bg.png');
        .chat_layer{
            height: 100%;
            box-sizing: border-box;
            padding-bottom: 0;
            --safe-area-inset-bottom: env(safe-area-inset-bottom);
            padding-bottom: calc(var(--safe-area-inset-bottom));
            display: flex;
            flex-direction: column;
        }
    }
    .chat_content{
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        height: 1px;
        overflow: hidden;
        .chat_body{
            padding: 5px 15px;
        }
    }
    .footer_dummy{
        position: relative;
    }
}
.message_entry{
    width: 100%;
}
.chat_unread_divider{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0 12px;
}
.chat_unread_divider__line{
    flex: 1 1 auto;
    height: 1px;
    background: rgba(29, 101, 192, 0.22);
}
.chat_unread_divider__label{
    flex: 0 0 auto;
    color: #1d65c0;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.message_entry_enter{
    animation-duration: 0.32s;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
    animation-fill-mode: both;
    will-change: transform, opacity;
}
.message_entry_enter_own{
    animation-name: msg-slide-in-right;
}
.message_entry_enter_other{
    animation-name: msg-slide-in-left;
}
@keyframes msg-slide-in-right {
    from {
        opacity: 0;
        transform: translate3d(18px, 0, 0);
    }
    to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}
@keyframes msg-slide-in-left {
    from {
        opacity: 0;
        transform: translate3d(-18px, 0, 0);
    }
    to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}
</style>
