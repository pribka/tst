<template>
    <div v-if="message || hasDraft" class="message_desc truncate">
        <div v-if="hasDraft" class="truncate flex items-center min-w-0">
            <span class="draft_prefix mr-1">{{ $t('chat.draft_prefix') }}</span>
            <div v-if="draftImages.length" class="message_images">
                <div v-for="image in draftImages" :key="image.id || image.iid || image.path" class="message_images__image">
                    <img :data-src="image.path || (image.file && image.file.path)" class="lazyload" />
                </div>
            </div>
            <span v-if="!draftFiles && draftImages.length && !draftText.length" class="truncate">
                {{ draftImagesCount }}
            </span>
            <span v-if="draftFiles" class="truncate">
                {{ draftFiles }}<span v-if="draftText.length" class="mr-1">,</span>
            </span>
            <span v-if="draftText.length" class="truncate min-w-0 flex-1" v-html="draftText" @click="onHtmlClick" />
        </div>
        <div v-else-if="chat.last_message.message_author" class="truncate flex items-center min-w-0">
            <div v-if="showMessageAuthor" class="mr-1">
                {{ messageAuthor }}:
            </div>
            <span v-if="message.message_reply || message.forwarded" class="message_reply_icon mr-1 blue_color">
                <i class="fi fi-rr-undo" />
            </span>
            <div v-if="messageImages.length" class="message_images">
                <div v-for="image in messageImages" :key="image.id" class="message_images__image">
                    <img :data-src="image.path" class="lazyload" :key="image.id" />
                </div>
            </div>
            <span v-if="!messageFiles && messageImages.length && !lastMessageReplace.length" class="truncate">
                {{ messageImagesCount }}
            </span>
            <span v-if="messageFiles" class="truncate flex items-center min-w-0">
                <i
                    v-if="hasReportSettingsPreview"
                    class="fi fi-rr-chart-histogram mr-1 message_report_settings_icon"></i>
                {{ messageFiles }}<span v-if="lastMessageReplace.length" class="mr-1">,</span>
            </span>
            <span class="truncate min-w-0 flex-1" v-html="lastMessageReplace" @click="onHtmlClick" />
        </div>
        <div v-else class="truncate flex items-center min-w-0">
            <span v-if="message.message_reply || message.forwarded" class="message_reply_icon mr-1 blue_color">
                <i class="fi fi-rr-undo" />
            </span>
            <div v-if="messageImages.length" class="message_images">
                <div v-for="image in messageImages" :key="image.id" class="message_images__image">
                    <img :data-src="image.path" class="lazyload" :key="image.id" />
                </div>
            </div>
            <span v-if="!messageFiles && messageImages.length && !lastMessageReplace.length" class="truncate">
                {{ messageImagesCount }}
            </span>
            <span v-if="messageFiles" class="truncate">
                {{ messageFiles }}<span v-if="lastMessageReplace.length" class="mr-1">,</span>
            </span>
            <span v-if="message.is_ai_message" class="truncate ms_img mr-1 inline-block" style="min-width: 14px;">
                <img src="@/assets/svg/ai_icons.svg" style="max-width: 14px;" />
            </span>
            <span v-html="lastMessageReplace" class="truncate" @click="onHtmlClick" />
        </div>
    </div>
</template>

