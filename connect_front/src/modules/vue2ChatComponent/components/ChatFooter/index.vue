<template>
    <div class="chat_body__footer relative" :class="[replyMessage && 'reply_footer']" ref="chatFooter">
        <a-badge
            class="scrol_down_btn"
            :class="isMobile && 'is_mobile'"
            v-show="showDownBtn" 
            :count="missedCount"
            :number-style="{ backgroundColor: '#1d65c0' }" >
            <a-button 
                @click="downAction"  
                :loading="loadingDown"
                flaticon
                class="flex items-center justify-center"
                shape="circle" 
                style="min-height: 42px;min-width: 42px;font-size: 22px;"
                icon="fi-rr-angle-small-down" 
                size="large" />
        </a-badge>
        <ReplyMessage />
        <EditBlock :message="message" :closeEdit="closeEdit" :activeChat="activeChat" />
        <div class="input_wrapper" :class="{ 'input_wrapper--standalone': isStandaloneChatWindow }">
            <div v-if="!voiceRecording && !voiceUploading" class="left_actions">
                <template v-if="isMobile">
                    <button
                        type="button"
                        class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost"
                        v-tippy
                        :content="$t('chat.select_file')"
                        @click="attachmentDrawerVisible = true">
                        <i class="fi fi-rr-clip"></i>
                    </button>
                    <ActivityDrawer
                        :vis="attachmentDrawerVisible"
                        :hardZIndex="6000"
                        useVis
                        :cDrawer="closeAttachmentDrawer">
                        <ActivityItem icon="fi-rr-clip" @click="handleMobileFileAttach">
                            <span>{{ $t('chat.select_file') }}</span>
                        </ActivityItem>
                        <ActivityItem icon="fi-rr-cloud-upload-alt" @click="handleMobileFileExchangeAttach">
                            <span>{{ $t('chat.send_via_exchange') }}</span>
                        </ActivityItem>
                    </ActivityDrawer>
                </template>
                <a-dropdown
                    v-else
                    :trigger="['click']"
                    placement="topLeft"
                    overlayClassName="chat_footer_attach_dropdown"
                    :getPopupContainer="getAttachmentDropdownContainer">
                    <button
                        type="button"
                        class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost"
                        :class="!isMobile && 'ant-btn-sm'"
                        v-tippy
                        :content="$t('chat.select_file')">
                        <i class="fi fi-rr-clip"></i>
                    </button>
                    <a-menu slot="overlay">
                        <a-menu-item key="attach-file" class="chat_footer_attach_dropdown__item" @click="openFilePicker">
                            <i class="fi fi-rr-clip"></i>
                            <span>{{ $t('chat.select_file') }}</span>
                        </a-menu-item>
                        <a-menu-item key="attach-exchange" class="chat_footer_attach_dropdown__item" @click="openFileExchangeModal">
                            <i class="fi fi-rr-cloud-upload-alt"></i>
                            <span>{{ $t('chat.send_via_exchange') }}</span>
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
            </div>
            <BalloonEditor
                v-if="isMobile && !voiceRecording && !voiceUploading"
                v-model="message.text"
                chatEditor
                :key="`${activeChat.chat_uid}_${editorKey}`"
                initFocus
                :class="activeChat.is_public && 'is_public'"
                :userPageSize="activeChat && activeChat.member_count || 30"
                :useUserMentions="activeChat && activeChat.is_public || false"
                :chat_uid="activeChat && activeChat.chat_uid ? activeChat.chat_uid : null"
                ref="message_input"
                class="message_input m_message_input"
                :enterShifthHand="sendMessage"
                @uploadFiles="uploadFilesFromEditor"
                :placeholder="$t('chat.enter_your_message')"
                @change="setTyping()" />
            <template v-else-if="!voiceRecording && !voiceUploading">
                <BalloonEditor 
                    v-model="message.text"
                    chatEditor 
                    initFocus
                    :userPageSize="activeChat && activeChat.member_count || 30"
                    :key="`${activeChat.chat_uid}_${editorKey}`"
                    :class="activeChat.is_public && 'is_public'"
                    :useUserMentions="activeChat && activeChat.is_public || false"
                    :chat_uid="activeChat && activeChat.chat_uid ? activeChat.chat_uid : null"
                    :behaviorStatus="behaviorStatus"
                    @uploadFiles="uploadFilesFromEditor"
                    ref="message_input"
                    class="message_input" 
                    :enterShifthHand="sendMessage"
                    :placeholder="$t('chat.press_message')"
                    @change="setTyping()" />
            </template>
            <div v-else class="voice_record_composer">
                <div class="voice_record_panel">
                    <div class="voice_record_panel__status">
                        <span class="voice_record_panel__dot"></span>
                        <span>{{ voiceUploading ? voiceStatusText : formatVoiceDuration(voiceDurationSeconds) }}</span>
                    </div>
                    <div class="voice_record_panel__wave">
                        <span
                            v-for="(bar, index) in voiceBars"
                            :key="index"
                            class="voice_record_panel__bar"
                            :style="{ height: `${bar}px` }"></span>
                    </div>
                </div>
            </div>
            <div class="send_actions">
                <a-button 
                    v-if="!isMobile && activeChat.is_public"
                    type="ui"
                    ghost
                    v-tippy
                    :content="$t('chat.user_tag')"
                    style="font-size: 22px;"
                    shape="circle"
                    class="ant-btn-icon-only mr-2"
                    @click="userTag()">
                    @
                </a-button>
                <template v-if="is_support && !isMobile && !voiceRecording && !voiceUploading">
                    <a-popover
                        trigger="click"
                        placement="topRight"
                        transitionName=""
                        :overlayStyle="{ minWidth: '634px' }"
                        @visibleChange="popoverVisibleChange"
                        destroyTooltipOnHide>
                        <template slot="content">
                            <div class="popover-content" :style="{ height: popoverHeight + 'px' }">
                                <SupportMessageTemplates
                                    @changePopoverHeight="changePopoverHeight" />
                            </div>
                        </template>
                        <div class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost">
                            <i class="fi fi-rr-file-edit" />
                        </div>
                    </a-popover>
                </template>
                <Emoji 
                    v-if="shouldUseDesktopEmojiPicker && !voiceRecording && !voiceUploading" 
                    class="act_btn"
                    :gifUploading="gifUploading"
                    @click="selectEmoji"
                    @select-gif="handleGifSelect" />
                <a-button
                    v-if="shouldShowMobileGifDrawer && !voiceRecording && !voiceUploading"
                    type="ui"
                    ghost
                    class="act_btn gif_action_btn"
                    shape="circle"
                    :loading="gifUploading"
                    v-tippy
                    :content="$t('emoji.tab_gif')"
                    @click="openGifDrawer">
                    <span v-if="!gifUploading" class="gif_action_btn__icon">GIF</span>
                </a-button>
                <a-button
                    v-if="shouldShowVoiceTextInput && !voiceRecording && !voiceUploading"
                    type="ui"
                    ghost
                    class="act_btn"
                    shape="circle"
                    flaticon
                    v-tippy
                    :content="$t('chat.voice_text_input')"
                    icon="n-icon-circle-microphone"
                    @click="startVoiceTextInput" />
                <div class="send_button_wrap" :class="{ 'send_button_wrap--recording': voiceRecording || voiceUploading }">
                    <a-button
                        v-if="voiceRecording || voiceUploading"
                        class="voice_record_cancel act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost"
                        shape="circle"
                        v-tippy
                        :content="$t('chat.stop_voice_recording')"
                        :loading="voiceUploading && voiceActionType === 'text'"
                        :disabled="voiceUploading"
                        @click="cancelVoiceRecording">
                        <template v-if="!(voiceUploading && voiceActionType === 'text')">
                            <span
                                v-if="voiceActionType === 'text'"
                                class="voice_record_cancel__icon n-icon-circle-microphone"></span>
                            <i v-else class="fi fi-rr-cross-small"></i>
                        </template>
                    </a-button>
                    <a-button
                        v-if="(voiceRecording || voiceUploading) && voiceActionType !== 'text'"
                        class="send_button"
                        type="primary"
                        icon="fi-rr-paper-plane-top"
                        flaticon
                        shape="circle"
                        :loading="voiceUploading"
                        @click="sendVoiceRecording()" />
                    <div v-else-if="!voiceRecording && !voiceUploading" class="footer_action_switch">
                        <transition name="footer-action-switch">
                            <button
                            v-if="!checkEmptyMessage"
                            key="voice"
                            type="button"
                            class="footer_action_switch__btn footer_action_switch__btn--voice act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost"
                            :class="[!isMobile && 'ant-btn-sm', voiceRecording && 'voice_record_btn--active']"
                            v-tippy
                            :content="$t('chat.record_voice_message')"
                                :disabled="voiceRecording || voiceUploading"
                                @click="startVoiceRecording">
                                <i class="fi fi-rr-microphone"></i>
                            </button>
                            <a-button
                                v-else
                                key="send"
                                class="footer_action_switch__btn send_button"
                                type="primary"
                                icon="fi-rr-paper-plane-top"
                                flaticon
                                shape="circle"
                                :loading="voiceUploading"
                                @click="sendMessage" />
                        </transition>
                    </div>
                    <div v-if="!isMobile && !voiceRecording && !voiceUploading && checkEmptyMessage" class="send_behavior" @click="behaviorType()">
                        <template v-if="!behaviorStatus">Shift + </template>Enter
                    </div>
                </div>
            </div>
        </div>
        <input
            type="file"
            id="file_upload"
            multiple
            style="display:none;"
            ref="file_upload"
            @change="handleFileUpload"
            accept=".jpg, .jpeg, .png, .gif .doc, .docx, .xlsx, .xls, .pdf, .zip, .rar, .7z, .txt" />
        <a-modal
            :visible="fileExchangeModal"
            :title="$t('chat.send_via_exchange')"
            :zIndex="isMobile ? 5000 : 1000"
            :getContainer="getContainer"
            :footer="null"
            :width="isMobile ? '100%' : 760"
            :wrapClassName="isMobile ? 'file_exchange_modal_mobile' : ''"
            centered
            destroyOnClose
            @cancel="closeFileExchangeModal">
            <iframe
                v-if="fileExchangeIframeVisible"
                :key="fileExchangeIframeKey"
                :src="fileExchangeIframeSrc"
                :style="fileExchangeIframeStyle"
                frameborder="0"
                allow="clipboard-write" />
        </a-modal>
        <ActivityDrawer
            v-if="gifDrawerVisible"
            class="chat_footer_gif_drawer"
            :vis="gifDrawerVisible"
            :hardZIndex="6000"
            useVis
            :closeOnBodyClick="false"
            :cDrawer="closeGifDrawer">
            <Emoji
                embedded
                initialTab="gif"
                pickerSize="drawer"
                :showTabs="false"
                :gifUploading="gifUploading"
                @select-gif="handleMobileGifSelect" />
        </ActivityDrawer>
        <a-modal
            @dragover.prevent
            @drop.prevent
            :title="$t('chat.file_modal_title')"
            centered
            :visible="fileModal"
            :zIndex="isMobile ? 5000 : 1000"
            :getContainer="getContainer"
            class="file_modal"
            @cancel="closeFileModal()">
            <div class="file_modal_body">
                <div v-if="fileList && fileList.length">
                    <div
                        v-for="(file, index) in fileList"
                        :key="index"
                        class="file_item relative">
                        <div v-if="!file.file" class="file_uploading">
                            <div class="file_uploading__loader">
                                <a-spin />
                            </div>
                            <div class="file_uploading__progress">
                                <div class="file_uploading__name truncate">
                                    {{ file.name }}
                                </div>
                                <a-progress
                                    :percent="file.percent || 0"
                                    :showInfo="false"
                                    size="small"
                                    status="active" />
                            </div>
                        </div>
                        <template v-else>
                            <div
                                v-if="file.image"
                                class="image_file">
                                <a-button
                                    icon="fi-rr-trash"
                                    flaticon
                                    shape="circle"
                                    @click="deleteFile(file)"
                                    class="absolute img_delete" />
                                <img
                                    :src="file.file.path"
                                    :alt="file.iid">
                            </div>
                            <div
                                v-else
                                class="mb-2 doc_item w-full flex items-center justify-between">
                                <div class="flex items-center truncate">
                                    <a-icon
                                        type="file"
                                        class="mr-2" />
                                    <div class="truncate">
                                        {{file.name}}
                                    </div>
                                </div>
                                <a-button
                                    @click="deleteFile(file)"
                                    class="ml-2"
                                    icon="delete"
                                    type="link" />
                            </div>
                        </template>
                    </div>
                </div>
            </div>
            <div slot="footer" class="w-full">
                <ReplyMessageModal />
                <div class="input_wrapper">
                    <div class="left_actions">
                        <label
                            class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost"
                            :class="!isMobile && 'ant-btn-sm'"
                            for="file_upload_modal">
                            <i class="fi fi-rr-clip"></i>
                        </label>
                    </div>
                    <BalloonEditor
                        v-if="isMobile"
                        v-model="messageModal.text"
                        chatEditor
                        initFocus
                        :userPageSize="activeChat && activeChat.member_count || 30"
                        :key="`${activeChat.chat_uid}_${editorKey}`"
                        :useUserMentions="activeChat && activeChat.is_public || false"
                        :chat_uid="activeChat && activeChat.chat_uid ? activeChat.chat_uid : null"
                        ref="message_input_modal"
                        class="message_input m_message_input"
                        :placeholder="$t('chat.enter_your_message')"
                        @uploadFiles="uploadFilesFromEditor"
                        @change="setTyping()" />
                    <template v-else>
                        <BalloonEditor 
                            v-model="messageModal.text"
                            chatEditor
                            :userPageSize="activeChat && activeChat.member_count || 30"
                            :key="`${activeChat.chat_uid}_${editorKey}`"
                            :useUserMentions="activeChat && activeChat.is_public || false"
                            :behaviorStatus="behaviorStatus"
                            :chat_uid="activeChat && activeChat.chat_uid ? activeChat.chat_uid : null"
                            class="message_input"
                            ref="message_input_modal"
                            :placeholder="$t('chat.press_message')"
                            :enterShifthHand="sendMessage"
                            @uploadFiles="uploadFilesFromEditor"
                            @change="setTyping()" />
                    </template>
                    <div class="send_actions">
                        <input
                            type="file"
                            id="file_upload_modal"
                            multiple
                            style="display:none;"
                            ref="file_upload_modal"
                            @change="handleFileUpload"
                            accept=".jpg, .jpeg, .png, .gif .doc, .docx, .xlsx, .xls, .pdf, .zip, .rar, .7z, .txt" />
                        <a-button
                            class="send_button"
                            type="primary"
                            icon="fi-rr-paper-plane-top"
                            flaticon
                            shape="circle"
                            @click="sendMessage" />
                    </div>
                </div>
            </div>
        </a-modal>
        <div v-show="showDragWin" class="drag-win">
            <div class="drag-body">
                <i class="fi fi-rr-add-document mb-3 blue_color" style="font-size: 54px;" />
                <span class="text-xl blue_color">{{$t('chat.drop_files_here')}}</span>
            </div>
        </div>
    </div>
