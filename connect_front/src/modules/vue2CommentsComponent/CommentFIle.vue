<template>
    <div 
        class="comment_file"
        :class="{
            'comment_file--media': isMedia,
            'comment_file--audio': isAudio,
            'comment_file--report-settings': isReportSettingsFile
        }" 
        :title="fileDisplayName">
        <a 
            v-if="isImage"
            class="lht_l"
            :href="file.path">
            <img
                class="lazyload"
                :data-src="file.path" 
                :alt="file.name" />
        </a>
        <video
            v-else-if="isVideo"
            class="comment_media comment_media--video"
            controls
            preload="metadata"
            :src="file.path"></video>
        <VoiceMessagePlayer
            v-else-if="isVoiceAudio"
            class="comment_media comment_media--audio"
            :src="file.path"
            :chat-uid="commentPlaybackScope"
            :message-uid="resolvedCommentId" />
        <audio
            v-else-if="isAudio"
            v-sync-media="{
                chatUid: commentPlaybackScope,
                messageUid: resolvedCommentId
            }"
            class="comment_media comment_media--audio-native"
            controls
            preload="metadata"
            :src="file.path"></audio>
        <template v-else>
            <a
                v-if="isReportSettingsFile"
                class="truncate doc_file report_settings_file"
                :title="fileDisplayName"
                href="#"
                @click.prevent="openReportSettingsFile">
                <span class="report_settings_file_icon">
                    <a-spin v-if="reportSettingsLoading" size="small" />
                    <i v-else class="fi fi-rr-chart-histogram"></i>
                </span>
                <span class="truncate">
                    {{ fileDisplayName }}
                </span>
            </a>
            <a
                v-else-if="useOnlyofficePreview"
                class="truncate doc_file"
                :title="fileDisplayName"
                href="#"
                @click.prevent="openPreview">
                <img 
                    :src="fileIcon"
                    class="file_icon" />
                <span class="truncate">
                    {{ fileDisplayName }}
                </span>
            </a>
            <a
                v-else
                download
                class="truncate doc_file"
                target="_blank"
                :title="fileDisplayName"
                :href="file.path">
                <img 
                    :src="fileIcon"
                    class="file_icon" />
                <span class="truncate">
                    {{ fileDisplayName }}
                </span>
            </a>
        </template>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'
import { isOnlyofficePreviewable, openOnlyofficePreview } from '@/utils/onlyoffice'
import { isVoiceMessageFile } from '@/utils/voice'
import { bindMediaElement, unbindMediaElement } from '@/utils/voicePlayback'

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
    components: {
        VoiceMessagePlayer: () => import('@/components/VoiceMessagePlayer')
    },
    props: {
        file: {
            type: Object,
            required: true
        },
        commentId: {
            type: [String, Number],
            default: null
        },
        id: {
            type: [String, Number],
            default: null
        }
    },
    data() {
        return {
            modalImage: null,
            reportSettingsLoading: false
        }
    },
    computed: {
        normalizedExtension() {
            return String(this.file?.extension || this.file?.ext || '')
                .toLowerCase()
                .replace(/^\./, '')
        },
        normalizedFileName() {
            const rawName = String(this.file?.name || '')

            if (!this.normalizedExtension || rawName.toLowerCase().endsWith(`.${this.normalizedExtension}`)) {
                return rawName
            }

            return `${rawName}.${this.normalizedExtension}`
        },
        isReportSettingsFile() {
            return this.normalizedExtension === 'json'
                && this.normalizedFileName.startsWith(REPORT_SETTINGS_FILE_PREFIX)
        },
        reportSettingsDisplayName() {
            const withoutExtension = this.normalizedFileName.replace(/\.json$/i, '')
            const reportName = withoutExtension.slice(REPORT_SETTINGS_FILE_PREFIX.length).trim()

            return `${this.$t('comment.report_settings_prefix')}${reportName || this.$t('Untitled')}`
        },
        fileIcon() {
            const find = filesFormat.find(f => f === this.normalizedExtension)
            if(find)
                return require(`@/assets/images/files/${this.normalizedExtension}.svg`)
            else
                return require(`@/assets/images/files/file.svg`)
        },
        fileName() {
            if(this.file?.name) {
                return this.normalizedFileName
            }

            return this.$t('file')
        },
        fileDisplayName() {
            if (this.isReportSettingsFile) {
                return this.reportSettingsDisplayName
            }

            return this.fileName
        },
        resolvedCommentId() {
            return this.commentId || this.id || null
        },
        commentPlaybackScope() {
            return `comment_${this.resolvedCommentId || this.file?.id || 'attachment'}`
        },
        office() {
            switch (this.normalizedExtension) {
            case "doc":
                return 'docx'
                break;
            case "docx":
                return 'docx'
                break;
            case "xlsx":
                return 'xlsx'
                break;
            case "xls":
                return 'xlsx'
                break;
            case "pptx":
                return 'pptx'
                break;
            case "ppt":
                return 'pptx'
                break;
            default:
                return ''
            }
        },
        isDoc() {
            const set = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
            return set.includes(this.normalizedExtension)
        },
        isImage() {
            return this.file.is_image
        },
        isVideo() {
            return !!this.file.is_video
        },
        isAudio() {
            return !!this.file.is_audio
        },
        isVoiceAudio() {
            return this.isAudio && isVoiceMessageFile(this.file)
        },
        isMedia() {
            return this.isVideo || this.isAudio
        },
        useOnlyofficePreview() {
            return !!this.resolvedCommentId && isOnlyofficePreviewable(this.file)
        },
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    methods: {
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
        getAuthenticatedFileUrl() {
            const rawPath = this.file?.path || ''
            const fileUrl = new URL(rawPath, window.location.origin)

            return `${window.location.origin}${fileUrl.pathname}${fileUrl.search}`
        },
        async openReportSettingsFile() {
            if (this.reportSettingsLoading) {
                return
            }

            this.reportSettingsLoading = true
            try {
                const { data } = await this.$http.get(this.getAuthenticatedFileUrl(), {
                    responseType: 'text'
                })
                const parsedSettings = typeof data === 'string' ? JSON.parse(data) : data
                const templateData = this.normalizeImportedReportSettings(parsedSettings)

                await this.$store.dispatch('reports/openReportModal', templateData)
            } catch (error) {
                console.error(error)
                this.$message.error(this.$t('Failed to open report settings'))
            } finally {
                this.reportSettingsLoading = false
            }
        },
        openPreview() {
            if (!this.useOnlyofficePreview) return
            openOnlyofficePreview(this.$store, {
                scope: 'comment_attachment',
                comment_id: this.resolvedCommentId,
                file_id: this.file.id
            })
        },
        handleCancel() {
            this.modalImage = null
        }
    }
}
</script>

