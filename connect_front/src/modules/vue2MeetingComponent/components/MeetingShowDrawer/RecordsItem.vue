<template>
    <div class="record_item">
        <iframe 
            v-if="record.url"
            width="100%"
            height="400px" 
            frameborder="0"
            scrolling="auto"
            :src="record.url" />
        <a-empty v-else :description="$t('meeting.no_video')" />
        <div v-if="record.url" class="flex items-center mt-3 gap-2 flex-wrap">
            <a-button 
                type="primary" 
                flaticon 
                :loading="videoLoading"
                icon="fi-rr-download" 
                @click="getMeetingVideo(record)">
                {{ $t('meeting.download') }}
            </a-button>
            <a :href="record.url" target="_blank" class="ant-btn ant-btn-flat_primary flex items-center" :class="isMobile && 'justify-center ant-btn-icon-only'">
                <i class="fi-rr-arrow-up-right-from-square" :class="!isMobile && 'mr-2'" />
                <template v-if="!isMobile">
                    {{ $t('meeting.open_new_window') }}
                </template>
            </a>
            <a-button 
                type="flat_primary" 
                flaticon 
                v-tippy
                :content="$t('copy_link')"
                icon="fi-rr-link-alt" 
                @click="copyLink(record)" />
        </div>
        <a-tabs v-if="detail.summary || record.transcribe" v-model="tab" class="records_tabs mt-3">
            <a-tab-pane v-if="detail.summary" key="summary" :tab="$t('meeting.sammary')">
                <div class="summary_card rounded-lg">
                    <div class="summary_card__header select-none flex items-center justify-between truncate">
                        <h4 class="summary_card__label truncate font-semibold mb-0">
                            <i class="fi fi-rr-pen-field mr-2" />
                            {{ $t('meeting.summary_label') }}
                        </h4>
                    </div>
                    <div v-html="summaryHtml(detail.summary)" @click.stop class="mt-3 mb-2 summary_text" />
                </div>
            </a-tab-pane>
            <a-tab-pane v-if="record.transcribe" key="transcribe" :tab="$t('meeting.transcribe')">
                <TranscribeListItem 
                    :meeting="meeting" 
                    :videoButton="false"
                    :detail="record" />
            </a-tab-pane>
        </a-tabs>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
const key = 'downloadKey'
export default {
    components: {
        TranscribeListItem: () => import('@apps/WorkPlan/Drawer/widgets/MeetingList/TranscribeListItem.vue'),
    },
    props: {
        record: {
            type: Object,
            required: true
        },
        detail: {
            type: Object,
            required: true
        },
        meeting: {
            type: Object,
            required: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    created() {
        if(!this.detail.summary)
            this.tab = 'transcribe'
    },
    data() {
        return {
            tab: 'summary',
            localRecordFile: null,
            videoLoading: false
        }
    },
    methods: {
        copyLink(item) {
            navigator.clipboard.writeText(item.url)
                .then(() => {
                    this.$message.success(this.$t('link_succes_copy'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('copy_link_error'))
                })
        },
        summaryHtml(summary) {
            if (!summary) return ''

            return summary
                .replace(/(^|\n)\s*(\d+\.)\s*\.?\s*_+/g, '$1$2 ')
                .replace(/_+(\s*\n|$)/g, '$1')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .trim()
                .replace(/^/, '<p>')
                .replace(/$/, '</p>')
        },
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
        async getMeetingVideo(record) {
            const file = this.localRecordFile || record.record_file

            if (file?.path) {
                this.downloadByLink(file.path, this.buildFilename(file))
                return
            }

            try {
                this.$message.loading({ content: this.$t('meeting.file_generate'), key })
                this.videoLoading = true
                const { data } = await this.$http.post(`/meetings/records/${record.id}/merge_video_audio/`)
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
    },
    beforeDestroy() {
        this.tab = 'summary'
    }
}
</script>

<style lang="scss" scoped>
.records_tabs{
    &.ant-tabs.ant-tabs-top{
        &::v-deep{
            .ant-tabs-bar.ant-tabs-top-bar{
                display: block;
            }
        }
    }
}
.record_item{
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
}
.summary_text{
    &::v-deep{
        p{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.summary_card{
    background: linear-gradient(135deg,  rgba(249,239,255,1) 46%,rgba(240,216,255,1) 100%); /* W3C, IE10+, FF16+, Chrome26+, Opera12+, Safari7+ */
    padding: 10px 15px;
    border: 1px solid #f1dcff;
    &:not(:last-child){
        margin-bottom: 15px;
    }
    @media (min-width: 768px) {
        padding: 10px 20px;
    }
    .summary_card__label{
        display: flex;
        align-items: center;
        font-size: 16px;
        img{
            max-width: 22px;
        }
        @media (min-width: 768px) {
            font-size: 18px;
        }
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.active{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
}
</style>