</template>

<script>
import ChatEventBus from '../../utils/ChatEventBus'
import { getChatDraft, removeChatDraft, saveChatDraft } from '../../utils/chatDraftsDb'
import computed from './mixins/computed'
import methods from './mixins/methods'
import utils from './mixins/utils'
import eventBus from '@/utils/eventBus'
import { useResizeObserver } from '@vueuse/core'
export default {
    name: "ChatFooter",
    props: {
        resizeEvent: {
            type: Function,
            default: () => {}
        },
        loadingDown: {
            type: Boolean,
            default: false
        },
        showDownBtn: {
            type: Boolean,
            default: false
        },
        missedCount: {
            type: Number,
            default: 0
        },
        downAction: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        Emoji: () => import('@/components/Emoji'),
        ActivityDrawer: () => import('@/components/ActivitySelect/ActivityDrawer.vue'),
        ActivityItem: () => import('@/components/ActivitySelect/ActivityItem.vue'),
        ReplyMessage: () => import('./ReplyMessage'),
        ReplyMessageModal: () => import('./ReplyMessageModal'),
        SupportMessageTemplates: () => import('./SupportMessageTemplates'),
        BalloonEditor: () => import('@apps/CKEditor/BalloonEditor.vue'),
        EditBlock: () => import('./EditBlock.vue')
    },
    mixins: [computed, methods, utils],
    computed: {
        replyMessage() {
            return this.getReplyMessage(this.activeChat.chat_uid)
        },
        chatFooter() {
            return this.$refs.chatFooter
        },
        fileExchangeIframeSrc() {
            const baseUrl = this.getFileExchangeBaseUrl()
            const params = new URLSearchParams({
                embed: 'chat-upload',
                lang: this.getFileExchangeLang(),
                parent_origin: typeof window !== 'undefined' ? window.location.origin : ''
            })

            return `${baseUrl}/?${params.toString()}`
        },
        fileExchangeIframeStyle() {
            return {
                display: 'block',
                width: '100%',
                height: this.isMobile ? '70vh' : '640px',
                border: 0,
                background: '#fff'
            }
        },
        voiceStatusText() {
            if (this.voiceActionType === 'text') {
                if (this.voiceProcessingStage === 'typing') {
                    return this.$t('chat.voice_typing_recognized_text')
                }

                return this.$t('chat.voice_recognizing')
            }

            return this.$t('chat.voice_uploading')
        },
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        shouldUseDesktopEmojiPicker() {
            return !this.isMobile || this.isStandaloneChatWindow
        },
        shouldShowMobileGifDrawer() {
            return this.isMobile && !this.isStandaloneChatWindow
        },
        shouldShowVoiceTextInput() {
            return !this.isMobile || this.isStandaloneChatWindow
        }
    },
    data(){
        return {
            behaviorStatus: true,
            height: this.isMobile ? 50 : 55,
            popoverHeight: 318,
            showDragWin: false,
            isInputExpanded: false,
            inputBaseHeight: 45,
            inputResizeObserver: null,
            attachmentDrawerVisible: false,
            oldChat: null,
            editorKey: 0,
            fileExchangeModal: false,
            fileExchangeIframeVisible: false,
            fileExchangeIframeKey: 0,
            gifDrawerVisible: false,
            gifUploading: false,
            voiceRecording: false,
            voiceUploading: false,
            voiceDurationSeconds: 0,
            voiceBars: Array.from({ length: 28 }, () => 10),
            voiceRecorder: null,
            voiceStream: null,
            voiceChunks: [],
            voiceMimeType: '',
            voiceFileExtension: '',
            voiceSendRequested: false,
            voiceActionType: null,
            voiceProcessingStage: null,
            voiceTimerId: null,
            voiceAnimationFrameId: null,
            voiceAudioContext: null,
            voiceAnalyser: null,
            voiceSourceNode: null,
            voiceProcessingAnimationId: null,
            pageHideHandler: null,
            beforeUnloadHandler: null,
            visibilityChangeHandler: null,
            draftRemovalSyncReadyChatUid: null
        }
    },
    watch: {
        fileModal(val) {
            if(val) {
                this.$nextTick(() => {
                    if(!this.isMobile)
                        this.$refs['message_input_modal']?.focus()
                })
            }
        },
        activeChat: {
            immediate: true,
            async handler(nextChat, prevChat) {
                this.draftRemovalSyncReadyChatUid = null

                if (prevChat?.chat_uid && prevChat.chat_uid !== nextChat?.chat_uid) {
                    await this.persistDraftByChat(prevChat)
                }

                if (nextChat?.chat_uid) {
                    await this.restoreDraftByChat(nextChat)
                    this.draftRemovalSyncReadyChatUid = nextChat.chat_uid
                }
            }
        },
        'message.text': function() {
            this.syncDraftRemovalState()
        },
        'messageModal.text': function() {
            this.syncDraftRemovalState()
        },
        fileList: {
            deep: true,
            handler() {
                this.syncDraftRemovalState()
            }
        }
    },
    created() {
        const behaviorType = localStorage.getItem('behaviorType')
        if(behaviorType)
            this.behaviorStatus = JSON.parse(behaviorType)
        eventBus.$on('pasteText', (text) => {
            this.message.text = text
        })

        this.pageHideHandler = () => {
            this.persistDraftByChat()
        }
        this.beforeUnloadHandler = () => {
            this.persistDraftByChat()
        }
        this.visibilityChangeHandler = () => {
            if (document.visibilityState === 'hidden') {
                this.persistDraftByChat()
            }
        }
    },
    mounted() {
        ChatEventBus.$on('edit_message', message => {
            if(this.activeChat) {
                const editMessage = {
                    ...message,
                    chat_uid: message.chat_uid || this.activeChat.chat_uid,
                    edit: true
                }

                if (message.attachments?.length) {
                    message.attachments.forEach(item => {
                        if ('is_new' in item) {
                            delete item.is_new
                        }
                    })
                }

                this.$store.commit('chat/CHANGE_CHAT_ALL_MESSAGE', {
                    id: this.activeChat.chat_uid,
                    message: editMessage
                })
                this.$nextTick(() => {
                    this.$refs['message_input'].focus()
                })
            }
        })
        ChatEventBus.$on('create_meeting_message', data => {
            this.$nextTick(() => {
                this.focusMessageInput()
                this.createMessage(data)
            })
        })
        ChatEventBus.$on('inputFocus', () => {
            this.focusMessageInput()
        })

        if (typeof window !== 'undefined') {
            window.addEventListener('message', this.handleFileExchangeMessage)
            window.addEventListener('pagehide', this.pageHideHandler)
            window.addEventListener('beforeunload', this.beforeUnloadHandler)
            document.addEventListener('visibilitychange', this.visibilityChangeHandler)
        }

        this.$nextTick(()=>{
            if (this.chatFooter && this.isMobile) {
                this.inputBaseHeight = this.chatFooter.offsetHeight
            }
            if(this.activeChat){ 
                this.initListeners()
            }
        })  

        useResizeObserver(this.chatFooter, entries => {
            const entry = entries[0]
            const height = entry.target.scrollHeight

            if (this.inputBaseHeight === null) {
                this.inputBaseHeight = height > 1 ? height : 0
            } else {
                this.isInputExpanded = height > this.inputBaseHeight ? true : false
            }

            if (height > this.height) {
                this.resizeEvent()
            }
        })
    },
    beforeDestroy() {
        this.persistDraftByChat()
        this.removeListeners()
        this.resetVoiceRecorderState()
        eventBus.$off('pasteText')
        ChatEventBus.$off('edit_message')
        ChatEventBus.$off('create_meeting_message')
        if (typeof window !== 'undefined') {
            window.removeEventListener('message', this.handleFileExchangeMessage)
            window.removeEventListener('pagehide', this.pageHideHandler)
            window.removeEventListener('beforeunload', this.beforeUnloadHandler)
            document.removeEventListener('visibilitychange', this.visibilityChangeHandler)
        }
    },
    methods: {
        openGifDrawer() {
            this.gifDrawerVisible = true
        },
        closeGifDrawer() {
            this.gifDrawerVisible = false
        },
        handleMobileGifSelect(gif) {
            this.closeGifDrawer()
            this.handleGifSelect(gif)
        },
        getDraftUserId() {
            return this.$store.state.user.user?.id || null
        },
        getChatComposerState(chatUid) {
            const chatState = this.$store.state.chat

            return {
                message: chatState.message?.[chatUid] || { text: '' },
                messageModal: chatState.messageModal?.[chatUid] || { text: '' },
                fileList: Array.isArray(chatState.fileList?.[chatUid]) ? chatState.fileList[chatUid] : [],
                fileModal: !!chatState.fileModal?.[chatUid]
            }
        },
        normalizeDraftFiles(files = []) {
            return files
                .filter(item => item?.file)
                .map(item => ({
                    ...JSON.parse(JSON.stringify(item)),
                    loading: false,
                    percent: 100
                }))
        },
        buildDraftPayload(chatUid) {
            const composerState = this.getChatComposerState(chatUid)

            return {
                text: composerState.message?.text || '',
                modalText: composerState.messageModal?.text || '',
                files: this.normalizeDraftFiles(composerState.fileList),
                fileModal: composerState.fileModal,
                updatedAt: new Date().toISOString()
            }
        },
        hasDraftContent(draft) {
            const text = String(draft?.text || '').trim()
            const modalText = String(draft?.modalText || '').trim()
            const files = Array.isArray(draft?.files) ? draft.files : []

            return !!(text || modalText || files.length)
        },
        syncDraftRemovalState() {
            const chatUid = this.activeChat?.chat_uid
            if (!chatUid) return
            if (this.draftRemovalSyncReadyChatUid !== chatUid) return

            const existingDraft = this.$store.state.chat.chatDrafts?.[chatUid]
            if (!existingDraft) return

            const currentDraft = this.buildDraftPayload(chatUid)
            if (!this.hasDraftContent(currentDraft)) {
                this.clearDraftByChatUid(chatUid)
            }
        },
        async clearDraftByChatUid(chatUid) {
            const userId = this.getDraftUserId()
            if (!chatUid || !userId) return

            this.$store.commit('chat/REMOVE_CHAT_DRAFT', chatUid)

            try {
                await removeChatDraft({ userId, chatUid })
            } catch (error) {
                console.error(error)
            }
        },
        async persistDraftByChat(chat = this.activeChat) {
            const chatUid = chat?.chat_uid
            const userId = this.getDraftUserId()
            if (!chatUid || !userId) return

            const composerState = this.getChatComposerState(chatUid)
            if (composerState.message?.edit) return

            const draft = this.buildDraftPayload(chatUid)

            if (!this.hasDraftContent(draft)) {
                await this.clearDraftByChatUid(chatUid)
                return
            }

            this.$store.commit('chat/SET_CHAT_DRAFT', { chatUid, draft })

            try {
                await saveChatDraft({
                    userId,
                    chatUid,
                    draft
                })
            } catch (error) {
                console.error(error)
            }
        },
        hasInMemoryComposerContent(chatUid) {
            const composerState = this.getChatComposerState(chatUid)

            return this.hasDraftContent({
                text: composerState.message?.text || '',
                modalText: composerState.messageModal?.text || '',
                files: composerState.fileList || []
            })
        },
        applyDraftToComposer(chatUid, draft) {
            this.SET_CHAT_MESSAGE(chatUid)
            this.CHANGE_CHAT_MESSAGE({
                id: chatUid,
                message: draft?.text || ''
            })

            this.SET_CHAT_MESSAGE_MODAL(chatUid)
            this.CHANGE_CHAT_MESSAGE_MODAL({
                id: chatUid,
                message: draft?.modalText || ''
            })

            this.SET_FILE_LIST({
                id: chatUid,
                files: Array.isArray(draft?.files) ? draft.files : []
            })

            this.SET_FILE_MODAL({
                id: chatUid,
                value: !!(draft?.fileModal && draft?.files?.length)
            })
        },
        async restoreDraftByChat(chat = this.activeChat) {
            const chatUid = chat?.chat_uid
            const userId = this.getDraftUserId()
            if (!chatUid || !userId) return

            if (this.hasInMemoryComposerContent(chatUid)) {
                return
            }

            let draft = this.$store.state.chat.chatDrafts?.[chatUid] || null

            if (!draft) {
                try {
                    draft = await getChatDraft({ userId, chatUid })
                    if (draft) {
                        this.$store.commit('chat/SET_CHAT_DRAFT', { chatUid, draft })
                    }
                } catch (error) {
                    console.error(error)
                    draft = null
                }
            }

            if (!draft) return

            this.applyDraftToComposer(chatUid, draft)
        },
        getAttachmentDropdownContainer(trigger) {
            return document.body
        },
        closeAttachmentDrawer() {
            this.attachmentDrawerVisible = false
        },
        handleMobileFileAttach() {
            this.closeAttachmentDrawer()
            this.openFilePicker()
        },
        handleMobileFileExchangeAttach() {
            this.closeAttachmentDrawer()
            this.openFileExchangeModal()
        },
        openFilePicker() {
            if (this.$refs.file_upload?.value) {
                this.$refs.file_upload.value = ''
            }
            this.$refs.file_upload?.click()
        },
        getFileExchangeBaseUrl() {
            return String(process.env.VUE_APP_FILE_EXCHANGE_URL || 'https://files.gos24.kz').replace(/\/+$/, '')
        },
        getFileExchangeLang() {
            const locale = String(this.$i18n?.locale || 'ru').toLowerCase()

            if (locale === 'kk') {
                return 'kz'
            }

            if (['ru', 'kz', 'en'].includes(locale)) {
                return locale
            }

            return 'ru'
        },
        openFileExchangeModal() {
            this.fileExchangeModal = true
            this.fileExchangeIframeVisible = false

            this.$nextTick(() => {
                if (!this.fileExchangeModal)
                    return

                window.requestAnimationFrame(() => {
                    if (!this.fileExchangeModal)
                        return

                    this.fileExchangeIframeKey += 1
                    this.fileExchangeIframeVisible = true
                })
            })
        },
        closeFileExchangeModal() {
            this.fileExchangeModal = false
            this.fileExchangeIframeVisible = false
            this.fileExchangeIframeKey += 1
        },
        async handleFileExchangeMessage(event) {
            try {
                const expectedOrigin = new URL(this.getFileExchangeBaseUrl()).origin
                if (event.origin !== expectedOrigin) {
                    return
                }

                if (event.data?.type !== 'file_exchange_upload_complete') {
                    return
                }

                const url = String(event.data?.url || '').trim()
                if (!url.startsWith(`${expectedOrigin}/`)) {
                    return
                }

                this.closeFileExchangeModal()
                await this.sendFileExchangeLinkMessage(url)
            } catch (error) {
                console.error(error)
            }
        },
        focusMessageInput() {
            const focusEditor = () => {
                const editorRef = this.$refs['message_input']
                if (!editorRef)
                    return

                editorRef.focus?.()
                editorRef.editorFocus?.()

                const editable = editorRef.$el?.querySelector?.('.ck-editor__editable')
                    || editorRef.$el?.querySelector?.('[contenteditable="true"]')

                if (editable) {
                    editable.focus()

                    const selection = window.getSelection?.()
                    if (selection && document.createRange) {
                        const range = document.createRange()
                        range.selectNodeContents(editable)
                        range.collapse(false)
                        selection.removeAllRanges()
                        selection.addRange(range)
                    }
                }
            }

            this.$nextTick(() => {
                focusEditor()
                requestAnimationFrame(() => {
                    focusEditor()
                    setTimeout(() => {
                        focusEditor()
                    }, 120)
                })
            })
        },
        popoverVisibleChange(value) {
            if(!value) {
                this.$store.commit('chat/RESET_SUPPORT_MESSAGE_TEMPLATES')
                this.$store.commit('chat/RESET_SMT_PAGE')
                this.$store.commit('chat/SET_SMT_END_OF_LIST', false)
                this.popoverHeight = 318
            }
        },
        changePopoverHeight(value) {
            this.$nextTick(() => {
                this.popoverHeight = value
            })
        },
        initListeners() {
            window.addEventListener('paste', this.paste)
            window.addEventListener('dragover', this.dragOver)
            window.addEventListener('drop', this.dropComplete)
            window.addEventListener('dragleave', this.dragLeave)
        },
        removeListeners() {
            window.removeEventListener('paste', this.paste, false)
            window.removeEventListener('dragover', this.dragOver, false)
            window.removeEventListener('drop', this.dropComplete, false)
            window.removeEventListener('dragleave', this.dragLeave, false)
        }
    }
}
</script>

