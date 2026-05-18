<template>
    <div ref="commentWrapper" :style="mobileWrapperStyle">
        <div
            v-if="!isMobile"
            class="comment_text"
            :class="!showEditor && 'place'">
            <template v-if="showEditor">
                <div class="ck_wrap" :class="showEditorToolbar && 'show_toolbar'">
                    <Editor
                        v-model="comment.text"
                        ref="editor"
                        useUserMentions
                        commentEditor
                        :behaviorStatus="false"
                        :mentionsData="mentionsData"
                        :enterShifthHand="addHandler"
                        initFocus />
                </div>

                <!-- VISIBILITY: Private / Public (Switch) -->
                <div v-if="useVisibility" class="comment_visibility px-4 pb-2">
                    <div class="visibility_row">
                        <a-switch
                            v-model="comment.is_personal"
                            size="small" />
                        <div
                            class="visibility_text"
                            :class="comment.is_personal ? 'is_private' : 'is_public'">
                            <i
                                class="fi mr-2"
                                :class="comment.is_personal ? 'fi-rr-lock' : 'fi-rr-globe'" />
                            {{ comment.is_personal ? $t('comment.private') : $t('comment.public') }}
                        </div>
                    </div>
                </div>

                <div class="comment_text__footer">
                    <div v-if="voiceRecording || voiceUploading" class="voice_record_panel">
                        <div class="voice_record_panel__status">
                            <span class="voice_record_panel__dot"></span>
                            <span>{{ voiceUploading ? 'Uploading voice...' : formatVoiceDuration(voiceDurationSeconds) }}</span>
                        </div>
                        <div class="voice_record_panel__wave">
                            <span
                                v-for="(bar, index) in voiceBars"
                                :key="index"
                                class="voice_record_panel__bar"
                                :style="{ height: `${bar}px` }"></span>
                        </div>
                        <a-button
                            type="ui"
                            ghost
                            size="small"
                            shape="circle"
                            :disabled="voiceUploading"
                            @click="cancelVoiceRecording">
                            <i class="fi fi-rr-cross-small"></i>
                        </a-button>
                    </div>
                    <label
                        v-if="showFileUpload"
                        class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost ant-btn-sm ml-2"
                        @click="openFileModal">
                        <i class="fi flaticon fi-rr-clip"></i>
                    </label>
                    <a-button
                        type="ui"
                        ghost
                        size="small"
                        shape="circle"
                        v-tippy
                        :content="$t('chat.record_voice_message')"
                        class="ant-btn-icon-only ml-2 flex items-center justify-center"
                        :class="voiceRecording && 'voice_record_btn--active'"
                        :loading="voiceUploading"
                        @click="voiceRecording || voiceUploading ? sendVoiceRecording() : startVoiceRecording()">
                        <i class="fi fi-rr-microphone"></i>
                    </a-button>
                    <a-button
                        v-if="mentionsData && mentionsData.length"
                        type="ui"
                        ghost
                        v-tippy
                        size="small"
                        :content="$t('comment.user_tag')"
                        shape="circle"
                        style="font-size: 16px;"
                        class="ant-btn-icon-only ml-2 flex items-center justify-center"
                        @click="userTag()">
                        @
                    </a-button>
                    <Emoji
                        v-if="showEmoji"
                        class="ml-2"
                        size="small"
                        pickerSize="compact"
                        :gifUploading="gifUploading"
                        @click="selectEmoji"
                        @select-gif="handleGifSelect" />

                    <a-button
                        type="ui"
                        ghost
                        class="ml-2"
                        shape="circle"
                        :class="showEditorToolbar && 'active_btn'"
                        size="small"
                        flaticon
                        icon="fi-rr-message-text"
                        @click="toggleShowToolbar()" />

                    <a-dropdown
                        :trigger="['click']"
                        :getPopupContainer="getModalContainer">
                        <a-button
                            type="ui"
                            ghost
                            class="ml-2"
                            shape="circle"
                            size="small"
                            flaticon
                            icon="fi-rr-settings" />
                        <a-menu slot="overlay">
                            <a-menu-item
                                key="0"
                                class="flex items-center"
                                @click="setBlockLeft()">
                                <i
                                    v-if="blockLeft"
                                    class="mr-2 fi fi-rr-check" />
                                {{ $t('comment.blocksLeft') }}
                            </a-menu-item>
                        </a-menu>
                    </a-dropdown>
                </div>
            </template>

            <div v-else class="comment_text__placeholder" @click="showEditorHandler()">
                {{ $t(inputPlaceholder) }}
            </div>
        </div>
        <div
            v-else-if="!showEditor || !parent"
            class="comment_text place">
            <div class="comment_text__placeholder" @click="showEditorHandler()">
                {{ $t(inputPlaceholder) }}
            </div>
        </div>

        <template v-if="showEditor && !isMobile">
            <FileAttach
                ref="fileAttach"
                :attachmentFiles="files"
                :maxMBSize="50"
                :oneUpload="oneUpload"
                :createFounder="createFounder"
                :class="files.length && 'mt-2'"
                class="ml-2" />

            <div class="flex items-center gap-1 justify-end ml-2 mt-2">
                <a-button
                    v-if="editData"
                    type="flat_primary"
                    :loading="loading"
                    @click="addHandler()">
                    {{ $t('comment.save') }}
                </a-button>
                <a-button
                    v-else
                    type="flat_primary"
                    :loading="loading"
                    :block="isMobile"
                    @click="addHandler()">
                    {{ $t('comment.send') }}
                </a-button>
                <a-button
                    type="ui_ghost"
                    ghost
                    :block="isMobile"
                    @click="closeEditorHandler()">
                    {{ $t('comment.cancel') }}
                </a-button>
            </div>
        </template>

        <DrawerTemplate
            v-if="isMobile"
            :value="showEditor"
            placement="bottom"
            :height="mobileDrawerHeight"
            :showHeader="false"
            :disabledBodyPadding="true"
            bodyStyle="overflow:hidden;padding:0;"
            wrapClassName="mobile-comment-drawer-wrap"
            @close="closeEditorHandler()">
            <div class="mobile_comment_drawer">
                <div class="mobile_drawer_handle_area" @click="closeEditorHandler()">
                    <div class="mobile_drawer_handle"></div>
                </div>
                <div class="mobile_comment_content">
                    <div class="mobile_comment_editor">
                        <div class="ck_wrap">
                            <Editor
                                v-model="comment.text"
                                ref="editor"
                                useUserMentions
                                commentEditor
                                :behaviorStatus="false"
                                :mentionsData="mentionsData"
                                :enterShifthHand="addHandler"
                                initFocus />
                        </div>

                        <div v-if="useVisibility" class="comment_visibility px-4 pb-2">
                            <div class="visibility_row">
                                <a-switch
                                    v-model="comment.is_personal"
                                    size="small" />
                                <div
                                    class="visibility_text"
                                    :class="comment.is_personal ? 'is_private' : 'is_public'">
                                    <i
                                        class="fi mr-2"
                                        :class="comment.is_personal ? 'fi-rr-lock' : 'fi-rr-globe'" />
                                    {{ comment.is_personal ? $t('comment.private') : $t('comment.public') }}
                                </div>
                            </div>
                        </div>

                        <div class="comment_text__footer">
                            <div v-if="voiceRecording || voiceUploading" class="voice_record_panel">
                                <div class="voice_record_panel__status">
                                    <span class="voice_record_panel__dot"></span>
                                    <span>{{ voiceUploading ? 'Uploading voice...' : formatVoiceDuration(voiceDurationSeconds) }}</span>
                                </div>
                                <div class="voice_record_panel__wave">
                                    <span
                                        v-for="(bar, index) in voiceBars"
                                        :key="`mobile-${index}`"
                                        class="voice_record_panel__bar"
                                        :style="{ height: `${bar}px` }"></span>
                                </div>
                                <a-button
                                    type="ui"
                                    ghost
                                    size="small"
                                    shape="circle"
                                    :disabled="voiceUploading"
                                    @click="cancelVoiceRecording">
                                    <i class="fi fi-rr-cross-small"></i>
                                </a-button>
                            </div>
                            <label
                                v-if="showFileUpload"
                                class="act_btn ant-btn flex items-center justify-center ant-btn-ui ant-btn-circle ant-btn-icon-only ant-btn-background-ghost ant-btn-sm ml-2"
                                @click="openFileModal">
                                <i class="fi flaticon fi-rr-clip"></i>
                            </label>
                            <a-button
                                type="ui"
                                ghost
                                size="small"
                                v-tippy
                                :content="$t('chat.record_voice_message')"
                                shape="circle"
                                class="ant-btn-icon-only ml-2 flex items-center justify-center"
                                :class="voiceRecording && 'voice_record_btn--active'"
                                :loading="voiceUploading"
                                @click="voiceRecording || voiceUploading ? sendVoiceRecording() : startVoiceRecording()">
                                <i class="fi fi-rr-microphone"></i>
                            </a-button>
                            <a-button
                                v-if="mentionsData && mentionsData.length"
                                type="ui"
                                ghost
                                v-tippy
                                size="small"
                                :content="$t('comment.user_tag')"
                                shape="circle"
                                style="font-size: 16px;"
                                class="ant-btn-icon-only ml-2 flex items-center justify-center"
                                @click="userTag()">
                                @
                            </a-button>
                        </div>
                    </div>

                    <div class="mobile_comment_files_wrap">
                        <FileAttach
                            ref="fileAttach"
                            :attachmentFiles="files"
                            :maxMBSize="50"
                            :oneUpload="oneUpload"
                            :createFounder="createFounder"
                            class="mobile_files_attach" />
                    </div>
                </div>

                <div class="mobile_comment_footer">
                    <a-button
                        v-if="editData"
                        type="flat_primary"
                        :loading="loading"
                        block
                        @click="addHandler()">
                        {{ $t('comment.save') }}
                    </a-button>
                    <template v-else>
                        <a-button
                            type="flat_primary"
                            :loading="loading"
                            block
                            @click.stop="submitFromDrawer()">
                            {{ $t('comment.send') }}
                        </a-button>
                    </template>
                    <a-button
                        type="ui_ghost"
                        ghost
                        block
                        @click="closeEditorHandler()">
                        {{ $t('comment.cancel') }}
                    </a-button>
                </div>
            </div>
        </DrawerTemplate>
    </div>
