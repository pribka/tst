<template>
    <div class="office_preview_viewer" :class="modalMode && 'office_preview_viewer--modal'">
        <header class="office_preview_viewer__header">
            <div class="office_preview_viewer__title_wrap">
                <div class="office_preview_viewer__title">{{ fileName || $t('file') }}</div>
            </div>
            <div class="office_preview_viewer__actions">
                <a-button
                    v-tippy
                    :content="$t('onlyoffice.reload')"
                    type="ui"
                    shape="circle"
                    :size="isMobile ? 'small' : 'default'"
                    flaticon
                    icon="fi-rr-rotate-right"
                    class="office_preview_viewer__action_btn"
                    @click="reloadViewer(true)" />
                <a-button
                    v-if="downloadUrl"
                    v-tippy
                    :content="$t('onlyoffice.download')"
                    type="ui"
                    :size="isMobile ? 'small' : 'default'"
                    flaticon
                    icon="fi-rr-download"
                    shape="circle"
                    class="office_preview_viewer__action_btn"
                    @click="openDownload" />
                <!--<a-button
                    v-if="showClose"
                    v-tippy
                    :content="$t('open_new_window')"
                    type="ui"
                    :size="isMobile ? 'small' : 'default'"
                    flaticon
                    icon="fi-rr-share-square"
                    shape="circle"
                    class="office_preview_viewer__action_btn"
                    @click="openInNewTab" />-->
                <a-button
                    v-if="showClose"
                    v-tippy
                    :content="$t('onlyoffice.close')"
                    type="ui"
                    :size="isMobile ? 'small' : 'default'"
                    flaticon
                    icon="fi-rr-cross"
                    shape="circle"
                    class="office_preview_viewer__action_btn"
                    @click="$emit('close')" />
            </div>
        </header>

        <div v-if="loading" class="office_preview_viewer__state">
            <div class="office_preview_viewer__loading">
                <video
                    v-if="scanAnimationWebmSrc || scanAnimationMovSrc"
                    class="office_preview_viewer__loading_anim"
                    autoplay
                    loop
                    muted
                    playsinline>
                    <source v-if="scanAnimationWebmSrc" :src="scanAnimationWebmSrc" type="video/webm">
                    <source v-if="scanAnimationMovSrc" :src="scanAnimationMovSrc" type="video/quicktime">
                </video>
                <div class="office_preview_viewer__loading_text">
                    {{ $t('onlyoffice.loadingSpreadsheet') }}
                </div>
            </div>
        </div>

        <div v-else-if="error" class="office_preview_viewer__state">
            <div class="office_preview_viewer__error_card">
                <div class="office_preview_viewer__error_title">{{ $t('onlyoffice.unavailableTitle') }}</div>
                <div class="office_preview_viewer__error_text">{{ error }}</div>
                <a-button type="primary" @click="reloadViewer">
                    {{ $t('onlyoffice.retry') }}
                </a-button>
            </div>
        </div>

        <div
            v-else
            :id="editorId"
            class="office_preview_viewer__editor"
            :style="editorStyle"></div>
    </div>
</template>

<script>
import { buildOnlyofficePreviewHref } from '@/utils/onlyoffice'

function normalizeServerUrl(url) {
    return String(url || '').replace(/\/+$/, '')
}