<style lang="scss" scoped>
.scrol_down_btn{
    position: absolute;
    top: -50px;
    right: 15px;
    z-index: 50;
    &.is_mobile{
        right: 0px;
    }
    &::v-deep{
        .ant-scroll-number.ant-badge-count{
            top: 5px;
            right: 5px;
        }
    }
}
.send_button_wrap{
    display: flex;
    flex-direction: column;
    align-items: center;

    &.send_button_wrap--recording{
        flex-direction: row;
        gap: 10px;
    }
}

.send_button{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    min-width: 34px;
    line-height: 34px;

    &::v-deep{
        i,
        .fi{
            margin: 0 !important;
            line-height: 1;
            transform: translate(-1px, 0);
        }
    }
}

.footer_action_switch{
    position: relative;
    width: 49px;
    height: 34px;
}

@media (max-width: 900px) {
    .footer_action_switch{
        width: 38px;
    }
}

.footer_action_switch__btn{
    position: absolute !important;
    inset: 0;
    width: 34px;
    height: 34px;
    min-width: 34px;
    line-height: 34px;
    margin: 0 !important;
    margin: auto !important;
    transform-origin: center center;
}

.footer_action_switch__btn.ant-btn-sm{
    width: 34px;
    height: 34px;
    min-width: 34px;
    line-height: 34px;
}

