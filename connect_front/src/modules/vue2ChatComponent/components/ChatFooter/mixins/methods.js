import { isFileImage } from '../../../utils'
import { mapMutations } from 'vuex'
import { debounce } from 'lodash'
import ChatEventBus from '../../../utils/ChatEventBus'
import { errorHandler } from '@/utils/index.js'
import {
    buildVoiceAudioConstraints,
    buildVoiceUploadFile as buildVoiceUploadFileHelper,
    formatVoiceDuration as formatVoiceDurationHelper,
    getVoiceMimeConfig as getVoiceMimeConfigHelper,
    getVoiceRecordingErrorMessage
} from '@/utils/voice'
export default {
    methods: {
        ...mapMutations({
            CHANGE_CHAT_MESSAGE: 'chat/CHANGE_CHAT_MESSAGE',
            SET_CHAT_MESSAGE: 'chat/SET_CHAT_MESSAGE',
            CHANGE_CHAT_MESSAGE_MODAL: 'chat/CHANGE_CHAT_MESSAGE_MODAL',
            SET_CHAT_MESSAGE_MODAL: 'chat/SET_CHAT_MESSAGE_MODAL',
            PUSH_FILE_LIST: 'chat/PUSH_FILE_LIST',
            FILE_CHANGE_FIELD: 'chat/FILE_CHANGE_FIELD',
            SET_FILE_MODAL: 'chat/SET_FILE_MODAL',
            FILE_DELETE: 'chat/FILE_DELETE',
            FILE_DELETE_BY_KEY: 'chat/FILE_DELETE_BY_KEY',
            SET_FILE_LIST: 'chat/SET_FILE_LIST',
            setReplyMessage: 'chat/setReplyMessage',
            setReplyMessageModal: 'chat/setReplyMessageModal',
            DELETE_REPLY_MESSAGE: 'chat/DELETE_REPLY_MESSAGE',
            DELETE_REPLY_MESSAGE_MODAL: 'chat/DELETE_REPLY_MESSAGE_MODAL',
            clearInput: "chat/CLEAR_INPUT",
            addLastMessage: 'chat/addLastMessage'
        }),
        buildOptimisticMessage(message) {
            const now = new Date()
            const optimisticUid = `tmp-${now.getTime()}-${Math.random().toString(36).slice(2, 10)}`

            return {
                ...message,
                client_uid: message?.client_uid || optimisticUid,
                message_uid: message?.message_uid || optimisticUid,
                created: message?.created || now.toISOString(),
                is_new: true,
                is_optimistic: true
            }
        },
        pushOptimisticMessage(message) {
            const optimisticMessage = this.buildOptimisticMessage(message)

            this.$store.commit('chat/ADD_MESSAGE', optimisticMessage)
            this.addLastMessage({
                ...optimisticMessage,
                message_author: optimisticMessage.message_author
                    ? { ...optimisticMessage.message_author }
                    : null
            })
        },
        getVoiceMimeConfig() {
            return getVoiceMimeConfigHelper()
        },
        formatVoiceDuration(seconds) {
            return formatVoiceDurationHelper(seconds)
        },
        resetVoiceBars() {
            this.voiceBars = Array.from({ length: 28 }, () => 10)
        },
        startVoiceProcessingAnimation() {
            this.stopVoiceProcessingAnimation()
            let frame = 0
            this.voiceProcessingAnimationId = setInterval(() => {
                frame += 1
                this.voiceBars = Array.from(
                    { length: 28 },
                    (_, index) => 10 + Math.round((Math.sin(index / 2.4 + frame * 0.7) + 1) * 10)
                )
            }, 120)
        },
        stopVoiceProcessingAnimation() {
            if (this.voiceProcessingAnimationId) {
                clearInterval(this.voiceProcessingAnimationId)
                this.voiceProcessingAnimationId = null
            }
        },
        clearVoiceTimer() {
            if (this.voiceTimerId) {
                clearInterval(this.voiceTimerId)
                this.voiceTimerId = null
            }
        },
        buildVoiceUploadFile(blob, extension, mimeType) {
            return buildVoiceUploadFileHelper(blob, extension, mimeType)
        },
        resolveVoiceFileExtension(mimeType = '') {
            const normalizedMimeType = String(mimeType || '')

            if (normalizedMimeType.includes('mp4')) {
                return 'm4a'
            }

            if (normalizedMimeType.includes('ogg')) {
                return 'ogg'
            }

            if (normalizedMimeType.includes('webm')) {
                return 'webm'
            }

            return 'm4a'
        },
        createVoiceRecorder(stream, preferredMimeType = '', preferredExtension = 'm4a') {
            let recorder = null
            let resolvedMimeType = preferredMimeType || ''
            let resolvedExtension = preferredExtension || 'm4a'

            try {
                recorder = preferredMimeType
                    ? new window.MediaRecorder(stream, { mimeType: preferredMimeType })
                    : new window.MediaRecorder(stream)
            } catch (error) {
                recorder = new window.MediaRecorder(stream)
                resolvedMimeType = recorder.mimeType || ''
                resolvedExtension = this.resolveVoiceFileExtension(resolvedMimeType)
            }

            if (!resolvedMimeType) {
                resolvedMimeType = recorder.mimeType || ''
            }

            if (!resolvedExtension) {
                resolvedExtension = this.resolveVoiceFileExtension(resolvedMimeType)
            }

            return {
                recorder,
                resolvedMimeType,
                resolvedExtension
            }
        },
        async waitForLiveVoiceStream(stream) {
            const getLiveTrack = () => stream?.getAudioTracks?.().find(track => track.readyState === 'live' && track.enabled !== false)

            if (getLiveTrack()) {
                return true
            }

            await new Promise(resolve => requestAnimationFrame(() => resolve()))

            if (getLiveTrack()) {
                return true
            }

            await new Promise(resolve => setTimeout(resolve, 60))
            return Boolean(getLiveTrack())
        },
        async startVoiceRecorderWithFallback(stream, preferredMimeType = '', preferredExtension = 'm4a') {
            const attempts = [
                { useDelay: false, timeslice: undefined },
                { useDelay: true, timeslice: undefined },
                { useDelay: true, timeslice: 1000 }
            ]

            let lastError = null

            for (const attempt of attempts) {
                if (attempt.useDelay) {
                    await new Promise(resolve => setTimeout(resolve, 60))
                }

                const payload = this.createVoiceRecorder(stream, preferredMimeType, preferredExtension)

                try {
                    if (typeof attempt.timeslice === 'number') {
                        payload.recorder.start(attempt.timeslice)
                    } else {
                        payload.recorder.start()
                    }

                    return payload
                } catch (error) {
                    lastError = error
                }
            }

            throw lastError || new Error('Failed to start voice recorder')
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
            this.voiceActionType = null
            this.voiceProcessingStage = null
            this.voiceRecorder = null
            this.voiceChunks = []
            this.voiceMimeType = ''
            this.voiceFileExtension = ''
            this.clearVoiceTimer()
            this.stopVoiceProcessingAnimation()
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
        async startVoiceRecording(mode = 'message') {
            if (this.voiceRecording || this.voiceUploading) return
            if (this.message?.edit || this.fileModal) return

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

            let stream = null

            try {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({
                        audio: buildVoiceAudioConstraints()
                    })
                } catch (error) {
                    const isConstraintError = ['OverconstrainedError', 'ConstraintNotSatisfiedError', 'TypeError'].includes(String(error?.name || ''))

                    if (!isConstraintError) {
                        throw error
                    }

                    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
                }

                const { mimeType, extension } = this.getVoiceMimeConfig()
                const hasLiveTrack = await this.waitForLiveVoiceStream(stream)
                if (!hasLiveTrack) {
                    const streamError = new Error('Voice stream is not active')
                    streamError.name = 'InvalidStateError'
                    throw streamError
                }

                const {
                    recorder,
                    resolvedMimeType,
                    resolvedExtension
                } = await this.startVoiceRecorderWithFallback(stream, mimeType, extension || 'm4a')

                this.voiceStream = stream
                this.voiceRecorder = recorder
                this.voiceChunks = []
                this.voiceMimeType = resolvedMimeType || recorder.mimeType || 'audio/mp4'
                this.voiceFileExtension = resolvedExtension || 'm4a'
                this.voiceDurationSeconds = 0
                this.voiceSendRequested = false
                this.voiceActionType = mode
                this.voiceRecording = true
                this.voiceUploading = false
                this.resetVoiceBars()

                recorder.ondataavailable = event => {
                    if (event.data?.size) {
                        this.voiceChunks.push(event.data)
                    }
                }

                recorder.onerror = event => {
                    const recorderError = event?.error || event

                    this.resetVoiceRecorderState()
                    this.$message.error(getVoiceRecordingErrorMessage(recorderError))
                }

                recorder.onstop = () => {
                    this.handleVoiceRecorderStop()
                }
                this.startVoiceTimer()
                this.startVoiceVisualizer(stream)
            } catch (error) {
                console.error('Voice recording start failed', error)
                this.resetVoiceRecorderState()
                this.$message.error(getVoiceRecordingErrorMessage(error))
            }
        },
        cancelVoiceRecording() {
            if (this.voiceUploading) return

            if (this.voiceActionType === 'text') {
                this.voiceSendRequested = true
                this.voiceUploading = true
                this.voiceRecording = false
                this.clearVoiceTimer()
                this.cleanupVoiceVisualizer()
                this.resetVoiceBars()

                if (this.voiceRecorder && this.voiceRecorder.state !== 'inactive') {
                    this.voiceRecorder.stop()
                    return
                }

                this.handleVoiceRecorderStop()
                return
            }

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
            this.cleanupVoiceVisualizer()
            this.resetVoiceBars()

            if (this.voiceRecorder && this.voiceRecorder.state !== 'inactive') {
                this.voiceRecorder.stop()
                return
            }

            await this.handleVoiceRecorderStop()
        },
        async handleVoiceRecorderStop() {
            const shouldSend = this.voiceSendRequested
            const chunks = Array.isArray(this.voiceChunks) ? this.voiceChunks.slice() : []
            const mimeType = this.voiceMimeType || this.voiceRecorder?.mimeType || 'audio/mp4'
            const extension = this.voiceFileExtension || 'm4a'

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
                const file = this.buildVoiceUploadFile(blob, extension, mimeType)
                if (this.voiceActionType === 'text') {
                    await this.uploadVoiceTextInput(file)
                } else {
                    await this.uploadVoiceMessage(file)
                }
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.resetVoiceRecorderState()
            }
        },
        async startVoiceTextInput() {
            return this.startVoiceRecording('text')
        },
        resolveRecognizedVoiceText(payload) {
            if (typeof payload === 'string') {
                return payload.trim()
            }

            if (Array.isArray(payload)) {
                return payload
                    .map(item => this.resolveRecognizedVoiceText(item))
                    .filter(Boolean)
                    .join('\n')
                    .trim()
            }

            if (payload && typeof payload === 'object') {
                const directValue = [
                    payload.text,
                    payload.recognized_text,
                    payload.transcript,
                    payload.result,
                    payload.message
                ].find(value => typeof value === 'string' && value.trim())

                if (directValue) {
                    return directValue.trim()
                }

                const nestedValue = [payload.data, payload.response]
                    .map(value => this.resolveRecognizedVoiceText(value))
                    .find(Boolean)

                if (nestedValue) {
                    return nestedValue
                }
            }

            return ''
        },
        async animateVoiceInputTextInsertion(text) {
            const editor = this.$refs.message_input
            if (!text) return

            const plainInputValue = String(this.message?.text || '')
                .replace(/<[^>]*>/g, ' ')
                .replace(/&nbsp;/gi, ' ')
                .trim()
            const prefix = plainInputValue ? ' ' : ''
            const textToInsert = `${prefix}${text}`
            const step = textToInsert.length > 180 ? 4 : textToInsert.length > 80 ? 3 : 2

            this.voiceProcessingStage = 'typing'

            if (!editor) {
                this.message.text = `${this.message?.text || ''}${textToInsert}`
                return
            }

            editor.focus()

            for (let index = 0; index < textToInsert.length; index += step) {
                editor.insertText(textToInsert.slice(index, index + step))
                await new Promise(resolve => setTimeout(resolve, 18))
            }
        },
        async uploadVoiceMessage(file) {
            if (!file) return

            let timeout = 0
            if (this.activeChat.no_create) {
                timeout = 300
                this.oldChat = JSON.parse(JSON.stringify(this.activeChat))
                await this.createNewChat(this.activeChat)
                setTimeout(() => {
                    this.$store.commit('chat/setSidebarActiveTab', 1)
                    this.setQueryId(this.activeChat)
                }, timeout)
            }

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
            if (!uploadedFile) return

            setTimeout(() => {
                const author = JSON.parse(JSON.stringify(this.$store.state.user.user))
                const replyMessage = this.replyMessageData || this.replyMessageModalData
                const chatUid = this.activeChat.chat_uid

                this.createMessage({
                    mentions: [],
                    message_author: {
                        ...author,
                        full_name: author.first_name + ' ' + author.last_name
                    },
                    text: '',
                    chat: chatUid,
                    chat_uid: chatUid,
                    is_system: false,
                    is_pinned: false,
                    is_deleted: false,
                    message_reply: replyMessage ? JSON.parse(JSON.stringify(replyMessage)) : null,
                    attachments: [{ ...uploadedFile, is_new: true, is_voice: true }]
                })

                this.clearDraftByChatUid(chatUid)
                if (this.oldChat?.chat_uid) {
                    this.clearDraftByChatUid(this.oldChat.chat_uid)
                }
                this.DELETE_REPLY_MESSAGE_MODAL(chatUid)
                this.DELETE_REPLY_MESSAGE(chatUid)
                ChatEventBus.$emit('arreaScrollDown', true)
                this.$nextTick(() => {
                    this.$refs['message_input']?.focus()
                })
            }, timeout)
        },
        async uploadVoiceTextInput(file) {
            if (!file) return

            this.voiceProcessingStage = 'recognizing'

            try {
                const uploadResponse = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload',
                    fileName: file.name,
                    extraData: {
                        is_voice: true,
                        is_voice_input: true
                    }
                })

                const recognizedText = this.resolveRecognizedVoiceText(uploadResponse)
                if (!recognizedText) {
                    this.$message.warning(this.$t('chat.voice_input_empty_text'))
                    return
                }

                await this.animateVoiceInputTextInsertion(recognizedText)
                this.$nextTick(() => {
                    this.$refs['message_input']?.focus()
                })
            } finally {
                this.resetVoiceBars()
            }
        },
        uploadFilesFromEditor(files) {
            if (!files || !files.length) return

            const dt = new DataTransfer()
            files.forEach(f => dt.items.add(f))

            this.handleFileUpload({ target: { files: dt.files } })
        },
        closeEdit() {
            this.$store.commit('chat/CLEAR_EDIT_MESSAGE', {
                id: this.activeChat.chat_uid
            })
        },
        behaviorType() {
            this.behaviorStatus = !this.behaviorStatus
            localStorage.setItem('behaviorType', this.behaviorStatus)
        },
        userTag() {
            if(this.$refs.message_input) {
                if(this.message.text?.length)
                    this.$refs.message_input.insertText(' @')
                else
                    this.$refs.message_input.insertText('@')
            }
        },
        // Emoji
        selectEmoji(emoji) {
            if(this.$refs.message_input)
                this.$refs.message_input.insertText(emoji.detail.unicode)

            if(this.$refs.message_input_modal)
                this.$refs.message_input_modal.insertText(emoji.detail.unicode)
        },
        handleGifSelect(gif) {
            this.sendGifMessage(gif)
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
        async sendGifMessage(gif) {
            if (!gif || this.gifUploading) {
                return
            }

            const hideLoading = this.$message.loading(this.$t('emoji.sending_gif'), 0)
            this.gifUploading = true

            try {
                const file = await this.fetchGifUploadFile(gif)
                let timeout = 0

                if (this.activeChat.no_create) {
                    timeout = 300
                    this.oldChat = JSON.parse(JSON.stringify(this.activeChat))
                    await this.createNewChat(this.activeChat)
                    setTimeout(() => {
                        this.$store.commit('chat/setSidebarActiveTab', 1)
                        this.setQueryId(this.activeChat)
                    }, timeout)
                }

                const uploadResponse = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload',
                    fileName: file.name
                })

                const uploadedFile = Array.isArray(uploadResponse) ? uploadResponse[0] : uploadResponse
                if (!uploadedFile) {
                    return
                }

                setTimeout(() => {
                    const author = JSON.parse(JSON.stringify(this.$store.state.user.user))
                    const chatUid = this.activeChat.chat_uid
                    const replyMessage = this.replyMessageData || this.replyMessageModalData

                    this.createMessage({
                        mentions: [],
                        message_author: {
                            ...author,
                            full_name: author.first_name + ' ' + author.last_name
                        },
                        text: '',
                        chat: chatUid,
                        chat_uid: chatUid,
                        is_system: false,
                        is_pinned: false,
                        is_deleted: false,
                        message_reply: replyMessage ? JSON.parse(JSON.stringify(replyMessage)) : null,
                        attachments: [{ ...uploadedFile, is_new: true }]
                    })

                    this.DELETE_REPLY_MESSAGE_MODAL(chatUid)
                    this.DELETE_REPLY_MESSAGE(chatUid)
                    ChatEventBus.$emit('arreaScrollDown', true)
                    this.syncDraftRemovalState()
                    this.$nextTick(() => {
                        this.$refs['message_input']?.focus()
                    })
                }, timeout)
            } catch (error) {
                errorHandler({ error })
            } finally {
                hideLoading?.()
                this.gifUploading = false
            }
        },
        // Delete filin from modal
        deleteFile(file) {
            this.FILE_DELETE_BY_KEY({
                id: this.activeChat.chat_uid,
                fileId: file.iid
            })

            if (!this.fileList?.length) {
                this.closeFileModal()
            }
        },
        // Close from file modal
        closeFileModal() {
            this.SET_FILE_MODAL({
                id: this.activeChat.chat_uid,
                value: false
            })
            this.FILE_DELETE(this.activeChat.chat_uid)
            if (this.messageModal?.text) {
                this.message.text = this.messageModal.text
                this.messageModal.text = ''
            }
            if (this.replyMessageModalData) {
                this.setReplyMessage({
                    id: this.activeChat.chat_uid,
                    mesage: this.replyMessageModalData
                })
                this.DELETE_REPLY_MESSAGE_MODAL(this.activeChat.chat_uid)
            }

            if(!this.isMobile) {
                this.$nextTick(() => {
                    this.$refs['message_input']?.focus()
                })
            }
        },
        handleFileUpload(event) {
            const files = Object.values(event?.target?.files || [])
            if (!files.length) return

            const chatId = this.activeChat.chat_uid
            const isEdit = !!this.message?.edit

            if (!isEdit) {
                if (this.fileList.length >= 10) {
                    this.$message.warning(this.$t('chat.file_max_count', { count: 10 }))
                    this.clearFileInputs()
                    return
                }
            }

            files.forEach(async (item, i) => {
                const iid = Date.now() + Math.floor(Math.random() * Math.floor(20)) + Math.random()
                const type = isFileImage(files[i])

                if (!isEdit) {
                    this.PUSH_FILE_LIST({
                        id: chatId,
                        file: {
                            image: type,
                            name: files[i].name,
                            type: files[i].name.split('.')[1],
                            loading: true,
                            percent: 0,
                            file: null,
                            iid
                        }
                    })

                    if (!this.fileModal) {
                        this.SET_FILE_MODAL({
                            id: chatId,
                            value: true
                        })

                        if (this.message.text) {
                            this.messageModal.text = this.message.text
                            this.message.text = ''
                        }

                        if (this.replyMessageData) {
                            this.setReplyMessageModal({
                                id: chatId,
                                mesage: this.replyMessageData
                            })
                            this.DELETE_REPLY_MESSAGE(chatId)
                        }
                    }
                }

                try {
                    const data = await this.$uploadFile({
                        file: files[i],
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: files[i].name,
                        onProgress: ({ percent }) => {
                            if (!isEdit) {
                                this.FILE_CHANGE_FIELD({
                                    id: chatId,
                                    field: 'percent',
                                    fileId: iid,
                                    value: percent
                                })
                            }
                        }
                    })

                    const uploadedFile = Array.isArray(data) ? data[0] : data
                    const uploaded = uploadedFile ? { ...uploadedFile, is_new: true } : null
                    if (!uploaded) return

                    if (isEdit) {
                        this.$store.commit('chat/ADD_CHAT_MESSAGE_ATTACHMENT', {
                            id: chatId,
                            attachment: uploaded
                        })
                        ChatEventBus.$emit('inputFocus')
                    } else {
                        this.FILE_CHANGE_FIELD({
                            id: chatId,
                            field: 'file',
                            fileId: iid,
                            value: uploaded
                        })
                        this.FILE_CHANGE_FIELD({
                            id: chatId,
                            field: 'loading',
                            fileId: iid,
                            value: false
                        })
                        this.FILE_CHANGE_FIELD({
                            id: chatId,
                            field: 'percent',
                            fileId: iid,
                            value: 100
                        })
                    }

                    this.clearFileInputs()
                } catch (error) {
                    errorHandler({error})
                }
            })
        },
        clearFileInputs() {
            if(this.$refs['file_upload_modal']?.value)
                this.$refs['file_upload_modal'].value = ''
            if(this.$refs['file_upload']?.value)
                this.$refs['file_upload'].value = ''
        },
        keydownHandler(e) {
            if (e.keyCode === 13 && e.shiftKey) {
                e.preventDefault()
                this.sendMessage()
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
        sendEditMessage() {
            const message = JSON.parse(JSON.stringify(this.message))
            const chatUid = message.chat_uid || message.chat || this.activeChat?.chat_uid

            if(message.id)
                delete message.id
            if (chatUid) {
                message.chat_uid = chatUid
                message.chat = chatUid
            }

            const text = this.getMessageText()
            const mentionIds = this.getMentionIds(text)
            message['mentions'] = mentionIds || []

            this.$socket.client.emit("message_update", message)
            this.resetComposer()
            this.closeEdit()
        },
        resetComposer() {
            const oldChatUid = this.oldChat?.chat_uid || null

            this.clearInput(this.activeChat.chat_uid)

            if (oldChatUid) {
                this.clearInput(oldChatUid)
                this.oldChat = null
            }

            this.$refs.message_input?.clearContent?.()
            this.$refs.message_input_modal?.clearContent?.()
            this.message.text = ""
            this.messageModal.text = ""
            this.editorKey += 1
            this.clearDraftByChatUid(this.activeChat.chat_uid)

            if (oldChatUid) {
                this.clearDraftByChatUid(oldChatUid)
            }
        },
        async sendMessage() {
            try {
                if (this.checkEmptyMessage) {
                    if(this.message.edit) {
                        this.sendEditMessage()
                        return
                    }

                    const activeChat = JSON.parse(JSON.stringify(this.activeChat))
                    const chatUid = activeChat.chat_uid
                    const author = JSON.parse(JSON.stringify(this.$store.state.user.user))
                    const text = this.getMessageText()
                    const mentionIds = this.getMentionIds(text)
                    const replyMessage = this.replyMessageData || this.replyMessageModalData
                    const attachments = this.getFileListSend(chatUid)

                    const data = {
                        mentions: mentionIds || [],
                        message_author: {
                            ...author,
                            full_name: author.first_name + ' ' + author.last_name
                        },
                        text,
                        chat: chatUid,
                        chat_uid: chatUid,
                        is_system: false,
                        is_pinned: false,
                        is_deleted: false,
                        message_reply: replyMessage ? JSON.parse(JSON.stringify(replyMessage)) : null,
                        attachments: Array.isArray(attachments) ? attachments.slice() : []
                    }

                    const payloads = this.buildMessagePayloads(data)
                    this.pushMessagePayloads(payloads)
                    this.resetComposer()
                    this.closeFileModal()
                    this.DELETE_REPLY_MESSAGE_MODAL(chatUid)
                    this.DELETE_REPLY_MESSAGE(chatUid)
                    ChatEventBus.$emit('arreaScrollDown', true)

                    if (activeChat.no_create) {
                        this.oldChat = activeChat
                        this.createNewChat(activeChat)
                            .then(createdChat => {
                                this.$store.commit('chat/setSidebarActiveTab', 1)
                                this.setQueryId(createdChat)
                                this.$store.dispatch('chat/refreshChatDetail', createdChat.chat_uid)
                                    .catch(error => errorHandler({ error, show: false }))
                                this.emitMessagePayloads(
                                    payloads.map(payload => ({
                                        ...payload,
                                        chat: createdChat.chat_uid,
                                        chat_uid: createdChat.chat_uid
                                    }))
                                )
                            })
                            .catch(error => {
                                errorHandler({error})
                            })
                    } else {
                        this.emitMessagePayloads(payloads)
                    }

                    this.$nextTick(() => {
                        if(this.$refs['message_input'])
                            this.$refs['message_input'].focus()
                    })
                } else {
                    this.resetComposer()
                    this.$nextTick(() => {
                        this.$refs['message_input'].focus()
                    })
                }
            } catch (error) {
                errorHandler({error})
                this.$nextTick(() => {
                    if(this.$refs['message_input'])
                        this.$refs['message_input'].focus()
                })
            }
        },
        async sendFileExchangeLinkMessage(link) {
            const text = String(link || '').trim()
            if (!text) return

            try {
                let timeout = 0
                if (this.activeChat.no_create) {
                    timeout = 300
                    this.oldChat = JSON.parse(JSON.stringify(this.activeChat))
                    await this.createNewChat(this.activeChat)
                    setTimeout(() => {
                        this.$store.commit('chat/setSidebarActiveTab', 1)
                        this.setQueryId(this.activeChat)
                    }, timeout)
                }

                setTimeout(() => {
                    const author = JSON.parse(JSON.stringify(this.$store.state.user.user))
                    const chatUid = this.activeChat.chat_uid

                    this.createMessage({
                        mentions: [],
                        message_author: {
                            ...author,
                            full_name: author.first_name + ' ' + author.last_name
                        },
                        text,
                        chat: chatUid,
                        chat_uid: chatUid,
                        is_system: false,
                        is_pinned: false,
                        is_deleted: false,
                        message_reply: null,
                        attachments: []
                    })

                    this.clearDraftByChatUid(chatUid)
                    if (this.oldChat?.chat_uid) {
                        this.clearDraftByChatUid(this.oldChat.chat_uid)
                    }
                    ChatEventBus.$emit('arreaScrollDown', true)
                    this.$nextTick(() => {
                        this.$refs['message_input']?.focus()
                    })
                }, timeout)
            } catch (error) {
                errorHandler({error})
            }
        },

        setTyping: debounce(function () {
            if (!this.activeChat?.chat_uid || this.activeChat?.no_create) return

            this.$socket.client.emit('chat_typing', { chat_uid: this.activeChat.chat_uid })
        }, 200),

        waitForCreatedPrivateChat(recipientId, timeout = 15000) {
            return new Promise((resolve, reject) => {
                const startedAt = Date.now()

                const check = () => {
                    const activeChat = this.$store.state.chat.activeChat
                    const chatList = this.$store.state.chat.chatList || []
                    const chat = !activeChat?.no_create && String(activeChat?.recipient?.id || '') === String(recipientId)
                        ? activeChat
                        : chatList.find(item => !item?.no_create && String(item?.recipient?.id || '') === String(recipientId))

                    if (chat?.chat_uid) {
                        resolve(chat)
                        return
                    }

                    if (Date.now() - startedAt >= timeout) {
                        reject(new Error('Chat creation timeout'))
                        return
                    }

                    setTimeout(check, 100)
                }

                check()
            })
        },

        async createNewChat(chat) {
            const recipientId = chat?.recipient?.id
            if (!recipientId) {
                throw new Error('Recipient is required to create chat')
            }

            this.$socket.client.emit("create",
                {
                    is_public: chat.is_public,
                    members: [
                        { user: recipientId }
                    ]
                })

            return this.waitForCreatedPrivateChat(recipientId)
        },

        buildMessagePayloads(message) {
            const baseMessage = {
                ...message,
                client_uid: message?.client_uid || `client-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
                message_author: message?.message_author
                    ? { ...message.message_author }
                    : null,
                attachments: Array.isArray(message?.attachments)
                    ? message.attachments.slice()
                    : []
            }

            let messageText = String(baseMessage.text).trim()
            if(!messageText.length) {
                return [baseMessage]
            }

            const payloads = []
            while (messageText.length > 0) {
                let textPortion = messageText.slice(0, this.maxCharLength)

                const breakIndex = textPortion.lastIndexOf(' ');
                if (breakIndex > 0 && messageText.length > this.maxCharLength) {
                    textPortion = textPortion.slice(0, breakIndex)
                    messageText = messageText.slice(breakIndex + 1)
                } else {
                    messageText = messageText.slice(this.maxCharLength)
                }
                messageText.trim()

                payloads.push({
                    ...baseMessage,
                    client_uid: payloads.length
                        ? `${baseMessage.client_uid}_${payloads.length}`
                        : baseMessage.client_uid,
                    text: textPortion
                })
            }

            return payloads
        },
        pushMessagePayloads(payloads) {
            payloads.forEach(payload => this.pushOptimisticMessage(payload))
        },
        emitMessagePayloads(payloads) {
            payloads.forEach(payload => this.$socket.client.emit("message", payload))
        },
        createMessage(message) {
            const payloads = this.buildMessagePayloads(message)
            this.pushMessagePayloads(payloads)
            this.emitMessagePayloads(payloads)
        },
        setQueryId(data) {
            if(!this.isMobile) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                if (query?.chat_id !== data.chat_uid) {
                    query.chat_id = data.chat_uid
                    if(query.user)
                        delete query.user
                    this.$router.push({ query })
                }
            } else {
                if(this.$route.params?.id !== data.chat_uid) {
                    this.$router.push({
                        name: 'chat-body',
                        params: {
                            id: data.chat_uid
                        }
                    })
                }
            }
        },
        paste(e) {
            let items;

            if (e.clipboardData?.items?.length) {
                items = e.clipboardData.items;
                if (items) {

                    let self = this
                    items = Array.prototype.filter.call(items, (element) => {
                        return element.type.indexOf('image') >= 0
                    })

                    Array.prototype.forEach.call(items, (item) => {

                        let blob = item.getAsFile();

                        let dt = new DataTransfer();
                        dt.items.add(new File([blob], blob.name ? blob.name : this.$t('chat.image_name_default'), { type: item.type }));

                        let file_list = { target: { files: dt.files } };
                        self.handleFileUpload(file_list)

                    });
                }
            }
        },
        dragOver(e) {
            e.stopPropagation();
            e.preventDefault();

            if (this.fileExchangeModal) {
                this.showDragWin = false
                return
            }

            e.dataTransfer.dropEffect = 'copy';
            this.showDragWin = true


        },
        dragLeave(event) {
            event.stopPropagation();
            event.preventDefault();

            if (this.fileExchangeModal) {
                this.showDragWin = false
                return
            }

            if (event.clientX === 0 && event.clientY === 0)
                this.showDragWin = false

        },
        dropComplete(e) {

            e.stopPropagation();
            e.preventDefault();
            this.showDragWin = false

            if (this.fileExchangeModal) {
                return
            }

            const fileList = { target: { files: e.dataTransfer.files } };

            this.handleFileUpload(fileList)
        },

    },
}