<style lang="scss" scoped>
.cm_modal_image{
    display: flex;
    align-items: center;
    justify-content: center;
    img{
        max-width: 100%;
    }
}
.doc_modal{
    &::v-deep{
        .ant-modal-body{
            padding: 0px;
            height: calc(100% - 36px);
        }
        .ant-modal{
            padding: 0px;
            height: 100vh;
        }
        .ant-modal-content{
            height: 100%;
            border-radius: 0px;
        }
        .ant-modal-wrap{
            overflow: hidden;
        }
        .ant-modal-header{
            padding: 7px 18px;
            border-radius: 0px;
            border-bottom: 0px;
            .ant-modal-title{
                font-size: 14px;
            }
        }
        .ant-modal-close-x{
            height: 36px;
            width: 36px;
            line-height: 30px;
        }
    }
}
.comment_file{
    width: 80px;
    height: 80px;
    border-radius: var(--borderRadius);
    overflow: hidden;
    border: 1px solid var(--border2);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
    text-align: center;
    -webkit-touch-callout: none; /* iOS Safari */
    -webkit-user-select: none;   /* Chrome/Safari/Opera */
    -khtml-user-select: none;    /* Konqueror */
    -moz-user-select: none;      /* Firefox */
    -ms-user-select: none;       /* Internet Explorer/Edge */
    user-select: none;
    transition : border 200ms ease-out;
    background: #fafafa;
    .doc_file{
        padding: 0 5px;
    }
    .file_icon{
        max-width: 40px;
        margin: 0 auto;
    }
    .report_settings_file{
        width: 100%;
        height: 100%;
        display: flex !important;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        text-align: left;
    }
    .report_settings_file_icon{
        width: 34px;
        height: 34px;
        min-width: 34px;
        border-radius: 50%;
        background: rgba(71, 112, 245, 0.12);
        color: var(--blue);
        display: flex;
        align-items: center;
        justify-content: center;

        i{
            font-size: 18px;
            line-height: 1;
        }
    }
    a{
        &.lht_l{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            img{
                transition: opacity 0.15s ease-in-out;
                &:not(.lazyloaded){
                    opacity: 0;
                }
            }
        }
        &:not(.lht_l){
            display: block;
        }
        color: #505050;
    }
    &:hover{
        border-color: var(--blue);
    }
    span{
        font-size: 12px;
        font-weight: 300;
        display: block;
    }
    img{
        width: 100%;
        object-fit: cover;
        vertical-align: middle;
        -o-object-fit: cover;
    }
    &:not(:last-child){
        margin-right: 5px;
    }
}

.comment_file--report-settings{
    width: 280px;
    max-width: 100%;
    height: 60px;
}

.comment_file--media{
    flex: 1 1 100%;
    width: 100%;
    max-width: 560px;
    height: auto;
    padding: 6px;
    background: #fff;
    align-items: stretch;
    justify-content: flex-start;
    cursor: default;
    user-select: auto;
    -webkit-touch-callout: default;
    -webkit-user-select: auto;
    -khtml-user-select: auto;
    -moz-user-select: auto;
    -ms-user-select: auto;
}

.comment_file--audio{
    flex-basis: 100%;
    width: 100%;
    max-width: 560px;
    padding: 10px;
    overflow: visible;
}

.comment_media{
    width: 100%;
    display: block;
    border-radius: 10px;
    background: #0f172a;
    outline: none;
}

.comment_media--video{
    min-height: 220px;
    max-height: 320px;
    object-fit: contain;
}

.comment_media--audio{
    width: 100%;
    min-width: 320px;
    height: auto;
    background: transparent;
}

.comment_media--audio-native{
    width: 100%;
    min-width: 320px;
    height: 54px;
    background: transparent;
}
</style>
