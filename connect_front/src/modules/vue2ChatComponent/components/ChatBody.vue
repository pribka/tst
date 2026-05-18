<!--ChatBody-->
<template>
    <div class="chat_body">
        <template v-if="activeChat">
            <div class="hfl chat_body__wrapper">
                <ChatBodyHeader :replySearch="replySearch" />
                <div
                    ref="chatBodyArea"
                    @scroll="scrollAction" 
                    @wheel.passive="handleUserScrollInteraction"
                    @touchmove.passive="handleUserScrollInteraction"
                    :class="currentPin && currentPin.results.length && 'open_pin'"
                    :data-initializing="initialViewportReady ? '0' : '1'"
                    class="chat_body__messages py-2 px-2 lg:px-3"
                    @click="clickChatBody()">
                    
                    <template v-if="activeChat.is_active">
                        <div
                            v-if="loading && !topInfiniteEnabled"
                            class="top_inf_sp top_inf_sp_static">
                            <a-spin />
                        </div>

                        <infinite-loading
                            v-if="topInfiniteEnabled && !infinitePaused"
                            v-bind:distance="5"
                            :identifier="`${ activeChat.chat_uid }_top_${ topInfiniteKey }`"
                            direction="top"
                            @infinite="upScrollHandler">
                            <template #spinner>
                                <div class="top_inf_sp"><a-spin  v-show="loading" /></div>
                            </template>
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
                                    :ref="'msg-' + index"
                                    :replySearch="replySearch"
                                    :user="user"
                                    useReact
                                    :resizeEvent="resizeEvent"
                                    :messageItem="item" />
                            </div>
                        </div>

                        <infinite-loading
                            v-if="bottomInfiniteEnabled && !infinitePaused && !isSearching && canLoadBottomMore"
                            v-bind:distance="10"
                            :identifier="bottomInfiniteIdentifier"
                            @infinite="downScrollHandler">
                            <div slot="spinner">
                                <div class="bt_inf_sp"><a-spin /></div>
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
                </div>
                <ChatFooter
                    v-show="!isSearching"
                    v-if="activeChat.is_active"
                    :showDownBtn="showDownBtnSync"
                    :missedCount="missedCount"
                    :loadingDown="loadingDown"
                    :downAction="downAction"
                    :resizeEvent="resizeEvent"
                    ref="ChatFooter" />
                <!--<div class="chat_drawer"></div>-->
            </div>
        </template>

        <div v-if="!activeChat" class="dialog_close h-full flex flex-col items-center justify-center">
            <a-spin :spinning="dialogLoading">
                <div class="empty_chat">
                    <div class="mb-4">
                        <i class="fi fi-rr-comment blue_color"></i>
                    </div>
                    <div>
                        <span v-html="$t('chat.select_chat')"></span>
                        <span class="cursor-pointer create" @click="$store.commit('chat/TOGGLE_CREATE_CHAT', true)">{{$t('chat.create_new_chat')}}</span>
                    </div>
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
import ChatEventBus from '../utils/ChatEventBus'
import eventBus from '@/utils/eventBus'
import { mapState, mapGetters, mapActions, mapMutations } from 'vuex'
import { changePageTitle } from '@/utils/utils.js'
import { pauseAllVoicePlayback } from '@/utils/voicePlayback'
const key = 'searchKey'
export default {
    name: "ChatBody",
    components: {
        ChatBodyHeader: () => import('./ChatBodyHeader'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        ChatMessage: () => import('./ChatMessage/index.vue'),
        ChatFooter: () => import('./ChatFooter')
    },
    beforeRouteLeave(to, from, next) {
        Promise.resolve(this.$refs.ChatFooter?.persistDraftByChat?.())
            .catch(() => {})
            .finally(() => next())
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            user: state => state.user.user,
            pinMessage: state => state.chat.pinMessage,
            dialogLoading: state => state.chat.dialogLoading,
            messageListPrev: state => state.chat.messageListPrev,
            primaryColor: state => state.config.primaryColor
        }),
        ...mapGetters({
            chatMessages: 'chat/chatMessages',
            getReplyMessage: 'chat/replyMessage',
            getCountMessages: 'chat/getCountMessages',
            getChatHistoryState: 'chat/chatHistoryState'
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
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
        missedCount(){
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
            const key = this.searchMoreKey
            if (!key) return false
            return this.$store.state.chat.chatSearchMoreScrollDoneByKey?.[key] === true
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
        currentHistoryState() {
            return this.activeChat?.chat_uid
                ? this.getChatHistoryState(this.activeChat.chat_uid)
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
            downLoading: false,
            emptyMessage: false,
            showDownBtn: false,
            loadingDown: false,
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
            firstScrollDone: {},
            replyAnchorUid: null,
            searchAutoScrollDone: {},
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
                    await this.ensureScrollBottom()
                    this.topInfiniteKey += 1
                })
            }
        },
        searchMessages: {
            deep: true,
            handler(val) {
                if (!this.isSearching) return

                const key = this.searchAutoKey
                if (!key) return

                const newLen = Array.isArray(val?.value) ? val.value.length : 0
                if (this.searchAutoScrollDone[key] === true) return

                if (newLen > 0) {
                    this.$nextTick(async () => {
                        await this.ensureScrollBottom()
                        this.topInfiniteKey += 1
                        this.$set(this.searchAutoScrollDone, key, true)
                    })
                }
            }
        },
        displayMessageIds(newIds, oldIds) {
            this.handleNewMessageAnimations(newIds, oldIds)
        },
        activeChat(val, oldVal) {
            if (oldVal?.chat_uid && oldVal.chat_uid !== val?.chat_uid) {
                pauseAllVoicePlayback({ reason: 'chat-switch', broadcast: false })
            }

            if (!val) {
                pauseAllVoicePlayback({ reason: 'chat-cleared', broadcast: false })
                this.initialViewportReady = true
            }

            clearTimeout(this.readProgressTimer)
            this.readProgressTimer = null
            this.readProgressSending = false
            this.pendingReadCreated = null

            this.resetMessageAnimations()
            if(val) {                
                const hasLocalMessages = !!this.chatMessages(val.chat_uid)?.value?.length
                this.topInfiniteKey += 1
                this.topInfiniteEnabled = false
                this.bottomInfiniteEnabled = false
                this.initialViewportReady = hasLocalMessages
                this.hasUserScrollInteraction = false
                this.showDownBtn = false
                this.missedCountLocal = 0
                this.firstMissedUid = null
                this.runWithInfiniteSuppressed(async () => {
                    this.scrollAction()
                })
                ChatEventBus.$emit('inputFocus')

                const chatName = val?.name || ""
                changePageTitle(`${this.$t('chat.title')}: ${chatName}`)
                if (!Number(val?.new_message_count || 0)) {
                    this.scheduleReadProgressSync()
                }

                if (this.isSearching) {
                    return
                }

                if (val.no_create) {
                    this.loading = false
                    this.infinitePaused = false
                    this.topInfiniteEnabled = false
                    this.bottomInfiniteEnabled = false
                    this.initialViewportReady = true
                    return
                }

                if(this.$route.query?.message_id) {
                    this.infinitePaused = true
                    this.replySearch({ message_uid: this.$route.query.message_id })
                    return
                }

                this.ensureActiveChatData(val.chat_uid)
            }
        }
    },
    methods: {
        ...mapActions({
            getMessageScroll: 'chat/getMessageScroll',
            getMessage: 'chat/getMessage',
            getMessageDownScroll: 'chat/getMessageDownScroll',
            getPinMessage: 'chat/getPinMessage',
            getInitialChatMessages: 'chat/getInitialChatMessages',
            getHistoryAfterMessages: 'chat/getHistoryAfterMessages',
            updateReadProgress: 'chat/updateReadProgress'
        }),
        ...mapMutations({
            clearMessage: "chat/clearMessage",
            setScrollToped: "chat/setScrollToped",
            clearChat: 'chat/CLEAR_CHAT'
        }),
        getAnchorSnapshot() {
            const container = this.$refs['chatBodyArea']
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
        restoreAnchorSnapshot(snapshot) {
            const container = this.$refs['chatBodyArea']
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
        async ensureActiveChatData(chat_uid) {
            if (!chat_uid) return

            const loadKey = ++this.activeChatLoadKey
            // Если в чате есть unread, открываем не обычный хвост,
            // а специальный unread-entry срез от первого непрочитанного.
            const useUnreadHistory = Number(this.activeChat?.new_message_count || 0) > 0
            const existingMessages = this.chatMessages(chat_uid)
            const shouldLoadInitialMessages = !existingMessages || useUnreadHistory

            try {
                this.infinitePaused = true
                this.topInfiniteEnabled = false
                this.bottomInfiniteEnabled = false
                if (!shouldLoadInitialMessages) {
                    this.initialViewportReady = true
                }
                this.loading = shouldLoadInitialMessages

                if (shouldLoadInitialMessages) {
                    await this.getInitialChatMessages({
                        chat_uid,
                        useUnreadHistory
                    })
                }

                if (loadKey !== this.activeChatLoadKey || this.activeChat?.chat_uid !== chat_uid) return

                if (!this.pinMessage?.[chat_uid]) {
                    await this.getPinMessage({ chat_uid, page_size: 10, page: 1 })
                }

                if (loadKey !== this.activeChatLoadKey || this.activeChat?.chat_uid !== chat_uid) return

            } finally {
                if (loadKey === this.activeChatLoadKey) {
                    this.loading = false
                    this.infinitePaused = false
                    this.topInfiniteKey += 1
                    if (this.activeChat?.chat_uid === chat_uid) {
                        this.$nextTick(async () => {
                            await new Promise(resolve => requestAnimationFrame(() => resolve()))
                            await this.afterChatFirstRender()
                        })
                    }
                }
            }
        },
        async ensureScrollBottom() {
            await this.runWithInfiniteSuppressed(async () => {
                let tries = 16
                let stable = 0
                let lastHeight = -1

                await new Promise(resolve => {
                    const step = () => {
                        if (this.hasUserScrollInteraction) return resolve()
                        const container = this.$refs['chatBodyArea']
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
        async selectChat(chat_uid) {
            if(this.isMobile) {
                this.$router.push({
                    name: 'chat-body',
                    params: {
                        id: chat_uid
                    }})
            } else {
                const chat = await this.$store.dispatch('chat/getCurrentChat', chat_uid)
                if (!chat || chat.chat_uid !== chat_uid) return

                if(this.activeChat && !this.activeChat.is_public)
                    this.$socket.client.emit('chat_status_user',
                        {chat_uid: this.activeChat.chat_uid, user_uid: this.activeChat.recipient.id})

                const query = JSON.parse(JSON.stringify(this.$route.query))
                if(query?.chat_id !== chat_uid) {
                    query.chat_id = chat_uid
                    this.$router.push({query})
                }
            }
        },
        clickChatBody() {
            if(!this.isMobile)
                ChatEventBus.$emit('inputFocus')
        },
        resizeEvent() {
            this.$nextTick(() => {
                if (this.replyAnchorUid) return
                if(this.$refs['chatBodyArea']) {
                    const currScroll = this.$refs['chatBodyArea'].scrollHeight - this.$refs['chatBodyArea'].scrollTop,
                        checkScroll = this.$refs['chatBodyArea'].clientHeight + 250

                    if(currScroll < checkScroll) {
                        this.scrollDown()
                    }
                }
            })
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
            if(this.missedCount > 0){ 
                this.scheduleReadProgressSync()
            }
        },
        scrollAction(){
            this.$nextTick(() => {
                const container = this.$refs['chatBodyArea']
                if(container){ 
                    const scrollTop = container.scrollTop
                    const isNearTop = scrollTop <= 80
                    if (isNearTop && !this.hasUserScrollInteraction && !this.suppressInfiniteActivation && this.initialViewportReady) {
                        this.handleUserScrollInteraction()
                    }

                    this.scheduleReadProgressSync()
                    const currScroll = container.scrollHeight - container.scrollTop,
                        checkScroll = container.clientHeight + 100

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
        async scrollToMessageUid(message_uid) {
            await this.$nextTick()
            await new Promise(resolve => requestAnimationFrame(() => resolve()))
            await new Promise(resolve => requestAnimationFrame(() => resolve()))

            const container = this.$refs['chatBodyArea']
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
                this.$message.loading({ content: `${this.$t('chat.loading')}...`, key })

                if (this.$route.query?.message_id) {
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

                if (!localMessage) {
                    await this.$store.dispatch('chat/searchMessages', message)
                }

                await this.$nextTick()
                await new Promise(r => requestAnimationFrame(r))
                await new Promise(r => requestAnimationFrame(r))

                const doScroll = async () => {
                    const container = this.$refs['chatBodyArea']
                    const elem = document.getElementById(`message_${message.message_uid}`)
                    if (!container || !elem) return false

                    const containerRect = container.getBoundingClientRect()
                    const elemRect = elem.getBoundingClientRect()

                    const elemTopInContainer =
                    (elemRect.top - containerRect.top) + container.scrollTop

                    const centerOffset =
                    (container.clientHeight / 2) - (elemRect.height / 2)

                    const targetTop = Math.max(0, elemTopInContainer - centerOffset)

                    container.scrollTo({ top: targetTop, behavior: 'smooth' })
                    return true
                }

                let ok = await doScroll()

                if (!ok) {
                    setTimeout(async () => {
                        await doScroll()
                    }, 300)
                } else {
                    let tries = 12
                    let lastTop = -1

                    while (tries > 0) {
                        await new Promise(r => requestAnimationFrame(r))

                        const container = this.$refs['chatBodyArea']
                        if (!container) break

                        const diff = Math.abs(container.scrollTop - lastTop)
                        lastTop = container.scrollTop

                        if (diff < 2) break
                        tries--
                    }
                }

                const elem = document.getElementById(`message_${message.message_uid}`)
                if (elem && !elem.classList.contains('flashing')) {
                    elem.classList.add('flashing')
                    setTimeout(() => {
                        elem.classList.remove('flashing')
                    }, 1200)
                }

                ChatEventBus.$emit('CLOSE_PIN_DRAWER')
            } catch (e) {
                this.infinitePaused = false
                this.topInfiniteKey += 1
            } finally {
                this.scrollBlock = false
                this.searchMessage = false
                this.$message.destroy()

                setTimeout(() => {
                    this.infinitePaused = false
                    this.topInfiniteKey += 1
                }, 200)

                setTimeout(() => {
                    this.replyAnchorUid = null
                }, 1500)
            }
        },
        isNearBottom(extra = 300) {
            const c = this.$refs.chatBodyArea
            if (!c) return false
            const gap = c.scrollHeight - c.scrollTop - c.clientHeight
            return gap <= extra
        },
        scrollDown() {
            if (this.scrollBlock) return
            if (this.replyAnchorUid) return
            this.$nextTick(() => {
                if (this.$refs['chatBodyArea']) {
                    this.runWithInfiniteSuppressed(async () => {
                        const container = this.$refs['chatBodyArea']
                        if (!container) return
                        container.scrollTop = container.scrollHeight
                    })
                }
            })
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
        async scrollTestPrev(){
            if (this.isUnreadEntryMode) return
            if(this.messageListPrev){
                await this.getMessage({refresh: true})
            }
        },
        async downScrollHandler($state) {
            if (this.isSearching) {
                $state.complete()
                return
            }
            if (this.searchMessage) {
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

            if (this.messages) {
                if (this.messages.prev && this.messages.prev.length) {
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
            if (this.infinitePaused) {
                $state.complete()
                return
            }

            if (!this.topInfiniteEnabled || !this.hasUserScrollInteraction) {
                $state.complete()
                return
            }

            if (this.loading) {
                $state.loaded()
                return
            }

            if (this.isSearching) {
                const uid = this.activeChat.chat_uid
                const bucket = this.searchMessages

                if (bucket?.hasMore && !bucket.loading) {
                    const c = this.$refs.chatBodyArea
                    const beforeH = c ? c.scrollHeight : 0
                    const beforeTop = c ? c.scrollTop : 0

                    try {
                        this.loading = true
                        await this.$store.dispatch('chat/searchChatMessagesMore', uid)
                        $state.loaded()
                        if (!this.searchMoreScrollDone && this.searchMoreKey) {
                            this.$store.commit('chat/SET_CHAT_SEARCH_MORE_SCROLL_DONE', {
                                key: this.searchMoreKey,
                                value: true
                            })

                            this.$nextTick(() => {
                                const c2 = this.$refs.chatBodyArea
                                if (!c2) return
                                const afterH = c2.scrollHeight
                                const diff = afterH - beforeH
                                c2.scrollTop = beforeTop + diff
                            })
                        }
                    } catch (e) {
                        $state.complete()
                    } finally {
                        this.loading = false
                    }
                    return
                }

                $state.complete()
                return
            }

            if (this.messages && !this.loading) {
                if (this.messages.next && this.messages.next.length) {
                    const snapshot = this.getAnchorSnapshot()

                    try {
                        this.loading = true
                        await this.getMessageScroll()

                        await this.$nextTick()
                        await new Promise(r => requestAnimationFrame(r))

                        this.restoreAnchorSnapshot(snapshot)

                        if (this.messages.status)
                            $state.loaded()
                        else
                            $state.complete()
                    } finally {
                        this.loading = false
                    }
                    return
                }

                if (this.messages.next === undefined) {
                    this.clearMessage()
                    await this.getMessage()
                    await this.getPinMessage({ page_size: 10, page: 1 })
                    await this.afterChatFirstRender()
                    if (this.messages && this.messages.status)
                        $state.loaded()
                    else
                        $state.complete()
                    return
                }

                $state.complete()
                return
            }

            try {
                this.loading = true
                ChatEventBus.$emit('inputFocus')
                await this.getMessage()
                await this.getPinMessage({ page_size: 10, page: 1 })
                await this.afterChatFirstRender()
                if (this.messages && this.messages.status)
                    $state.loaded()
                else
                    $state.complete()
            } finally {
                this.loading = false
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
        eventBus.$on('CHAT_OPEN_SEARCH', () => {
            this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat?.chat_uid })
            if(!this.isSearchOpen) {
                this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat?.chat_uid, value: false })
                this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.activeChat?.chat_uid)
            }
        })
        eventBus.$on('CHAT_SEARCH_USER_TAGS', () => {
            if(this.$route.query?.message_id) {

                this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat.chat_uid, value: false })
                this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.activeChat.chat_uid)

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
            this.$nextTick(() => {
                if (this.isNearBottom()) {
                    this.scrollDown()
                }
            })
        })
        ChatEventBus.$on('newMessageArreaScroll', () => {
            if (this.isNearBottom()) {
                this.scrollDown()
            }
        })
        ChatEventBus.$on('arreaScrollDown', (clear = true) => {
            this.$nextTick(() => {
                this.scrollDown()
            })
            if(clear)
                this.clearCount()
        })
        ChatEventBus.$on('CHAT_SHOW_NEW_MESSAGE', this.onNewMessageVisibilityCheck)
        this.$store.dispatch('chat/getReactions')
    },
    beforeDestroy() {
        pauseAllVoicePlayback({ reason: 'chat-body-destroy', broadcast: false })
        this.resetMessageAnimations()
        clearTimeout(this.readProgressTimer)
        eventBus.$off('CHAT_SEARCH_USER_TAGS')
        eventBus.$off('CHAT_SEARCH_SELECT_CHAT')
        eventBus.$off('CHAT_OPEN_SEARCH')
        ChatEventBus.$off('arreaScrollDown')
        ChatEventBus.$off('arreaScroll')
        ChatEventBus.$off('newMessageArreaScroll')
        ChatEventBus.$off('CHAT_SHOW_NEW_MESSAGE', this.onNewMessageVisibilityCheck)
        this.clearChat()
    }
}
</script>

<style lang="scss" scoped>
.bt_inf_sp,
.top_inf_sp{
    &::v-deep{
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
}

.chat_body__messages[data-initializing="1"]{
    .chat__log,
    .bt_inf_sp,
    .reply_dummy{
        opacity: 0;
        pointer-events: none;
    }
}

.chat__log,
.bt_inf_sp,
.reply_dummy{
    transition: opacity .12s ease;
}
.bt_inf_sp{
    position: absolute;
    bottom: 70px;
    left: 50%;
    margin-left: -35px;
    width: 35px;
    z-index: 5;
    display: flex;
    justify-content: center;
    align-items: center;
}
.top_inf_sp{
    position: absolute;
    top: 6px;
    left: 50%;
    margin-left: -35px;
    width: 35px;
    z-index: 5;
    display: flex;
    justify-content: center;
    align-items: center;
}
.top_inf_sp_static{
    margin-left: -17.5px;
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