</template>

<script>
//import UserDrawer from './UserDrawer.vue'
import eventBus from './eventBus'
import eventBusGlob from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { inputProps } from './initProps.js'
import {
    buildFallbackVoiceBars,
    buildVoiceUploadFile,
    formatVoiceDuration,
    getVoiceMimeConfig
} from '@/utils/voice'

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        Emoji: () => import('@/components/Emoji'),
        //UserDrawer,
        FileAttach: () => import('@apps/vue2Files/components/FileAttach'),
        Editor: () => import('@apps/CKEditor/index.vue')
    },
    props: { ...inputProps },
    data() {
        const buildComment = () => ({
            parent: this.parent ? this.parent.id : null,
            text: '',
            readers: [],
            related_object: this.related_object,
            model: this.model,

            // ✅ is_personal: true = PRIVATE, false = PUBLIC
            // ✅ default: PRIVATE
            is_personal: this.useVisibility ? !this.defaultPublic : null,

            attachments: []
        })

        return {
            loading: false,
            fileLoading: false,
            gifUploading: false,
            usersShow: false,
            showEditor: false,
            showEditorToolbar: false,
            mobileKeyboardOffset: 0,
            files: [],
            readers: [],
            comment: buildComment(),
            voiceRecording: false,
            voiceUploading: false,
            voiceDurationSeconds: 0,
            voiceBars: buildFallbackVoiceBars(28),
            voiceRecorder: null,
            voiceStream: null,
            voiceChunks: [],
            voiceMimeType: '',
            voiceFileExtension: '',
            voiceSendRequested: false,
            voiceTimerId: null,
            voiceAnimationFrameId: null,
            voiceAudioContext: null,
            voiceAnalyser: null,
            voiceSourceNode: null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        mobileDrawerHeight() {
            return '42vh'
        },
        mobileWrapperStyle() {
            return {
                '--mobile-keyboard-offset': `${this.mobileKeyboardOffset}px`
            }
        },
        showTooltip() {
            return {
                attribute: this.isMobile ? 'visible' : null,
                visible: this.isMobile ? false : null
            }
        }
    },
    created() {
        if (this.parent) {
            eventBusGlob.$emit('CLOSE_MAIN_FORM')
            if (!this.modal)
                this.showEditorHandler()
        }
        if (this.editData) {
            this.editInit()
        }
    },
    watch: {
        editData(val) {
            if (!val) {
                this.clear()
            } else {
                this.editInit()
            }
        }
    },
    methods: {
        ensureDefaultVisibility() {
            if (!this.useVisibility) return
            if (typeof this.comment.is_personal !== 'boolean') {
                this.$set(this.comment, 'is_personal', !this.defaultPublic)
            }
        },
        userTag() {
            if(this.$refs.editor) {
                if(this.comment.text?.length)
                    this.$refs.editor.insertText(' @')
                else
                    this.$refs.editor.insertText('@')
            }
        },
        editInit() {
            const editData = JSON.parse(JSON.stringify(this.editData))
            this.comment = {
                ...editData
            }
            if (editData.attachments?.length)
                this.files = editData.attachments

            this.ensureDefaultVisibility()

            if (!this.showEditor)
                this.showEditor = true
        },
        closeEditorHandler() {
            this.showEditor = false
            this.closeEditorFunc()
            this.clear()
        },
        clear() {
            this.resetVoiceRecorderState()
            this.files = []
            this.readers = []
            this.comment = {
                parent: this.parent ? this.parent.id : null,
                text: '',
                related_object: this.related_object,
                model: this.model,

                is_personal: this.useVisibility ? !this.defaultPublic : null,

                attachments: []
            }
        },
        showEditorHandler() {
            if (!this.parent)
                eventBusGlob.$emit('CLOSE_RES_FORM')

            this.showEditor = true
            const tolbar = localStorage.getItem('showCommentToolbar')
            if (tolbar)
                this.showEditorToolbar = JSON.parse(tolbar)

            // ✅ при открытии редактора ставим дефолт
            this.ensureDefaultVisibility()
        },
        toggleShowToolbar() {
            this.showEditorToolbar = !this.showEditorToolbar
            localStorage.setItem('showCommentToolbar', this.showEditorToolbar)
            this.$nextTick(() => {
                this.$refs.editor.editorFocus()
            })
        },
        updateUsers(val) {
            this.comment.readers = val.map(el => el.id)
        },
        openDrawer() {
            eventBus.$emit('open_user_comment_drawer', this.related_object)
        },
        getPopupContainer() {
            return this.$refs['commentWrapper']
        },
        selectEmoji(emoji) {
            const unicode = emoji?.detail?.unicode || ''
            if (!unicode) return

            const editor = this.$refs.editor
            if (editor?.editorFocus) {
                editor.editorFocus()
            }

            if (editor?.insertText) {
                editor.insertText(unicode)
                return
            }

            this.comment.text = `${this.comment?.text || ''}${unicode}`
        },
        handleGifSelect(gif) {
            this.sendGifComment(gif)
        },
        buildGifUploadFileName(gif = {}) {
            const rawName = String(gif.filename || gif.title || gif.id || `giphy-${Date.now()}`)
                .trim()
                .toLowerCase()
                .replace(/[^a-z0-9-_]+/g, '-')
                .replace(/^-+|-+$/g, '')

            return `${rawName || `giphy-${Date.now()}`}.gif`
        },
        async fetchGifUploadFile(gif = {}) {
            const url = String(gif.downloadUrl || '').trim()
            if (!url) {
                throw new Error('GIF URL is required')
            }

            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`GIF fetch failed with status ${response.status}`)
            }

            const blob = await response.blob()
            const fileName = this.buildGifUploadFileName(gif)

            if (typeof File === 'function') {
                return new File([blob], fileName, {
                    type: blob.type || 'image/gif',
                    lastModified: Date.now()
                })
            }

            blob.name = fileName
            blob.lastModified = Date.now()

            return blob
        },
        async sendGifComment(gif) {
            if (!gif || this.gifUploading || this.loading || this.voiceRecording || this.voiceUploading) {
                return
            }

            const hideLoading = this.$message.loading(this.$t('emoji.sending_gif'), 0)
            this.gifUploading = true

            try {
                const file = await this.fetchGifUploadFile(gif)
                const data = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload',
                    fileName: file.name
                })

                const uploadedFile = Array.isArray(data) ? data[0] : data
                if (!uploadedFile) return

                this.files.push(uploadedFile)
                await this.addHandler()
            } catch (error) {
                errorHandler({ error })
            } finally {
                hideLoading?.()
                this.gifUploading = false
            }
        },
        formatVoiceDuration(seconds) {
            return formatVoiceDuration(seconds)
        },
        resetVoiceBars() {
            this.voiceBars = buildFallbackVoiceBars(28)
        },
        clearVoiceTimer() {
            if (this.voiceTimerId) {
                clearInterval(this.voiceTimerId)
                this.voiceTimerId = null
            }
        },
        cleanupVoiceVisualizer() {
            if (this.voiceAnimationFrameId) {
                cancelAnimationFrame(this.voiceAnimationFrameId)
                this.voiceAnimationFrameId = null
            }

            if (this.voiceSourceNode && typeof this.voiceSourceNode.disconnect === 'function') {
                this.voiceSourceNode.disconnect()
            }

            if (this.voiceAnalyser && typeof this.voiceAnalyser.disconnect === 'function') {
                this.voiceAnalyser.disconnect()
            }

            if (this.voiceAudioContext && typeof this.voiceAudioContext.close === 'function') {
                this.voiceAudioContext.close().catch(() => {})
            }

            this.voiceSourceNode = null
            this.voiceAnalyser = null
            this.voiceAudioContext = null
        },
        cleanupVoiceStream() {
            if (this.voiceStream?.getTracks) {
                this.voiceStream.getTracks().forEach(track => {
                    try {
                        track.stop()
                    } catch (error) {}
                })
            }
            this.voiceStream = null
        },
        resetVoiceRecorderState() {
            this.voiceRecording = false
            this.voiceUploading = false
            this.voiceDurationSeconds = 0
            this.voiceSendRequested = false
            this.voiceRecorder = null
            this.voiceChunks = []
            this.voiceMimeType = ''
            this.voiceFileExtension = ''
            this.clearVoiceTimer()
            this.cleanupVoiceVisualizer()
            this.cleanupVoiceStream()
            this.resetVoiceBars()
        },
        startVoiceTimer() {
            this.clearVoiceTimer()
            this.voiceTimerId = setInterval(() => {
                this.voiceDurationSeconds += 1
            }, 1000)
        },
        startVoiceVisualizer(stream) {
            const AudioContextCtor = window.AudioContext || window.webkitAudioContext
            if (!AudioContextCtor) {
                this.resetVoiceBars()
                return
            }

            try {
                this.voiceAudioContext = new AudioContextCtor()
                this.voiceAnalyser = this.voiceAudioContext.createAnalyser()
                this.voiceAnalyser.fftSize = 128
                this.voiceSourceNode = this.voiceAudioContext.createMediaStreamSource(stream)
                this.voiceSourceNode.connect(this.voiceAnalyser)

                const buffer = new Uint8Array(this.voiceAnalyser.frequencyBinCount)

                const draw = () => {
                    if (!this.voiceAnalyser) return

                    this.voiceAnalyser.getByteFrequencyData(buffer)

                    const step = Math.max(1, Math.floor(buffer.length / this.voiceBars.length))
                    this.voiceBars = this.voiceBars.map((bar, index) => {
                        const start = index * step
                        const end = Math.min(start + step, buffer.length)
                        let sum = 0

                        for (let i = start; i < end; i += 1) {
                            sum += buffer[i]
                        }

                        const average = end > start ? sum / (end - start) : 0
                        return Math.max(8, Math.min(36, Math.round((average / 255) * 36)))
                    })

                    this.voiceAnimationFrameId = requestAnimationFrame(draw)
                }

                draw()
            } catch (error) {
                this.resetVoiceBars()
            }
        },
        async startVoiceRecording() {
            if (this.voiceRecording || this.voiceUploading) return
            if (this.loading) return

            const hasMediaDevices = !!navigator.mediaDevices?.getUserMedia
            const hasMediaRecorder = typeof window.MediaRecorder !== 'undefined'
            const isSecureOrigin = typeof window === 'undefined'
                ? true
                : window.isSecureContext || ['localhost', '127.0.0.1'].includes(window.location.hostname)

            if (!isSecureOrigin) {
                this.$message.error('Voice recording requires HTTPS or localhost')
                return
            }

            if (!hasMediaDevices || !hasMediaRecorder) {
                this.$message.error('Voice recording is not supported in this browser')
                return
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                })

                const { mimeType, extension } = getVoiceMimeConfig()
                const recorder = mimeType
                    ? new window.MediaRecorder(stream, { mimeType })
                    : new window.MediaRecorder(stream)

                this.voiceStream = stream
                this.voiceRecorder = recorder
                this.voiceChunks = []
                this.voiceMimeType = mimeType || recorder.mimeType || 'audio/webm'
                this.voiceFileExtension = extension || 'webm'
                this.voiceDurationSeconds = 0
                this.voiceSendRequested = false
                this.voiceRecording = true
                this.voiceUploading = false
                this.resetVoiceBars()

                recorder.ondataavailable = event => {
                    if (event.data?.size) {
                        this.voiceChunks.push(event.data)
                    }
                }

                recorder.onstop = () => {
                    this.handleVoiceRecorderStop()
                }

                recorder.start(250)
                this.startVoiceTimer()
                this.startVoiceVisualizer(stream)
            } catch (error) {
                this.resetVoiceRecorderState()
                this.$message.error('Microphone access is unavailable')
            }
        },
        cancelVoiceRecording() {
            if (this.voiceUploading) return

            this.voiceSendRequested = false

            if (this.voiceRecorder && this.voiceRecorder.state !== 'inactive') {
                this.voiceRecorder.stop()
                return
            }

            this.resetVoiceRecorderState()
        },
        async sendVoiceRecording() {
            if (this.voiceUploading) return
            if (!this.voiceRecording && !this.voiceRecorder) return

            this.voiceSendRequested = true
            this.voiceUploading = true
            this.voiceRecording = false
            this.clearVoiceTimer()

            if (this.voiceRecorder && this.voiceRecorder.state !== 'inactive') {
                this.voiceRecorder.stop()
                return
            }

            await this.handleVoiceRecorderStop()
        },
        async handleVoiceRecorderStop() {
            const shouldSend = this.voiceSendRequested
            const chunks = Array.isArray(this.voiceChunks) ? this.voiceChunks.slice() : []
            const mimeType = this.voiceMimeType || this.voiceRecorder?.mimeType || 'audio/webm'
            const extension = this.voiceFileExtension || 'webm'
            let shouldSubmitComment = false

            this.clearVoiceTimer()
            this.cleanupVoiceVisualizer()
            this.cleanupVoiceStream()
            this.voiceRecorder = null

            if (!shouldSend) {
                this.resetVoiceRecorderState()
                return
            }

            try {
                const blob = new Blob(chunks, { type: mimeType })
                const file = buildVoiceUploadFile(blob, extension, mimeType)
                const data = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload',
                    fileName: file.name,
                    extraData: {
                        is_voice: true
                    }
                })

                const uploadedFile = Array.isArray(data) ? data[0] : data
                if (uploadedFile) {
                    this.files.push({ ...uploadedFile, is_voice: true })
                    shouldSubmitComment = !this.editData
                }
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.resetVoiceRecorderState()
            }

            if (shouldSubmitComment) {
                await this.addHandler()
            }
        },
        handleFileUpload() {
            const files = this.$refs[`com_file_${this.related_object}`].files
            if (files.length) {
                Array.prototype.forEach.call(files, async (item, i) => {
                    try {
                        this.fileLoading = true
                        const data = await this.$uploadFile({
                            file: files[i],
                            url: '/common/upload/',
                            fieldName: 'upload',
                            fileName: files[i].name
                        })
                        if (data?.length)
                            this.files.push(data[0])

                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.fileLoading = false
                    }
                })
            }
        },
        dropInput(e) {
            if (e.dataTransfer?.files?.length) {
                this.$refs[`com_file_${this.related_object}`].files = e.dataTransfer.files
                this.handleFileUpload()
            }
        },
        getMentionIds(text) {
            if (!text) return []

            const doc = new DOMParser().parseFromString(String(text), 'text/html')

            return Array.from(
                new Set(
                    Array.from(
                        doc.querySelectorAll('span.user_chat_mention[data-id]')
                    ).map(el => el.getAttribute('data-id'))
                )
            )
        },
        hasCommentText(text) {
            const plain = String(text || '')
                .replace(/<[^>]*>/g, ' ')
                .replace(/&nbsp;/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()

            return Boolean(plain.length)
        },
        async addHandler() {
            if (this.loading) return false
            if (this.voiceRecording || this.voiceUploading) {
                await this.sendVoiceRecording()
                return false
            }

            let editorText = this.comment.text
            if (!editorText && this.$refs.editor?.editorRef?.getData) {
                editorText = this.$refs.editor.editorRef.getData()
            }

            const hasText = this.hasCommentText(editorText)
            const hasFiles = Boolean(this.files?.length)
            if (!(hasText || hasFiles)) return false

            const wasEditorVisible = this.showEditor
            if (wasEditorVisible) {
                this.showEditor = false
            }

            try {
                this.loading = true
                const commentData = JSON.parse(JSON.stringify(this.comment))
                commentData.text = editorText || ''

                // ✅ если is_personal = null/undefined — не отправляем поле на бэк
                if (commentData.is_personal == null) {
                    delete commentData.is_personal
                }

                const mentionIds = this.getMentionIds(commentData.text)
                commentData['mentions'] = mentionIds || []

                if (this.useVisibility && typeof commentData.is_personal !== 'boolean')
                    commentData.is_personal = !this.defaultPublic

                if (this.files?.length)
                    commentData.attachments = this.files.map(file => file.id)

                if (this.editData) {
                    const { data } = await this.$http.put(`/comments/${commentData.id}/update/`, commentData)
                    if (data) {
                        //this.updateComment(data)
                        this.closeEditorHandler()
                        return true
                    }
                } else {
                    const { data } = await this.$http.post('/comments/create/', commentData)
                    if (data) {
                        this.pushNewComment(data)
                        this.closeEditorHandler()
                        return true
                    }
                }
            } catch (error) {
                errorHandler({ error })
                if (wasEditorVisible) {
                    this.showEditor = true
                }
                return false
            } finally {
                this.loading = false
            }
            return false
        },
        async submitFromDrawer() {
            return this.addHandler()
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        updateMobileViewportOffset() {
            if (!this.isMobile || !window.visualViewport) {
                this.mobileKeyboardOffset = 0
                return
            }
            const viewport = window.visualViewport
            const offset = Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop)
            this.mobileKeyboardOffset = offset
        }
    },
    mounted() {
        eventBusGlob.$on('CLOSE_MAIN_FORM', () => {
            this.closeEditorHandler()
        })
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', this.updateMobileViewportOffset)
            window.visualViewport.addEventListener('scroll', this.updateMobileViewportOffset)
        }
        this.updateMobileViewportOffset()
    },
    beforeDestroy() {
        this.resetVoiceRecorderState()
        eventBusGlob.$off('CLOSE_MAIN_FORM')
        if (window.visualViewport) {
            window.visualViewport.removeEventListener('resize', this.updateMobileViewportOffset)
            window.visualViewport.removeEventListener('scroll', this.updateMobileViewportOffset)
        }
    }
}
</script>