.footer_action_switch__btn--voice{
    background: var(--blue) !important;
    border-color: var(--blue) !important;
    color: #fff !important;

    &:hover,
    &:focus{
        background: var(--primaryColor) !important;
        border-color: var(--primaryColor) !important;
        color: #fff !important;
        opacity: .92;
    }

    i{
        color: inherit !important;
    }
}

.voice_record_panel{
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;
    min-width: 0;
    padding: 0;
}

.voice_record_panel__status{
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #5f6b85;
    font-variant-numeric: tabular-nums;
}

.voice_record_panel__dot{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ff4d4f;
    box-shadow: 0 0 0 6px rgba(255, 77, 79, 0.14);
}

.voice_record_panel__wave{
    flex: 1 1 auto;
    min-width: 0;
    height: 34px;
    display: flex;
    align-items: center;
    gap: 3px;
}

.voice_record_panel__bar{
    flex: 1 1 0;
    min-width: 3px;
    border-radius: 999px;
    background: rgba(65, 108, 233, 0.28);
}

.voice_record_composer{
    flex: 1 1 auto;
    min-height: 55px;
    min-width: 0;
    display: flex;
    align-items: center;
    padding: 0 108px 0 14px;
}

.voice_record_cancel{
    width: 34px;
    height: 34px;
    min-width: 34px;
    line-height: 34px;
    background: rgba(0, 0, 0, 0.04) !important;
    border-color: transparent !important;
    color: #2d2d2d !important;

    &:hover,
    &:focus{
        background: rgba(0, 0, 0, 0.08) !important;
        border-color: transparent !important;
        color: #2d2d2d !important;
    }
}

