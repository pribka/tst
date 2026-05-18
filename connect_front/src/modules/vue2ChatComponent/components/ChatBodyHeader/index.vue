<template>
    <div style="background: #f7f9fc;">
        <div class="chat_header flx justify-between items-center">
            <div class="chat_header_left truncate w-full">
                <div class="chat_info flx items-center truncate w-full">
                    <a-badge
                        v-if="isStandaloneChatWindow"
                        :count="getCounter && getCounter.count ? getCounter.count : 0"
                        class="back_badge"
                        :number-style="{
                            boxShadow: '0 0 0 0',
                            backgroundColor: primaryColor
                        }">
                        <a-button
                            type="flat_primary"
                            shape="circle"
                            flaticon
                            icon="fi-rr-menu-burger"
                            class="mr-2"
                            @click.stop="chatWindowSidebarVisible = true" />
                    </a-badge>
                    <a-badge 
                        v-if="isMobile && !isStandaloneChatWindow" 
                        :count="getCounter && getCounter.count ? getCounter.count : 0" 
                        class="back_badge"
                        :number-style="{
                            boxShadow: '0 0 0 0',
                            backgroundColor: primaryColor
                        }">
                        <a-button 
                            type="ui"
                            ghost
                            shape="circle"
                            icon="fi-rr-angle-left"
                            flaticon
                            class="mr-2"
                            @click="$router.push({ name: 'chat-contact' })" />
                    </a-badge>
                    <div 
                        v-if="!isMobile && activeChat" 
                        class="awatar_wrapper pr-2 cursor-pointer"
                        @click="openChatInfo()">
                        <template v-if="activeChat.is_public">
                            <a-avatar
                                v-if="activeChat.is_support"
                                class="chat_header__avatar--group"
                                :key="activeChat.chat_uid"
                                src="/img/support_avatar.jpg"
                                :size="38" />
                            <a-avatar
                                v-else
                                class="chat_header__avatar--group"
                                :key="activeChat.chat_uid"
                                :style="activeChat.color ? `backgroundColor:${activeChat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'"
                                :size="38">
                                {{ avatarText }}
                            </a-avatar>
                        </template>
                        <a-avatar
                            v-else
                            :key="activeChat.chat_uid"
                            :size="38"
                            :style="activeChat.color ? `backgroundColor:${activeChat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'"
                            :src="getAvatar">
                            {{ avatarText }}
                        </a-avatar>
                    </div>
                    <div
                        v-if="activeChat"
                        class="chat_name truncate flex items-center cursor-pointer" 
                        :class="isMobile && 'justify-center w-full text-center'"
                        @click="openChatInfo()">

                        <div class="truncate" :style="isMobile && 'line-height: 18px;'">
                            <div class="name font-bold truncate flex items-center">
                                <div 
                                    v-if="isMobile && activeChat" 
                                    class="awatar_wrapper cursor-pointer mr-1">
                                    <template v-if="activeChat.is_public">
                                        <a-avatar
                                            v-if="activeChat.is_support"
                                            class="chat_header__avatar--group"
                                            src="/img/support_avatar.jpg"
                                            :size="16" />
                                        <a-avatar
                                            v-else
                                            class="chat_header__avatar--group"
                                            :style="activeChat.color ? `backgroundColor:${activeChat.color}` : 'backgroundColor: #cccccc'"
                                            :size="16">
                                            {{ avatarText }}
                                        </a-avatar>
                                    </template>
                                    <a-avatar
                                        v-else
                                        :key="activeChat.chat_uid"
                                        :size="16"
                                        :style="activeChat.color ? `backgroundColor:${activeChat.color}` : 'backgroundColor: #cccccc'"
                                        :src="getAvatar">
                                        {{ avatarText }}
                                    </a-avatar>
                                </div>
                                <span>
                                    {{ name }}
                                </span>
                                <template v-if="activeChat.recipient && activeChat.recipient.is_support" >
                                    <span 
                                        class="ml-1 text-sm"
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                        :content="$t('chat.support')">
                                        <i class="fi fi-rr-headset"></i>
                                    </span>
                                </template>
                            </div>
                            <div
                                v-if="activeChat && activeChat.is_public && !activeTyping"
                                class="user_count truncate">
                                <template v-if="activeChat.is_support">
                                    {{ $t('chat.support_message') }}
                                </template>
                                <template v-else>{{ chatMember }}</template>
                            </div>
                            <template v-if="!activeTyping">
                                <div v-if="!activeChat.is_public" class="chat_status">
                                    <div v-if="isOnline">
                                        <span>{{ $t('chat.online') }}</span>
                                    </div>
                                    <template v-else>
                                        <template v-if="isOffline">
                                            <span v-if="fromNowDate">{{ $t('chat.was_online') }} {{ $moment(isOffline.date).format("Do MMMM HH:mm") }}</span>
                                            <span v-else>{{ $t('chat.was_online') }} {{ $moment(isOffline.date).fromNow() }}</span>
                                        </template>
                                        <div v-else-if="userLastActivity">
                                            <span v-if="fromNowDate">{{ $t('chat.was_online') }} {{ $moment(userLastActivity).format("Do MMMM HH:mm") }}</span>
                                            <span v-else>{{ $t('chat.was_online') }} {{ $moment(userLastActivity).fromNow() }}</span>
                                        </div>
                                    </template>
                                </div>
                            </template>
                            <template v-else>
                                <div class="text-xs font-light">
                                    <span class="text-xs font-light" v-if="!activeChat.is_public">
                                        {{ $t('chat.typing') }}
                                        <span class="print-dot font-light">  ....</span>
                                    </span>
                                    <span v-else>
                                        <span>{{ typingPublicText }}</span>
                                        <span class="print-dot">  ....</span>
                                    </span>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
            <template v-if="hasActiveChatActions">
                <div class="chat_header_right flx gap-2">
                    <template v-if="!isMobile">
                        <a-button
                            v-if="isHelpdescUser"
                            class="desktop_compact_action"
                            type="flat_primary"
                            icon="fi-rr-phone-flip"
                            :content="$t('chat.call')"
                            v-tippy
                            flaticon
                            :loading="callLoading"
                            @click="startChatCall()">
                            <span class="desktop_compact_action__text">{{ $t('chat.call') }}</span>
                        </a-button>
                        <a-button
                            class="desktop_compact_action"
                            type="flat_primary"
                            icon="fi-rr-video-camera"
                            :content="$t('chat.run_meeting')"
                            v-tippy
                            flaticon
                            :loading="meetingLoading"
                            @click="getMeeting(false)">
                            <span class="desktop_compact_action__text">{{ $t('chat.meeting') }}</span>
                        </a-button>
                    </template>
                    <a-button
                        v-if="!isMobile && activeChat.workgroup"
                        type="flat_primary"
                        @click="openWorkgroup()">
                        {{ activeChat.workgroup.is_project ? $t("chat.project") :  $t("chat.workgroup")}}
                    </a-button>
                    <RemoteAccessButton />
                    <AISummaryGenerate v-if="activeChat" :activeChat="activeChat" />
                    <a-button
                        v-if="!isMobile && activeChat && activeChat.chat_uid && !isStandaloneChatWindow"
                        type="flat_primary"
                        flaticon
                        v-tippy
                        :content="$t('chat.open_in_window')"
                        icon="fi-rr-arrow-up-right-from-square"
                        shape="circle"
                        @click="openChatWindow()" />
                    <a-button
                        type="flat_primary"
                        flaticon
                        v-tippy
                        :content="$t('chat.message_search')"
                        icon="fi-rr-search"
                        shape="circle"
                        @click="toggleSearchPanel()" />
                    <a-button
                        v-if="!isMobile"
                        type="flat_primary"
                        v-tippy
                        :content="$t('chat.chat_information')"
                        icon="fi-rr-sidebar-flip"
                        flaticon
                        shape="circle"
                        @click="openChatInfo()" />
                </div>
                <ChatInfoDrawer />
            </template>
        </div>
        <div v-if="showCompactWorkgroupLink" class="mobile_group_link" @click="openWorkgroup()">
            {{ activeChat.workgroup.is_project ? $t('chat.open_project') : $t('chat.open_team') }}
        </div>
        <div v-if="!isSearchOpen && isMobile && hasActiveChatActions" class="mobile_chat_actions">
            <button
                v-if="isHelpdescUser"
                type="button"
                class="mobile_chat_action"
                :disabled="callLoading"
                @click="startChatCall()">
                <i :class="callLoading ? 'fi fi-rr-spinner animate-spin' : 'fi fi-rr-phone-flip'" />
                <span>{{ $t('chat.call') }}</span>
            </button>
            <button
                type="button"
                class="mobile_chat_action"
                :disabled="meetingLoading"
                @click="getMeeting(false)">
                <i :class="meetingLoading ? 'fi fi-rr-spinner animate-spin' : 'fi fi-rr-video-camera'" />
                <span>{{ $t('chat.meeting') }}</span>
            </button>
        </div>
        <PinMessages
            v-if="!isSearchOpen && activeChat && activeChat.is_active && currentPin && currentPin.results.length"
            :messageSearch="replySearch"
            :currentPin="currentPin"
            :chatData="activeChat" />
        <SearchPanel v-if="isSearchOpen" :activeChat="activeChat" />
        <a-modal
            :visible="meetingModal"
            :footer="false"
            :title="$t('chat.invite_link')"
            @cancel="meetingModal = false">
            <template v-if="meetingModalData">
                <div class="flex justify-center">
                    <VueQRCodeComponent 
                        :text="meetingModalData.url2" />
                </div>
                <div class="url_input truncate" @click="meetingCopy()">
                    <div class="url_input__link truncate pr-3">{{ meetingModalData.url2 }}</div>
                    <a-button 
                        type="link"
                        size="small"
                        class="ant-btn-icon-only" 
                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"  
                        content="Скопировать ссылку">
                        <i class="fi fi-rr-copy-alt" />
                    </a-button>
                </div>
                <a-divider>или</a-divider>
                <div class="flex items-center justify-center mb-2">
                    <div 
                        class="share_btn" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}" 
                        :content="$t('chat.share_telegram')"
                        @click="tgShare(meetingModalData.url2)">
                        <img src="@/assets/images/telegram.svg" />
                    </div>
                    <div 
                        class="share_btn" 
                        v-tippy="{ inertia : true, duration : '[600,300]'}" 
                        :content="$t('chat.share_whatsapp')"
                        @click="wpShare(meetingModalData.url2)">
                        <img src="@/assets/images/WhatsApp.svg" />
                    </div>
                </div>
            </template>
        </a-modal>
        <DrawerTemplate
            v-if="isStandaloneChatWindow"
            :value="chatWindowSidebarVisible"
            placement="left"
            :width="380"
            :showHeader="false"
            :disabledBodyPadding="true"
            wrapClassName="chat_window_sidebar_drawer"
            @close="chatWindowSidebarVisible = false">
            <Sidebar />
            <template #footer>
                <div class="chat_window_sidebar_drawer__footer">
                    <a-button type="ui_ghost" block size="large" @click="chatWindowSidebarVisible = false">
                        {{ $t('close') }}
                    </a-button>
                </div>
            </template>
        </DrawerTemplate>
        <!--
        <a-modal
            :visible="meetingMobileModal"
            :footer="false"
            :title="$t('chat.meeting')"
            @cancel="meetingMobileModal = false">
            <a-button :loading="meetingLoading" block class="mb-3" size="large" type="primary" @click="getMeeting(false)">
                {{ $t('chat.open_meeting') }}
            </a-button>
            <a-button :loading="meetingLoading" block size="large" @click="getMeetingLink()">
                {{ $t('chat.invite_link') }}
            </a-button>
        </a-modal>-->
    </div>