<style lang="scss" scoped>
.comment_text{
    border: 1px solid var(--borderColor);
    border-radius: var(--borderRadius);
    background: #ffffff;
    &.place{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            border-color: var(--blue);
        }
    }
    &__placeholder{
        cursor: pointer;
        padding: 10px 15px;
        color: #000000;
        opacity: 0.4;
        text-align: left;
        background: #ffffff;
    }
    &__footer{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        padding: 2px 15px 3px 15px;
        &::v-deep{
            .ant-badge-count{
                font-size: 10px !important;
                min-width: 17px;
                height: 17px;
                padding: 0 6px;
                line-height: 17px;
            }
        }
    }
    .ck_wrap{
        &:not(.show_toolbar){
            &::v-deep{
                .ck-editor__top{
                    display: none;
                }
            }
        }
        &::v-deep{
            .ck-content{
                box-shadow: initial!important;
                border: 0px!important;
            }
        }
    }
    &::v-deep{
        .ck-dropdown__panel.ck-dropdown__panel_ne, .ck.ck-dropdown .ck-dropdown__panel.ck-dropdown__panel_se{
            left: initial;
            right: 0;
        }
        .ant-btn{
            &.active_btn{
                color: var(--blue);
            }
        }
        .ck-toolbar,
        .ck-content{
            border: 0px;
            max-height: 300px;
        }
        .ck-content{
            &.ck-focused{
                border: 0px;
                box-shadow: initial;
            }
            &.ck-editor__editable_inline{
                padding-left: 15px;
                padding-right: 15px;
            }
        }
        .ck.ck-code-block-dropdown .ck-dropdown__panel{
            max-height: 100px;
        }
        .ck.ck-color-grid{
            max-height: 60px;
            overflow-y: auto;
            overflow-x: hidden;
        }
    }
}

