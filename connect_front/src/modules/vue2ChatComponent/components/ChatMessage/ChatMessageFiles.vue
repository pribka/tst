<template>
    <div class="message_files mt-2" :class="message.attachments.length > 1 && 'grid gap-1.5 grid-cols-2'">
        <div 
            class="file_list_item"
            :class="{
                'file_list_item--media': isVideoFile(item) || isAudioFile(item)
            }" 
            v-for="(item, index) in message.attachments" 
            :key="index">
            <div 
                class="res_img_wrapper cursor-pointer" 
                v-if="item.is_image">
                <a 
                    :href="path(item.path)" 
                    class="lht_l ch_lght">
                    <img 
                        class="img_resp lazyload" 
                        :data-src="path(item.path)" 
                        :alt="item.name" />
                </a>
            </div>
            <div v-else-if="isVideoFile(item)" class="media_wrapper media_wrapper--video">
                <video
                    class="media_player media_player--video"
                    controls
                    preload="metadata"
                    :src="path(item.path)"></video>
            </div>
            <div v-else-if="isAudioFile(item)" class="media_wrapper media_wrapper--audio">
                <VoiceMessagePlayer
                    v-if="isVoiceFile(item)"
                    :src="path(item.path)"
                    :chat-uid="getChatUid()"
                    :message-uid="message?.message_uid" />
                <audio
                    v-else
                    v-sync-media="{
                        chatUid: getChatUid(),
                        messageUid: message?.message_uid
                    }"
                    class="media_player media_player--audio"
                    controls
                    preload="metadata"
                    :src="path(item.path)"></audio>
            </div>
            <div class="file_wrapper" v-else>
                <a
                    v-if="isReportSettingsFile(item)"
                    class="doc_file_message report_settings_file_message"
                    :title="fileDisplayName(item)"
                    href="#"
                    @click.prevent="openReportSettingsFile(item)">
                    <span class="report_settings_file_icon">
                        <a-spin v-if="isReportSettingsLoading(item)" size="small" />
                        <i v-else class="fi fi-rr-chart-histogram"></i>
                    </span>
                    <span class="truncate">
                        {{ fileDisplayName(item) }}
                    </span>
                </a>
                <a
                    v-else-if="isPreviewable(item)"
                    class="doc_file_message"
                    :title="fileDisplayName(item)"
                    href="#"
                    @click.prevent="openPreview(item)">
                    <img
                        :src="fileIcon(item)"
                        class="file_icon"
                        :alt="fileDisplayName(item)" />
                    <span class="truncate">
                        {{ fileDisplayName(item) }}
                    </span>
                </a>
                <a 
                    v-else
                    class="doc_file_message" 
                    :title="fileDisplayName(item)"
                    target="_blank" 
                    download 
                    :href="path(item.path)">
                    <img
                        :src="fileIcon(item)"
                        class="file_icon"
                        :alt="fileDisplayName(item)" />
                    <span class="truncate">
                        {{ fileDisplayName(item) }}
                    </span>
                </a>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { filesFormat } from '@/utils'
import { isOnlyofficePreviewable, openOnlyofficePreview } from '@/utils/onlyoffice'
import { isVoiceMessageFile } from '@/utils/voice'
import { bindMediaElement, unbindMediaElement } from '@/utils/voicePlayback'