<script>
import { declOfNum, clearMessageHtmlTruncate } from '../utils'
import { getChatSharePreviewText } from '@/utils/chatPreview'
export default {
    props: {
        chat: {
            type: Object,
            required: true
        },
        draft: {
            type: Object,
            default: null
        },
        selectChat: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
        message() {
            return this.chat.last_message
        },
        hasDraft() {
            return !!this.draft
        },
        previewMessage() {
            return this.message?.forwarded && this.message?.message_forwarded
                ? this.message.message_forwarded
                : this.message
        },
        previewAttachments() {
            if (this.previewMessage?.is_deleted) {
                return []
            }

            const nestedAttachments = Array.isArray(this.message?.message_forwarded?.attachments)
                ? this.message.message_forwarded.attachments
                : []
            const ownAttachments = Array.isArray(this.message?.attachments)
                ? this.message.attachments
                : []

            if (nestedAttachments.length) {
                return nestedAttachments
            }

            return ownAttachments
        },
        draftAttachments() {
            return Array.isArray(this.draft?.files) ? this.draft.files : []
        },
        draftText() {
            return clearMessageHtmlTruncate(this.draft?.modalText || this.draft?.text || '')
        },
        isOwnMessage() {
            return !!this.user && this.user.id === this.message?.message_author?.id
        },
        showMessageAuthor() {
            return !!this.message?.message_author && (this.chat.is_public || this.isOwnMessage)
        },
        messageAuthor() {
            if(this.user) {
                if(this.isOwnMessage) {
                    return this.$t('chat.you')
                } else {
                    const n = this.message.message_author.full_name.split(' ')
                    return `${n[0]}${n[1] ? ' ' + n[1].charAt(0).toUpperCase() + '.' : ''}`
                }
            }
            return ''
        },
        messageImages() {
            if(this.previewAttachments.length) {
                const files = this.previewAttachments.filter(f => f.is_image)
                if(files.length > 4) {
                    return files.splice(0, 4)
                }

                return files
            }

            return []
        },
        draftImages() {
            if (this.draftAttachments.length) {
                const files = this.draftAttachments
                    .filter(f => f?.file?.is_image || f?.image)
                    .map(f => f.file || f)

                if (files.length > 4) {
                    return files.slice(0, 4)
                }

                return files
            }

            return []
        },
        messageImagesCount() {
            if(this.previewAttachments.length) {
                const file = this.previewAttachments.filter(f => f.is_image)
                if(file.length) {
                    if (file.length === 1 && this.isGifImage(file[0])) {
                        return '1 GIF'
                    }

                    return file.length + ' '
                        + declOfNum(file.length,
                            [this.$t('chat.photo'), this.$t('chat.photos'), this.$t('chat.photosGen')])
                }
                
                return null
            }
            return []
        },
        draftImagesCount() {
            if(this.draftAttachments.length) {
                const files = this.draftAttachments.filter(f => f?.file?.is_image || f?.image)
                if(files.length) {
                    const normalizedFiles = files.map(f => f.file || f)

                    if (normalizedFiles.length === 1 && this.isGifImage(normalizedFiles[0])) {
                        return '1 GIF'
                    }

                    return files.length + ' '
                        + declOfNum(files.length,
                            [this.$t('chat.photo'), this.$t('chat.photos'), this.$t('chat.photosGen')])
                }
            }

            return null
        },
        messageFiles() {
            if(this.previewAttachments.length) {
                const file = this.previewAttachments.filter(f => !f.is_image)
                if(file.length) {
                    if (file.length === 1 && this.isReportSettingsFile(file[0])) {
                        return this.reportSettingsDisplayName(file[0])
                    }

                    if (file.every(item => this.isVoiceMessageFile(item))) {
                        return this.$t('chat.voice_message')
                    }

                    return file.length + ' '
                        + declOfNum(file.length,
                            [this.$t('chat.fileC'), this.$t('chat.fileGenC'), this.$t('chat.filesC')])
                }
            }
            return null
        },
        hasReportSettingsPreview() {
            const files = this.previewAttachments.filter(f => !f.is_image)
            return files.length === 1 && this.isReportSettingsFile(files[0])
        },
        draftFiles() {
            if(this.draftAttachments.length) {
                const file = this.draftAttachments
                    .map(item => item.file || item)
                    .filter(f => !f?.is_image)

                if(file.length) {
                    if (file.every(item => this.isVoiceMessageFile(item))) {
                        return this.$t('chat.voice_message')
                    }

                    return file.length + ' '
                        + declOfNum(file.length,
                            [this.$t('chat.fileC'), this.$t('chat.fileGenC'), this.$t('chat.filesC')])
                }
            }

            return null
        },
        lastMessageReplace() {
            let mess = this.previewMessage
            let res = mess?.is_deleted
                ? this.$t('chat.deleted_message_text')
                : clearMessageHtmlTruncate(this.previewMessage?.text)

            // Share
            if(res.trim().length === 0 && mess.share){
                res = `"${getChatSharePreviewText(mess.share, this.$t.bind(this), this.toPlainAndTrim)}"`
            }
            return res
        }
    },
    methods: {
        normalizeExtension(file) {
            return String(file?.extension || file?.ext || '')
                .toLowerCase()
                .replace(/^\./, '')
        },
        normalizedFileName(file) {
            const extension = this.normalizeExtension(file)
            const rawName = String(file?.name || '')

            if (!extension || rawName.toLowerCase().endsWith(`.${extension}`)) {
                return rawName
            }

            return `${rawName}.${extension}`
        },
        isReportSettingsFile(file) {
            return this.normalizeExtension(file) === 'json'
                && this.normalizedFileName(file).startsWith('ReportSetting-')
        },
        reportSettingsDisplayName(file) {
            const fullName = this.normalizedFileName(file)
            const withoutExtension = fullName.replace(/\.json$/i, '')
            const reportName = withoutExtension.slice('ReportSetting-'.length).trim()

            return `${this.$t('chat.report_settings_prefix')}${reportName || this.$t('Untitled')}`
        },
        isVoiceMessageFile(file = {}) {
            if (!file || typeof file !== 'object') {
                return false
            }

            if (file.is_voice === true || file.voice === true) {
                return true
            }

            const rawName = [
                file.name,
                file.original_name,
                file.file_name,
                file.title
            ].find(Boolean)

            const normalizedName = String(rawName || '')
                .trim()
                .toLowerCase()

            if (normalizedName.startsWith('voice-message-')) {
                return true
            }

            const meta = file.meta && typeof file.meta === 'object' ? file.meta : {}
            return meta.is_voice === true || meta.voice === true
        },
        isGifImage(file = {}) {
            if (!file || typeof file !== 'object') {
                return false
            }

            const contentType = String(file.content_type || file.mime_type || file.type || '')
                .trim()
                .toLowerCase()
            if (contentType === 'image/gif') {
                return true
            }

            const extension = String(file.extension || file.ext || '')
                .trim()
                .toLowerCase()
                .replace(/^\./, '')
            if (extension === 'gif') {
                return true
            }

            const name = String(file.name || file.original_name || file.file_name || '')
                .trim()
                .toLowerCase()

            return name.endsWith('.gif')
        },
        toPlainAndTrim(text, limit = 100) {
            const div = document.createElement('div')
            div.innerHTML = text || ''
            const plain = (div.textContent || div.innerText || '')
                .replace(/\s+/g, ' ')
                .trim()

            if (plain.length <= limit) return plain
            return plain.slice(0, limit).trim() + '…'
        },
        onHtmlClick(e) {
            const link = e.target.closest('a')
            if (!link) return
            e.preventDefault()
            e.stopPropagation()
            this.selectChat()
        }
    }
}
</script>

<style lang="scss" scoped>
.message_reply_icon{
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    min-width: 14px;
}
</style>

<style lang="scss" scoped>
.message_desc{
    &::v-deep{
        .user_chat_mention{
            color: var(--blue);
        }
    }

    .draft_prefix{
        color: #f5222d;
        flex-shrink: 0;
    }

    .message_report_settings_icon {
        flex-shrink: 0;
        line-height: 1;
    }
}
.message_images{
    display: flex;
    align-items: center;
    margin-right: 5px;
    &__image{
        width: 20px;
        height: 20px;
        overflow: hidden;
        border-radius: 5px;
        background: rgba(115, 115, 115, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--border2);
        &:not(:last-child){
            margin-right: 3px;
        }
        img{
            object-fit: cover;
            vertical-align: middle;
            -o-object-fit: cover;
            max-width: 100%;
            opacity: 0;
            transition: opacity 0.05s ease-in-out;
            &.lazyloaded{
                opacity: 1;
            }
        }
    }
}
</style>