.voice_record_panel{
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1 1 100%;
    min-width: 0;
    margin-right: auto;
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

.voice_record_btn--active{
    color: #ff4d4f;
    border-color: rgba(255, 77, 79, 0.28);
}

.comment_visibility{
    display: flex;
    justify-content: flex-end;

    .visibility_row{
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .visibility_text{
        display: flex;
        align-items: center;
        font-size: 12px;
        user-select: none;
        color: var(--gray);

        &.is_private{
            color: var(--gray);
        }
        &.is_public{
            color: var(--gray);
        }
    }
}

.mobile_comment_drawer{
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.mobile_drawer_handle_area{
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.mobile_drawer_handle{
    background: #888;
    height: 5px;
    width: 50px;
    border-radius: 5px;
    opacity: 0.5;
}

.mobile_comment_content{
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    padding: 0 10px;
}

    .mobile_comment_editor{
        flex: 1;
        min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 0;
    background: #fff;
        .comment_text__footer{
            margin-top: auto;
            border-top: 1px solid #e6e6e8;
            padding-top: 8px;
            padding-bottom: 8px;
        }
    .ck_wrap{
        flex: 1;
        min-height: 0;
        &::v-deep{
            .ck-editor{
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .ck-editor__main{
                flex: 1;
                min-height: 0;
            }
            .ck-content{
                height: 100%;
                max-height: none;
                min-height: 120px;
                overflow-y: auto;
            }
            .ck-toolbar,
            .ck-content{
                border: 0 !important;
                box-shadow: none !important;
            }
            .ck.ck-editor__editable_inline{
                padding: 0px;
            }
        }
    }
}

.mobile_comment_files_wrap{
    flex-shrink: 0;
    padding: 8px 2px 0 2px;
    overflow: hidden;
}

.mobile_comment_footer{
    flex-shrink: 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 10px 12px calc(10px + env(safe-area-inset-bottom, 0px)) 12px;
    border-top: 1px solid var(--borderColor);
    background: #fff;
}
</style>

<style lang="scss">
.mobile-comment-drawer-wrap {
    .ant-drawer-content-wrapper {
        bottom: var(--mobile-keyboard-offset, 0px);
        max-height: calc(95% - constant(safe-area-inset-top) - constant(safe-area-inset-bottom));
        max-height: calc(95% - env(safe-area-inset-top) - env(safe-area-inset-bottom));
        box-shadow: none !important;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body {
        overflow: hidden;
        height: 100%;
    }
    .ant-drawer-content {
        border-radius: 12px 12px 0 0 !important;
        background: transparent;
    }
    .ant-drawer-body {
        background: #fff;
        border-radius: 12px 12px 0 0;
        overflow: hidden;
    }
    .drawer_body {
        overflow: hidden !important;
    }
    .mobile_files_attach {
        .attached_files {
            display: flex;
            flex-wrap: nowrap;
            gap: 8px;
            overflow-x: auto;
            overflow-y: hidden;
            padding-bottom: 6px;
            -webkit-overflow-scrolling: touch;
            scroll-snap-type: x proximity;
            .attached_file {
                flex: 0 0 96px;
                scroll-snap-align: start;
            }
        }
        .file-grid {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            overflow-y: hidden;
            .file_p_card {
                flex: 0 0 160px;
                max-height: none;
            }
        }
    }
}
</style>