const AUDIO_EXTENSIONS = new Set(['aac', 'flac', 'm4a', 'mp3', 'oga', 'ogg', 'wav', 'weba'])
const VIDEO_EXTENSIONS = new Set(['avi', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogv', 'webm'])
const REPORT_SETTINGS_EXPORT_KIND = 'ReportSetting'
const REPORT_SETTINGS_FILE_PREFIX = 'ReportSetting-'

export default {
    directives: {
        syncMedia: {
            inserted(el, binding) {
                bindMediaElement(el, binding.value || {})
            },
            unbind(el) {
                unbindMediaElement(el)
            }
        }
    },
    props: {
        message: Object
    },
    components: {
        VoiceMessagePlayer: () => import('@/components/VoiceMessagePlayer')
    },
    data() {
        return {
            reportSettingsLoadingFileId: null
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        })
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
                && this.normalizedFileName(file).startsWith(REPORT_SETTINGS_FILE_PREFIX)
        },
        reportSettingsDisplayName(file) {
            const fullName = this.normalizedFileName(file)
            const withoutExtension = fullName.replace(/\.json$/i, '')
            const reportName = withoutExtension.slice(REPORT_SETTINGS_FILE_PREFIX.length).trim()

            return `${this.$t('chat.report_settings_prefix')}${reportName || this.$t('Untitled')}`
        },
        reportSettingsFileKey(file) {
            return file?.id || file?.path || this.normalizedFileName(file)
        },
        isReportSettingsLoading(file) {
            return this.reportSettingsLoadingFileId === this.reportSettingsFileKey(file)
        },
        fileIcon(file) {
            const extension = this.normalizeExtension(file)
            const foundFormat = filesFormat.find(format => format === extension)

            if (foundFormat) {
                return require(`@/assets/images/files/${extension}.svg`)
            }

            return require(`@/assets/images/files/file.svg`)
        },
        fileDisplayName(file) {
            if (this.isReportSettingsFile(file)) {
                return this.reportSettingsDisplayName(file)
            }

            if (!file?.name) return this.$t('file')

            return this.normalizedFileName(file)
        },
        isAudioFile(file) {
            return !!file?.is_audio || AUDIO_EXTENSIONS.has(this.normalizeExtension(file))
        },
        isVoiceFile(file) {
            return isVoiceMessageFile(file)
        },
        isVideoFile(file) {
            if (this.isAudioFile(file) || this.isVoiceFile(file)) {
                return false
            }
            return !!file?.is_video || VIDEO_EXTENSIONS.has(this.normalizeExtension(file))
        },
        getChatUid() {
            const chatUid = this.message?.chat_uid || this.message?.chat || ''

            if (chatUid && typeof chatUid === 'object') {
                return chatUid.chat_uid || chatUid.uid || chatUid.id || ''
            }

            return chatUid
        },
        isPreviewable(file) {
            return !!file?.id && !!this.getChatUid() && !!this.message?.message_uid && isOnlyofficePreviewable(file)
        },
        openPreview(file) {
            openOnlyofficePreview(this.$store, {
                scope: 'chat_attachment',
                chat_uid: this.getChatUid(),
                message_uid: this.message?.message_uid,
                file_id: file?.id
            })
        },
        normalizeImportedReportSettings(parsedSettings) {
            const template = parsedSettings?.kind === REPORT_SETTINGS_EXPORT_KIND
                ? parsedSettings.template
                : parsedSettings

            if (!template?.metadata?.modelName) {
                throw new Error('invalid_report_settings_file')
            }

            return {
                ...template,
                id: null,
                editable: false,
                imported: true,
                is_base: false,
                name: template.name || parsedSettings?.reportName || this.$t('Untitled'),
                description: template.description || '',
                appSectionCode: template.appSectionCode || '',
                base_report: template.base_report || null,
                template: template.template || null,
                complexFilterMode: template.complexFilterMode ?? template.complexFilter ?? template.metadata?.complexFilter ?? false,
                metadata: template.metadata
            }
        },
        async openReportSettingsFile(file) {
            if (this.reportSettingsLoadingFileId) {
                return
            }

            this.reportSettingsLoadingFileId = this.reportSettingsFileKey(file)
            try {
                const { data } = await this.$http.get(this.getAuthenticatedFileUrl(file), {
                    responseType: 'text'
                })
                const parsedSettings = typeof data === 'string' ? JSON.parse(data) : data
                const templateData = this.normalizeImportedReportSettings(parsedSettings)

                await this.$store.dispatch('reports/openReportModal', templateData)
            } catch (error) {
                console.error(error)
                this.$message.error(this.$t('Failed to open report settings'))
            } finally {
                this.reportSettingsLoadingFileId = null
            }
        },
        getAuthenticatedFileUrl(file) {
            const rawPath = this.path(file?.path || '')
            const fileUrl = new URL(rawPath, window.location.origin)

            return `${window.location.origin}${fileUrl.pathname}${fileUrl.search}`
        },
        path(path) {
            if(path.includes('chat_attachments'))
                return path
            else
                return path + encodeURIComponent(`&chat_uid=${this.getChatUid()}&message_uid=${this.message.message_uid}&target=chat_attachments`)
        }
    }
}
</script>

<style lang="scss" scoped>
.ch_lght{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
}
.message_files{
    .res_img_wrapper{
        img{
            opacity: 0;
            transition: opacity 0.05s ease-in-out;
            &.lazyloaded{
                opacity: 1;
            }
        }
    }

    .file_wrapper{
        height: 100%;
    }

    .doc_file_message{
        min-height: 62px;
        height: 100%;
        display: flex;
        align-items: center;
        gap: 10px;
        color: inherit;
        transition: opacity 0.15s ease-in-out;

        &:hover{
            opacity: 0.72;
        }
    }

    .file_icon{
        width: 32px;
        min-width: 32px;
        height: 32px;
        display: block;
        object-fit: contain;
    }

    .report_settings_file_message {
        .report_settings_file_icon {
            width: 34px;
            min-width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.18);
            color: inherit;
        }

        .fi {
            line-height: 1;
            font-size: 18px;
        }
    }
}

.media_wrapper{
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    background: #0f172a;
}

.file_list_item--media{
    grid-column: 1 / -1;
}

.media_wrapper--audio{
    background: rgba(15, 23, 42, 0.04);
    padding: 10px;
    min-width: 340px;
    max-width: min(100%, 420px);

    @media (max-width: 900px) {
        min-width: 0;
        max-width: 100%;
    }
}

.media_player{
    width: 100%;
    display: block;
    outline: none;
}

.media_player--video{
    min-height: 220px;
    max-height: 360px;
    background: #000;
}

.media_player--audio{
    height: 40px;
    min-width: 320px;

    @media (max-width: 900px) {
        min-width: 240px;
    }
}
</style>
