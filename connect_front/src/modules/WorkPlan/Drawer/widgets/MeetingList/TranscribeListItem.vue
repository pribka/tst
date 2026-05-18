<template>
    <div class="transcribe_item">
        <div v-if="detail.created_at" class="flex justify-center">
            <div class="transcribe__date">
                {{ $moment(detail.created_at).format('DD.MM.YYYY HH:mm') }}
            </div>
        </div>
        <div class="mb-2 flex items-center gap-2">
            <template v-if="videoButton">
                <a v-if="detail.url" :href="detail.url" target="_blank" class="ant-btn ant-btn-flat_primary flex items-center" :class="isMobile && 'justify-center ant-btn-icon-only'">
                    <i class="fi-rr-clapperboard-play" :class="!isMobile && 'mr-2'" />
                    <template v-if="!isMobile">{{ $t('workplan.video_recording') }}</template>
                </a>
                <a-button 
                    type="flat_primary" 
                    flaticon 
                    v-tippy
                    :loading="videoLoading"
                    :content="$t('workplan.download_video')"
                    icon="fi-rr-download" 
                    @click="getMeetingVideo()" />
            </template>
            <template v-if="detail.transcribe">
                <a-button 
                    type="flat_primary" 
                    flaticon 
                    v-tippy
                    :content="$t('workplan.copy_text')"
                    icon="fi-rr-copy-alt" 
                    @click="textCopy()" />
                <a-button 
                    type="flat_primary" 
                    flaticon 
                    v-tippy
                    :content="$t('workplan.print_text')"
                    icon="fi-rr-print" 
                    @click="textPrint()" />
            </template>
        </div>
        <div v-html="formattedTranscribe" />
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
const key = 'downloadKey'
export default {
    props: {
        detail: {
            type: Object,
            required: true
        },
        meeting: {
            type: Object,
            default: () => null
        },
        videoButton: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        formattedTranscribe() {
            if (!this.detail.transcribe) return ''
            return this.detail.transcribe
                .replace(/\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}\s*\n/g, '')
                .replace(/\[([A-Z_0-9]+)\]/g, '<strong>$1</strong>')
                .replace(/\n{2,}/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/(<br>\s*){2,}/g, '<br>')
                .trim()
                .replace(/^/, '<p>')
                .replace(/$/, '</p>')
        }
    },
    data() {
        return {
            videoLoading: false,
            localRecordFile: null
        }
    },
    methods: {
        getExtFromUrl(url) {
            try {
                const pathname = new URL(url, window.location.origin).pathname
                const last = pathname.split('/').pop() || ''
                const parts = last.split('.')
                if (parts.length > 1) return parts.pop()
                return ''
            } catch (e) {
                const last = (url || '').split('?')[0].split('#')[0].split('/').pop() || ''
                const parts = last.split('.')
                if (parts.length > 1) return parts.pop()
                return ''
            }
        },
        downloadByLink(url, filename) {
            const u = new URL(url, window.location.origin)
            u.searchParams.set('download', '1')

            const a = document.createElement('a')
            a.href = u.toString()
            a.setAttribute('download', filename || '')
            a.target = '_blank'
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
        },
        getExtFromContentType(contentType) {
            const map = {
                'video/webm': 'webm',
                'video/mp4': 'mp4',
                'audio/mpeg': 'mp3',
                'audio/mp4': 'm4a',
                'application/pdf': 'pdf'
            }
            return map[contentType] || ''
        },

        buildFilename(file) {
            const base = file?.name || 'file'
            const ext = file?.extension
        || this.getExtFromUrl(file?.path)
        || this.getExtFromUrl(file?.url)
        || this.getExtFromContentType(file?.content_type)

            return ext ? `${base}.${ext}` : base
        },
        async getMeetingVideo() {
            const file = this.localRecordFile || this.detail.record_file

            if (file?.path) {
                this.downloadByLink(file.path, this.buildFilename(file))
                return
            }

            try {
                this.$message.loading({ content: this.$t('workplan.generating_video_file'), key })
                this.videoLoading = true
                const { data } = await this.$http.post(`/meetings/records/${this.detail.id}/merge_video_audio/`)
                if (data?.record_file?.path) {
                    this.localRecordFile = data.record_file
                    this.downloadByLink(data.record_file.path, this.buildFilename(data.record_file))
                }
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.$message.destroy()
                this.videoLoading = false
            }
        },
        textPrint() {
            const printWindow = window.open('', '_blank')
            if (!printWindow) return

            const title = this.meeting?.meeting?.name || this.$t('workplan.print')
            const heading = this.meeting?.meeting?.name
                ? `<h3>${this.meeting.meeting.name}</h3>`
                : ''

            printWindow.document.write(`
                <html>
                    <head>
                        <title>${title}</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                padding: 20px;
                                line-height: 1.6;
                            }
                            h1 {
                                margin-bottom: 20px;
                            }
                            p {
                                margin: 0 0 10px;
                            }
                            strong {
                                font-weight: 600;
                            }
                        </style>
                    </head>
                    <body>
                        ${heading}
                        ${this.formattedTranscribe}
                    </body>
                </html>
            `)

            printWindow.document.close()
            printWindow.focus()
            printWindow.print()
            printWindow.close()
        },
        textCopy() {
            navigator.clipboard.writeText(this.detail.transcribe)
                .then(() => {
                    this.$message.success(this.$t('workplan.text_copied'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('workplan.copy_link_failed'))
                })
        },
    }
}
</script>

<style lang="scss" scoped>
.transcribe_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
    .transcribe__date{
        background: #f7f9fc;
        padding: 0px 8px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
}
</style>