.voice_record_cancel__icon{
    color: var(--blue);
    font-size: 20px;
    line-height: 1;
}

.voice_record_btn--active{
    color: #ff4d4f;
    border-color: rgba(255, 77, 79, 0.28);
}

.gif_action_btn{
    min-width: 34px;
    width: 34px;
    height: 34px;
    padding: 0;
    background: transparent !important;
    color: #334b5a !important;

    &:hover,
    &:focus{
        border-color: var(--blue) !important;
        color: var(--blue) !important;
        background: rgba(65, 108, 233, 0.08) !important;
    }
}

.gif_action_btn__icon{
    font-size: 13px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: 0;
}

.footer-action-switch-enter-active,
.footer-action-switch-leave-active{
    transition: opacity .2s ease, transform .2s cubic-bezier(.2,.8,.2,1);
}

.footer-action-switch-enter,
.footer-action-switch-leave-to{
    opacity: 0;
    transform: scale(.45);
}

.footer-action-switch-enter{
    transform: scale(.45);
}

.footer-action-switch-enter-to,
.footer-action-switch-leave{
    opacity: 1;
    transform: scale(1);
}

.send_behavior{
    font-size: 9px;
    color: var(--gray);
    cursor: pointer;
    margin-top: 1px;
    min-width: 49px;
    text-align: center;
    &:hover{
        opacity: 0.8;
    }
}
</style>