</template>

<script>
import { mapMutations, mapState, mapGetters } from 'vuex'
import { declOfNum } from '../../utils'
import ChatEventBus from '../../utils/ChatEventBus.js'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { startMeetingCall } from '@apps/vue2MeetingComponent/utils/call'

const CHAT_WINDOW_CACHE_KEY = 'chat-window-cache'

export default {
    name: "ChatBodyHeader",
    components: {
        ChatInfoDrawer: () => import('./ChatInfoDrawer'),
        PinMessages: () => import('../PinMessages.vue'),
        SearchPanel: () => import('./SearchPanel.vue'),
        VueQRCodeComponent: () => import('vue-qrcode-component'),
        AISummaryGenerate: () => import('./AISummaryGenerate.vue'),
        RemoteAccessButton: () => import('./RemoteAccessButton.vue'),
        Sidebar: () => import('../Sidebar'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        replySearch: {
            type: Function,
            default: () => {}
        }
    },
    data(){
        return {
            typing: [],
            activeTyping: false,
            timeout: null,
            callLoading: false,
            meetingLoading: false,
            meetingData: null,
            meetingModalData: null,
            meetingModal: false,
            meetingMobileModal: false,
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ',
            chatWindowSidebarVisible: false
        }
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            user: state => state.user.user,
            pinMessage: state => state.chat.pinMessage,
            isMobile: state => state.isMobile,
            primaryColor: state => state.config.primaryColor
        }),
        ...mapGetters({
            chatMessages: 'chat/chatMessages',
            getReplyMessage: 'chat/replyMessage',
            getOnlineMember: 'chat/getStatusUser',
            getTyping: 'chat/getTyping'
        }),
        isHelpdescUser() {
            if (!this.activeChat)
                return false
            if(this.activeChat.is_public)
                return false
            /*const tariffSectionCodes = this.user?.tariff_section_codes
            if (!Array.isArray(tariffSectionCodes))
                return false

            return tariffSectionCodes.includes('request') || tariffSectionCodes.includes('help_desk')*/

            return true
        },
        isSearchOpen() {
            const uid = this.activeChat?.chat_uid
            if (!uid) return false
            return this.$store.state.chat.chatSearchPanelOpen?.[uid] === true
        },
        getCounter() {
            return this.$store.getters['navigation/getMenuCounter']('chat')
        },
        hasActiveChatActions() {
            return !!(this.activeChat && !this.activeChat.no_create)
        },
        showCompactWorkgroupLink() {
            return !!(
                !this.isSearchOpen
                && this.hasActiveChatActions
                && this.activeChat?.workgroup
                && (this.isMobile || this.isStandaloneChatWindow)
            )
        },
        avatarText() {
            if (this.activeChat) {
                if (this.activeChat.is_public) {
                    return this.activeChat.name.charAt(0).toUpperCase()
                } else {
                    const n = this.activeChat.name.split(' ')
                    return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}${n[2] ? n[2].charAt(0).toUpperCase() : ''}`
                }
            }
            return ''
        },
        mobileMenu() {
            if (this.isMobile)
                return () => import('./MobileMenu.vue')
            else
                return null
        },
        getAvatar() {
            if (this.activeChat) {
                if (this.activeChat.chat_author?.id !== this.user.id) {
                    return this.activeChat.chat_author?.avatar?.path || null
                }

                return this.activeChat.recipient?.avatar?.path || null
            }

            return null
        },
        chatMember() {
            return this.activeChat.member_count + ' ' +
            declOfNum(this.activeChat.member_count,
                [this.$t('chat.participant'), this.$t('chat.participant2'), this.$t('chat.participant3')])
        },
        name() {
            if(this.activeChat) {
                if(this.user.is_support) {
                    return this.activeChat.name
                } else {
                    if(this.activeChat.is_support)
                        return this.$t('chat.support_name', { name: this.appName })
                }
                return this.activeChat.name
            }   
            return ''
        },
        author() {
            return this.activeChat ? this.activeChat.chat_author : null
        },
        isOffline() {
            if (this.activeChat.recipient?.id)
                return this.$store.getters['user/getUserOffline'](this.activeChat.recipient.id)
            else
                return null
        },
        isOnline() {
            if (this.activeChat.recipient?.id)
                return this.$store.getters['user/getUserStatus'](this.activeChat.recipient.id)
            else
                return null
        },
        statusUser() {
            if (this.activeChat?.recipient) {
                return this.getOnlineMember(this.activeChat.recipient.id)
            }
            return false
        },
        userLastActivity() {
            if (this.activeChat?.recipient?.last_activity) {
                return this.activeChat.recipient.last_activity
            }
            return false
        },
        isAdmin() {
            if (this.author?.id === this.user.id)
                return true
            else
                return false
        },
        fromNowDate() {
            let now = this.$moment(new Date()); // today's date
            let end = this.$moment(this.statusUser.last_activity); // another date
            let duration = this.$moment.duration(now.diff(end));
            let hours = duration.asHours();

            return hours > 23 ? true : false
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        currentPin() {
            if (this.activeChat && this.pinMessage[this.activeChat.chat_uid])
                return this.pinMessage[this.activeChat.chat_uid]
            else
                return false
        },
        typingPublicText() {
            let text;
            if (this.typing.length === 1) {
                text = `${this.typing[0]} ${this.$t('chat.typing')}`
            } else if (this.typing.length === 2) {
                text = `${this.typing[0]}, ${this.typing[1]} ${this.$t('chat.typing2')}`
            } else {
                text = `${this.typing[0]}, ${this.typing[1]} ${this.$t('chat.typing3')} ${this.typing.length - 2} ${this.$t('chat.typing4')}`
            }

            return text
        }
    },
    watch: {
        typing(){
            if(this.typing.length === 0){
                this.activeTyping = false
            }
        },
        activeChat() {
            this.meetingDat = null
            this.meetingModalData = null
        },
        '$route.params.id'() {
            if (this.isStandaloneChatWindow) {
                this.chatWindowSidebarVisible = false
            }
        },
        '$route.query.open_sidebar'(value) {
            if (this.isStandaloneChatWindow && value === '1') {
                this.chatWindowSidebarVisible = true
            }
        }
    },
    sockets: {
        chat_typing({ data }) {
            const payload = data || {}
            const activeChat = this.activeChat
            if (!payload.chat_uid || !activeChat || !activeChat.chat_uid || activeChat.no_create) return

            if(String(payload.chat_uid) === String(activeChat.chat_uid)){
                const find = this.typing.find(el=> el === payload.user)

                if(find === undefined){
                    this.typing.push(payload.user)
                    this.timeout = setTimeout(() => {
                        this.typing = this.typing.filter(el => el !== payload.user)

                    }, 1500);
                } else {
                    clearTimeout(this.timeout)
                    this.timeout = setTimeout(() => {
                        this.typing = this.typing.filter(el => el !== payload.user)

                    }, 1500);
                }

                this.activeTyping = true
            }
        }
    },
    methods: {
        ...mapMutations({
            TOGGLE_INFO_SIDEBAR: 'chat/TOGGLE_INFO_SIDEBAR',
            TOGGLE_TASKS_SIDEBAR: 'chat/TOGGLE_TASKS_SIDEBAR',
            SET_CHAT_MEMBERS: 'chat/SET_CHAT_MEMBERS',
            CLEAR_CHAT: 'chat/CLEAR_CHAT'
        }),
        toggleSearchPanel() {
            this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat?.chat_uid })
        },
        wpShare(link) {
            window.open(`https://wa.me/?text=${encodeURIComponent(this.$t('chat.invite_link') + ' - ' + link)}`, '_blank').focus()
        },
        tgShare(link) {
            window.open(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${this.$t('chat.invite_link')}`, '_blank').focus()
        },
        meetingCopy() {
            try {
                navigator.clipboard.writeText(this.meetingModalData.url2)
                this.$message.success(this.$t('chat.linkCopied'))
            } catch(e) {
                console.log(e)
            }
        },
        async startChatCall() {
            if (!this.activeChat?.chat_uid)
                return

            const targetUserId = this.activeChat?.recipient?.id
                || (this.activeChat?.chat_author?.id !== this.user?.id ? this.activeChat?.chat_author?.id : null)

            await startMeetingCall({
                payload: {
                    chat_uid: this.activeChat.chat_uid
                },
                context: {
                    chatUid: this.activeChat.chat_uid,
                    targetUserId
                },
                setLoading: value => {
                    this.callLoading = value
                }
            })
        },
        async getMeetingLink() {
            if(!this.meetingModalData) {
                try {
                    this.meetingLoading = true
                    const { data } = await this.$http.get(`/chat/${this.activeChat.chat_uid}/vks/`)
                    if(data) {
                        this.meetingModalData = data
                        this.meetingData = data
                        this.meetingCopy()
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.meetingLoading = false
                }
            } else{
                this.meetingCopy()
            }
            this.meetingMobileModal = false
        },
        async sendMeetingMessage(meeting) {
            try {
                const author = JSON.parse(JSON.stringify(this.$store.state.user.user))
                const chatUid = this.activeChat.chat_uid
                const data = {
                    message_author: {
                        ...author,
                        full_name: author.first_name + ' ' + author.last_name
                    },
                    text: `${this.$t('chat.meeting_chat_message')}\n${meeting.url}`,
                    chat: chatUid,
                    chat_uid: chatUid,
                    is_system: false,
                    is_pinned: false,
                    is_deleted: false,
                    message_reply: null,
                    attachments: []
                }
                ChatEventBus.$emit('create_meeting_message', data)
            } catch (error) {
                errorHandler({error})
            }
        },
        async getMeeting(isModal) {
            if(!this.meetingData || !this.meetingModalData) {
                try {
                    this.meetingLoading = true
                    const { data } = await this.$http.get(`/chat/${this.activeChat.chat_uid}/vks/`)
                    if(data) {
                        this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.activeChat.chat_uid, value: false })
                        this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.activeChat.chat_uid)
                        if(isModal) { 
                            this.meetingModalData = data
                            this.meetingData = data
                            this.meetingModal = true
                        } else {
                            this.meetingData = data
                            this.meetingModalData = data
                            if(this.meetingData?.url) {
                                window.open(this.meetingData.url, '_blank')
                            }
                        }
                        if(data.url)
                            this.sendMeetingMessage(data)
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.meetingLoading = false
                }
            } else{
                if(isModal) {
                    this.meetingModal = true
                } else {
                    if(this.meetingData?.url) {
                        window.open(this.meetingData.url, '_blank')
                    }
                }
            }
            this.meetingMobileModal = false
        },
        openWorkgroup(){
            let query = {...this.$route.query}
            if(this.activeChat.workgroup.is_project){
                query['viewProject'] = this.activeChat.workgroup.uid
            } else {
                query['viewGroup'] = this.activeChat.workgroup.uid
            }
            this.$router.replace({query})
        },
        showDeleteModal() {
            this.$confirm({
                title: this.$t('chat.chat_delete'),
                content: this.$t('chat.chat_delete_text'),
                okText: this.$t('chat.yes'),
                okType: 'danger',
                cancelText: this.$t('chat.no'),
                onOk() {
                    // console.log('OK');
                },
                onCancel() {
                    // console.log('Cancel');
                }
            })
        },
        openChatInfo() {
            this.TOGGLE_INFO_SIDEBAR(true)
        },
        openChatWindow() {
            if (!this.activeChat?.chat_uid) return

            this.persistChatWindowCache()

            const routeData = this.$router.resolve({
                name: 'chat-window',
                params: { id: this.activeChat.chat_uid }
            })

            const features = [
                'popup=yes',
                'width=480',
                'height=820',
                'left=120',
                'top=80',
                'menubar=no',
                'toolbar=no',
                'location=no',
                'status=no',
                'resizable=yes',
                'scrollbars=no'
            ].join(',')

            const openedWindow = window.open(routeData.href, 'chat-window-standalone', features)
            if (openedWindow) {
                openedWindow.focus()
                this.closeChatInCurrentWindow()
            }
        },
        persistChatWindowCache() {
            if (typeof window === 'undefined') return

            try {
                const chatState = this.$store.state.chat || {}
                const payload = {
                    chatList: Array.isArray(chatState.chatList) ? chatState.chatList : [],
                    chatListNext: !!chatState.chatListNext,
                    chatListPage: Number(chatState.chatListPage || 0),
                    contactList: Array.isArray(chatState.contactList) ? chatState.contactList : [],
                    contactListNext: !!chatState.contactListNext,
                    contactListPage: Number(chatState.contactListPage || 0),
                    helpDeskList: Array.isArray(chatState.helpDeskList) ? chatState.helpDeskList : [],
                    helpDeskNext: !!chatState.helpDeskNext,
                    helpDeskPage: Number(chatState.helpDeskPage || 0),
                    chatDrafts: chatState.chatDrafts || {},
                    sidebarActiveTab: Number(chatState.sidebarActiveTab || 1),
                    savedAt: Date.now()
                }

                window.localStorage.setItem(CHAT_WINDOW_CACHE_KEY, JSON.stringify(payload))
            } catch (e) {
                // noop
            }
        },
        closeChatInCurrentWindow() {
            this.CLEAR_CHAT()

            if (this.$route?.name === 'chat') {
                const nextQuery = { ...(this.$route.query || {}) }
                delete nextQuery.chat_id
                delete nextQuery.message_id
                delete nextQuery.chat_uid

                this.$router.replace({
                    name: 'chat',
                    query: nextQuery
                }).catch(() => {})
                return
            }

            if (this.$route?.name === 'chat-body') {
                this.$router.replace({ name: 'chat-contact' }).catch(() => {})
            }
        }
    },
    mounted() {
        if (this.isStandaloneChatWindow && this.$route.query?.open_sidebar === '1') {
            this.chatWindowSidebarVisible = true
        }

        eventBus.$on('create_meeting', () => {
            if(this.activeChat) {
                this.getMeeting(false)
            }
        })
        eventBus.$on('chat_info', () => {
            if(this.activeChat) {
                this.openChatInfo()
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('create_meeting')
        eventBus.$off('chat_info')
    }
}
</script>
<style scoped lang="scss">
::v-deep(.chat_window_sidebar_drawer .ant-drawer-body){
    padding: 0;
    height: 100%;
}
::v-deep(.chat_window_sidebar_drawer .ant-drawer-content),
::v-deep(.chat_window_sidebar_drawer .ant-drawer-wrapper-body){
    height: 100%;
}
::v-deep(.chat_window_sidebar_drawer .ant-drawer-footer){
    padding: 12px 16px;
    border-top: 1px solid var(--borderColor);
    background: #fff;
}
::v-deep(.chat_window_sidebar_drawer .chat_contact.active){
    border-radius: 8px;
    overflow: hidden;
}
.chat_window_sidebar_drawer__footer{
    width: 100%;
}
.share_or{
    text-align: center;
    color: #888;
    margin-bottom: 10px;
}
.share_btn{
    cursor: pointer;
    width: 35px;
    height: 35px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #eff2f5;
    border-radius: 50%;
    img{
        max-width: 18px;
        height: auto;
    }
    &:not(:last-child){
        margin-right: 8px;
    }
}
.url_input{
    margin-top: 20px;
    background-color: #f7f9fc;
    overflow: hidden;
    width: 100%;
    display: flex;
    align-items: center;
    padding-left: 15px;
    padding-right: 15px;
    border-radius: var(--borderRadius);
    cursor: pointer;
    user-select: none;
    min-height: 32px;
    margin-bottom: 10px;
}
.back_badge{
    &::v-deep{
        .ant-badge-count{
            font-size: 10px;
            min-width: 17px;
            height: 17px;
            line-height: 17px;
            top: 10px;
            right: 9px;
        }
    }
}
.chat_header__avatar--group{
    border-radius: 12px !important;
}
::v-deep(.chat_header__avatar--group.ant-avatar),
::v-deep(.chat_header__avatar--group img){
    border-radius: 12px !important;
}
.mobile_group_link{
    border-bottom: 1px solid var(--borderColor);
    cursor: pointer;
    padding: 5px 15px;
    text-align: center;
    font-size: 14px;
}
.mobile_chat_actions{
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid var(--borderColor);
}
.mobile_chat_action{
    appearance: none;
    border: 0;
    border-radius: 0;
    background: rgb(247, 249, 252);
    flex: 1 1 0;
    min-width: 0;
    padding: 9px 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 14px;
    cursor: pointer;
    color: inherit;
    &:disabled{
        cursor: default;
        opacity: .7;
    }
    &:not(:last-child){
        border-right: 1px solid var(--borderColor);
    }
    i{
        font-size: 14px;
        line-height: 1;
    }
}
@media (min-width: 769px) and (max-width: 1440px) {
    .desktop_compact_action{
        width: 40px;
        height: 40px;
        min-width: 40px;
        padding: 0;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        &__text{
            display: none;
        }
        &::v-deep{
            i{
                margin-right: 0;
            }
        }
    }
}
.print-dot {
    display:inline-block;
    font-size: 1rem;
    clip-path: inset(0 2ch 0 0);
    animation: l 2s steps(4) infinite;
}

.chat_name{
    padding: 0 8px;
    .name{
        font-size: 14px;
    }
    .chat_status{
        font-size: 12px;
        font-weight: 300;
    }
}

@keyframes l {
  to {
    clip-path: inset(0 -1ch 0 0)
  }
}

</style>

<style lang="scss">
.chat_window_sidebar_drawer {
    .chat_contact.active {
        background: var(--primaryHover);
        border-radius: 8px;
        overflow: hidden;
    }
}
</style>