export default {
    props: {
        query: {
            type: Object,
            default: () => ({})
        },
        modalMode: {
            type: Boolean,
            default: false
        },
        showClose: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            editor: null,
            editorId: `onlyoffice-preview-editor-${Math.random().toString(36).slice(2, 10)}`,
            loading: true,
            error: '',
            fileName: '',
            downloadUrl: '',
            scanAnimationWebmSrc: '',
            scanAnimationMovSrc: '',
            pendingConfig: null,
            viewportHeight: typeof window !== 'undefined' ? window.innerHeight : 900,
            activeQuery: {}
        }
    },
    metaInfo() {
        return {
            title: this.fileName
                ? `${this.fileName} | ${this.$t('onlyoffice.previewTitle')}`
                : this.$t('onlyoffice.previewTitle')
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        editorHeightPx() {
            const headerHeight = 72
            return Math.max(this.viewportHeight - headerHeight, 480)
        },
        editorStyle() {
            return {
                height: `${this.editorHeightPx}px`
            }
        }
    },
    watch: {
        query: {
            deep: true,
            handler() {
                this.activeQuery = { ...(this.query || {}) }
                this.reloadViewer()
            }
        }
    },
    mounted() {
        window.addEventListener('resize', this.handleResize)
        this.activeQuery = { ...(this.query || {}) }
        this.reloadViewer()
    },
    created() {
        this.loadScanAnimation()
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize)
        this.destroyEditor()
    },
    methods: {
        async loadScanAnimation() {
            this.scanAnimationMovSrc = `${process.env.BASE_URL}animate/scan.mov`

            try {
                const animationModule = await import('@/assets/animate/scan.webm')
                this.scanAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.scanAnimationWebmSrc = ''
            }
        },
        handleResize() {
            this.viewportHeight = window.innerHeight
        },
        openDownload() {
            if (!this.downloadUrl) return
            const link = document.createElement('a')
            link.href = this.downloadUrl
            link.download = ''
            link.rel = 'noopener noreferrer'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        },
        openInNewTab() {
            const href = buildOnlyofficePreviewHref(this.$router, this.query)
            window.open(href, '_blank', 'noopener')
        },
        async refreshReportSessionIfNeeded() {
            const currentQuery = this.activeQuery || {}
            if (currentQuery.scope !== 'report_session' || !currentQuery.session_id) {
                return
            }

            const { data } = await this.$http.post('/onlyoffice/report-session/refresh/', {
                session_id: currentQuery.session_id
            })

            if (!data?.session_id) {
                throw new Error('empty_onlyoffice_report_session')
            }

            this.activeQuery = {
                ...currentQuery,
                session_id: data.session_id
            }
        },
        async reloadViewer(forceRegenerate = false) {
            this.loading = true
            this.error = ''
            this.pendingConfig = null
            this.destroyEditor()

            try {
                if (forceRegenerate) {
                    await this.refreshReportSessionIfNeeded()
                }

                const { data } = await this.$http.get('/onlyoffice/config/', {
                    params: this.activeQuery
                })

                const serverUrl = normalizeServerUrl(data?.document_server_url)
                if (!serverUrl) {
                    throw new Error(this.$t('onlyoffice.serverUrlMissing'))
                }

                await this.ensureOnlyofficeScript(serverUrl)

                if (!window.DocsAPI?.DocEditor) {
                    throw new Error(this.$t('onlyoffice.clientApiMissing'))
                }

                this.fileName = data?.file_name || this.$t('file')
                this.downloadUrl = data?.download_url || ''
                this.pendingConfig = {
                    ...(data?.config || {}),
                    width: '100%',
                    height: `${this.editorHeightPx}px`
                }
                this.loading = false

                await this.$nextTick()
                await new Promise(resolve => window.requestAnimationFrame(resolve))

                if (!this.pendingConfig) {
                    throw new Error(this.$t('onlyoffice.configMissing'))
                }

                this.editor = new window.DocsAPI.DocEditor(this.editorId, this.pendingConfig)
            } catch (error) {
                this.error = error?.data?.detail || error?.detail || error?.message || 'Unknown error'
                this.loading = false
            }
        },
        ensureOnlyofficeScript(serverUrl) {
            if (window.DocsAPI?.DocEditor) {
                return Promise.resolve()
            }

            const source = `${serverUrl}/web-apps/apps/api/documents/api.js`
            if (window.__onlyofficeScriptPromise && window.__onlyofficeScriptSource === source) {
                return window.__onlyofficeScriptPromise
            }

            window.__onlyofficeScriptSource = source
            window.__onlyofficeScriptPromise = new Promise((resolve, reject) => {
                const script = document.createElement('script')
                script.async = true
                script.src = source
                script.onload = () => resolve()
                script.onerror = () => reject(new Error(this.$t('onlyoffice.scriptLoadFailed')))
                document.body.appendChild(script)
            })

            return window.__onlyofficeScriptPromise
        },
        destroyEditor() {
            if (this.editor && typeof this.editor.destroyEditor === 'function') {
                this.editor.destroyEditor()
            }
            this.editor = null
        }
    }
}
</script>

<style lang="scss" scoped>
.office_preview_viewer{
    min-height: 100vh;
    background: #fff;
    display: flex;
    flex-direction: column;
}

.office_preview_viewer--modal{
    min-height: 100%;
    height: 100%;
}

.office_preview_viewer__header{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 10px 20px;
    background: rgba(255, 255, 255, 0.92);
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    backdrop-filter: blur(10px);
}

.office_preview_viewer__title_wrap{
    flex: 1 1 auto;
    min-width: 0;
}

.office_preview_viewer__eyebrow{
    font-size: 11px;
    line-height: 1.2;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5f6b85;
    margin-bottom: 4px;
}

.office_preview_viewer__title{
    font-size: 16px;
    line-height: 1.3;
    font-weight: 600;
    color: #162033;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.office_preview_viewer__actions{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: nowrap;
    justify-content: flex-end;
    flex: 0 0 auto;
}

.office_preview_viewer__action_btn{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
}

.office_preview_viewer__state{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 32px;
}

.office_preview_viewer__loading{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
}

.office_preview_viewer__loading_anim{
    width: 126px;
    height: 126px;
    object-fit: contain;
}

.office_preview_viewer__loading_text{
    color: #586174;
    font-size: 14px;
}

.office_preview_viewer__error_card{
    width: min(420px, 100%);
    padding: 24px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.office_preview_viewer__error_title{
    font-size: 18px;
    font-weight: 600;
    color: #162033;
    margin-bottom: 8px;
}

.office_preview_viewer__error_text{
    color: #586174;
    margin-bottom: 16px;
}

.office_preview_viewer__editor{
    flex: 0 0 auto;
    width: 100%;
}

@media (max-width: 768px) {
    .office_preview_viewer__header{
        padding: 10px 15px;
        gap: 12px;
    }

    .office_preview_viewer__actions{
        justify-content: flex-end;
        gap: 8px;
    }

    .office_preview_viewer__eyebrow{
        display: none;
    }

    .office_preview_viewer__title{
        font-size: 15px;
    }
}
</style>