<style lang="scss">
.chat_footer_attach_dropdown{
    z-index: 100000 !important;

    .chat_footer_attach_dropdown__item{
        display: flex;
        align-items: center;
        gap: 8px;

        i{
            font-size: 16px;
        }
    }
}

.chat_body__footer.reply_footer{
    .input_wrapper{
        .left_actions{
            top: auto;
            bottom: 0;
            transform: none;
            align-items: flex-end;
            padding-bottom: 8px;
        }
    }
}

.file_exchange_modal_mobile{
    &.ant-modal-wrap.ant-modal-centered .ant-modal{
        top: 0!important;
        width: 100% !important;
        max-width: 100%;
        margin: 0;
        padding-bottom: 0;
    }

    .ant-modal-content{
        min-height: 100vh;
        border-radius: 0;
    }

    .ant-modal-body{
        padding: 0;
    }
}

.file_modal_body{
    overflow-y: auto;
    padding: 10px;
    .img_delete{
        top: 10px;
        right: 10px;
    }
    .file_item{
        &:not(:last-child){
            .image_file{
                margin-bottom: 10px;
            }
        }
        .file_uploading{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.04);
            margin-bottom: 10px;
        }
        .file_uploading__loader{
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 24px;
        }
        .file_uploading__progress{
            flex: 1 1 auto;
            min-width: 0;
        }
        .file_uploading__name{
            font-size: 13px;
            margin-bottom: 8px;
        }
        .image_file{
            background: rgba(0, 0, 0, 0.04);
            position: relative;
            min-height: 200px;
            max-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            img{
                width: 100%;
                object-fit: cover;
                vertical-align: middle;
                -o-object-fit: cover;
            }
        }
    }
}
.file_modal{
    .ant-modal-header{
        padding: 10px;
    }
    .ant-modal-footer{
        padding: 0px;
        position: sticky;
        bottom: 0;
        z-index: 10;
    }
    .ant-modal-close-x{
        width: 43px;
        height: 43px;
        line-height: 43px;
    }
    .input_wrapper{
        position: relative;
        width: 100%;
        min-width: 0;
        border-top: 1px solid var(--border2);
        .left_actions{
            position: absolute;
            bottom: 0;
            z-index: 1;
            left: 0;
            height: 54px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-left: 10px;
            padding-top: 0;
            height: 100%;
            width: 50px;
        }
        .message_input{
            width: 100%;
            height: 100%;
            min-width: 0;
            max-width: 100%;
            text-align: left;
            min-height: 55px!important;
            outline: none;
            padding: 0 148px 0 54px;
            border: 0px;
            outline: none;
            border-radius: 0px;
            box-shadow: initial!important;
            border: 0px!important;
            overflow-wrap: anywhere;
            word-break: break-word;
            &.ck,
            .ck-editor,
            .ck-editor__main,
            .ck-editor__editable,
            .ck-content{
                min-width: 0;
                max-width: 100%;
            }
            .ck-editor__editable,
            .ck-content{
                overflow-wrap: anywhere;
                word-break: break-word;
            }
        }
        .send_actions{
            position: absolute;
            bottom: 0;
            z-index: 1;
            right: 0;
            height: 55px;
            display: flex;
            align-items: center;
            padding-right: 10px;
            .act_btn{
                margin-right: 8px;
                i{
                    font-size: 20px;
                }
            }
        }
    }
    .ant-modal-body{
        padding: 0px;
        min-height: 400px;
        max-height: 400px;
        overflow-y: auto;
        @media (max-width: 900px) {
            min-height: auto;
            max-height: 300px;
        }
    }
    @media (min-width: 901px) {
        .ant-modal-wrap,
        .ant-modal-mask{
            position: absolute;
        }
    }
    .ant-modal-mask{
        background-color: rgba(0, 0, 0, 0.3);
    }
}
.drag-win{
    display: block;
    position: fixed;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    left: 30px;
    bottom: 30px;
    right: 30px;
    top: 30px;
    z-index: 1000;
    .drag-body{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        backdrop-filter: saturate(180%) blur(20px);
        background: rgba(251, 251, 253, .8);
        border: 2px dashed var(--primaryColor);
        border-radius: 20px;
        width: 100%;
        height: 100%;
    }
}
</style>
