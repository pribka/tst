<template>
    <div class="tv_root">
        <div
            class="ck_text_viewer_wrap"
            :class="[{ collapsed: isCollapsed && canCollapse }]"
            @click="onRootClick">
            <div
                ref="CKTextViewer"
                class="ck_text_viewer"
                v-html="linkedBody"
                :style="isCollapsed && canCollapse ? { maxHeight: collapsedHeight + 'px', overflow: 'hidden' } : null"/>
            <div
                v-if="isCollapsed && canCollapse"
                class="tv_overlay"
                :style="{ background: `linear-gradient(to bottom, rgba(0,0,0,0), ${overlayColor || overlayBg})` }"
                @click.stop="toggle"></div>
        </div>
        <div
            v-if="canCollapse"
            class="tv_toggle"
            :class="toggleAlign"
            :style="`color:${toggleButtonColor};`"
            @click.stop="toggle">
            {{ isCollapsed ? $t(expandLabel) : $t(collapseLabel) }}
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

const REPORT_SETTINGS_EXPORT_KIND = 'ReportSetting'
const REPORT_SETTINGS_FILE_PREFIX = 'ReportSetting-'

export default {
    props: {
        body: {
            type: String,
            default: ''
        },
        collapseHandler: {
            type: Function,
            default: () => {}
        },
        collapsible: {
            type: Boolean,
            default: false
        },
        collapsedHeight: {
            type: Number,
            default: 80
        },
        expandLabel: {
            type: String,
            default: 'expand_comment'
        },
        collapseLabel: {
            type: String,
            default: 'collapse_comment'
        },
        toggleAlign: {
            type: String,
            default: 'left'
        },
        overlayColor: {
            type: String,
            default: '#eef2f5'
        },
        toggleButtonColor: {
            type: String,
            default: 'var(--blue)'
        }
    },
    computed: {
        linkedBody() {
            if(!this.body) return ''

            const doc = new DOMParser().parseFromString(this.body, 'text/html')
            const root = doc.body

            const testRe = /(https?:\/\/[^\s<>"']+|www\.[^\s<>"']+)/i
            const replaceRe = /(https?:\/\/[^\s<>"']+|www\.[^\s<>"']+)/gi

            const walker = doc.createTreeWalker(
                root,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode(node) {
                        const p = node.parentElement
                        if(!p) return NodeFilter.FILTER_REJECT
                        if(p.closest('a, pre, code')) return NodeFilter.FILTER_REJECT
                        if(!testRe.test(node.nodeValue)) return NodeFilter.FILTER_REJECT
                        return NodeFilter.FILTER_ACCEPT
                    }
                }
            )

            const nodes = []
            let n
            while((n = walker.nextNode())) nodes.push(n)

            nodes.forEach(node => {
                const text = node.nodeValue
                const frag = doc.createDocumentFragment()
                let lastIndex = 0

                text.replace(replaceRe, (...args) => {
                    const match = args[0]
                    const offset = args[args.length - 2]

                    if(offset > lastIndex) {
                        frag.appendChild(
                            doc.createTextNode(text.slice(lastIndex, offset))
                        )
                    }

                    const a = doc.createElement('a')
                    a.href = /^https?:\/\//i.test(match) ? match : 'http://' + match
                    a.textContent = match
                    a.target = '_blank'
                    a.rel = 'noopener noreferrer'
                    frag.appendChild(a)

                    lastIndex = offset + match.length
                })

                if(lastIndex < text.length) {
                    frag.appendChild(
                        doc.createTextNode(text.slice(lastIndex))
                    )
                }

                node.replaceWith(frag)
            })

            root.querySelectorAll('a').forEach(link => {
                if (!this.isReportSettingsLink(link)) return

                const reportName = this.extractReportSettingsReportName(link)
                link.dataset.reportSettings = 'true'
                link.classList.add('report_settings_link')
                link.textContent = `${this.$t('Report - ')}${reportName || this.$t('Untitled')}`
            })

            return root.innerHTML
        }
    },
    data() {
        return {
            isCollapsed: true,
            canCollapse: false,
            mo: null,
            ro: null,
            overlayBg: '#fff',
            lg: null,
            lgInst: null,
            lazyHandler: null
        }
    },
    methods: {
        onRootClick(e) {
            const stopNode = e.target.closest('a, .tv_toggle, .tv_overlay, [data-mention]')
            if(stopNode) e.stopPropagation()

            const link = e.target.closest('a')
            if (link && this.isReportSettingsLink(link)) {
                e.preventDefault()
                e.stopPropagation()
                this.openReportSettingsLink(link)
            }
        },
        isReportSettingsName(value = '') {
            return String(value || '').trim().startsWith(REPORT_SETTINGS_FILE_PREFIX)
        },
        extractReportSettingsReportName(link) {
            const rawName = String(link?.dataset?.reportSettingsName || link?.textContent || '')
                .trim()
                .replace(/\.json$/i, '')

            return rawName.startsWith(REPORT_SETTINGS_FILE_PREFIX)
                ? rawName.slice(REPORT_SETTINGS_FILE_PREFIX.length).trim()
                : ''
        },
        isReportSettingsLink(link) {
            if (!link) return false

            if (link.dataset?.reportSettings === 'true') return true

            const text = String(link.textContent || '').trim()
            return this.isReportSettingsName(text)
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
        getAuthenticatedFileUrl(rawUrl = '') {
            const fileUrl = new URL(rawUrl, window.location.origin)
            return `${window.location.origin}${fileUrl.pathname}${fileUrl.search}`
        },
        async openReportSettingsLink(link) {
            const href = String(link?.getAttribute('href') || '').trim()
            if (!href) return

            try {
                const { data } = await this.$http.get(this.getAuthenticatedFileUrl(href), {
                    responseType: 'text'
                })
                const parsedSettings = typeof data === 'string' ? JSON.parse(data) : data
                const templateData = this.normalizeImportedReportSettings(parsedSettings)

                await this.$store.dispatch('reports/openReportModal', templateData)
            } catch (error) {
                console.error(error)
                this.$message.error(this.$t('Failed to open report settings'))
            }
        },
        addEventListenersToMentions() {
            const root = this.$refs.CKTextViewer
            if(!root) return
            const mentions = root.querySelectorAll('[data-mention]')
            mentions.forEach(mention => {
                mention.addEventListener('click', e => {
                    e.stopPropagation()
                    const dataset = e.target.dataset
                    this.mentionClickHandler(dataset)
                })
            })
        },
        async mentionClickHandler(dataset) {
            if(dataset.type === 'task') {
                eventBus.$emit('OPEN_TASK_DRAWER', dataset.id)
            }
        },
        measure() {
            const el = this.$refs.CKTextViewer
            if(!el) return
            this.$nextTick(() => {
                const need = el.scrollHeight > this.collapsedHeight + 2
                this.canCollapse = this.collapsible && need
                if(!this.canCollapse) this.isCollapsed = false
            })
        },
        detectOverlayBg() {
            if(this.overlayColor) return
            const wrap = this.$el.querySelector('.ck_text_viewer_wrap')
            if(!wrap) return
            const bg = window.getComputedStyle(wrap).backgroundColor || ''
            if(bg) this.overlayBg = bg
        },
        bindImageLoads() {
            const el = this.$refs.CKTextViewer
            if(!el) return
            const imgs = el.querySelectorAll('img')
            imgs.forEach(img => {
                if(!img.complete) img.addEventListener('load', this.measure, { once: true })
            })
        },
        wrapImagesForLightbox() {
            const root = this.$refs.CKTextViewer
            if(!root) return
            const imgs = root.querySelectorAll('img')
            imgs.forEach(img => {
                const parent = img.parentElement
                if (parent && parent.tagName.toLowerCase() === 'a' && parent.classList.contains('lht_l')) return
                const href = img.getAttribute('data-src') || img.getAttribute('src')
                if (!href) return
                const a = document.createElement('a')
                a.className = 'lht_l'
                a.href = href
                parent ? parent.replaceChild(a, img) : root.appendChild(a)
                a.appendChild(img)
            })
        },
        async getLG() {
            if (this.lg) return this.lg
            if (typeof window !== 'undefined' && (window.lightGallery || window.lightgallery))
                this.lg = window.lightGallery || window.lightgallery
            else {
                const mod = await import('lightgallery.js')
                this.lg = mod.default || mod
            }
            return this.lg
        },
        destroyLightbox() {
            if (this.lgInst && this.lgInst.destroy) {
                try { this.lgInst.destroy(true) } catch(e) {}
                this.lgInst = null
            }
        },
        async initLightboxIfNeeded() {
            const root = this.$refs.CKTextViewer
            if(!root) return
            const links = root.querySelectorAll('.lht_l')
            if(!links.length) return
            const LG = await this.getLG()
            this.destroyLightbox()
            this.lgInst = LG(root, {
                selector: '.lht_l',
                thumbnail: true,
                rotateLeft: true,
                rotateRight: true,
                fullScreen: true,
                animateThumb: true,
                showThumbByDefault: true,
                download: true,
                speed: 300
            })
        },
        scheduleLGInit() {
            this.$nextTick(() => {
                this.wrapImagesForLightbox()
                this.initLightboxIfNeeded()
            })
        },
        setupObservers() {
            const el = this.$refs.CKTextViewer
            if(!el) return
            this.mo = new MutationObserver(() => {
                this.bindImageLoads()
                this.measure()
                this.addEventListenersToMentions()
                this.detectOverlayBg()
                this.scheduleLGInit()
            })
            this.mo.observe(el, { childList: true, subtree: true, attributes: true, characterData: true })
            this.ro = new ResizeObserver(() => this.measure())
            this.ro.observe(el)
            window.addEventListener('resize', this.measure)
            if(!this.lazyHandler) {
                this.lazyHandler = e => {
                    const t = e && e.target
                    if(!t) return
                    const root = this.$refs.CKTextViewer
                    if(root && root.contains(t)) this.scheduleLGInit()
                }
                document.addEventListener('lazyloaded', this.lazyHandler, true)
            }
        },
        cleanupObservers() {
            if(this.mo) {
                this.mo.disconnect()
                this.mo = null
            }
            if(this.ro) {
                this.ro.disconnect()
                this.ro = null
            }
            window.removeEventListener('resize', this.measure)
            if(this.lazyHandler) {
                document.removeEventListener('lazyloaded', this.lazyHandler, true)
                this.lazyHandler = null
            }
        },
        toggle() {
            this.isCollapsed = !this.isCollapsed
            this.$nextTick(() => {
                this.addEventListenersToMentions()
                this.collapseHandler()
            })
        }
    },
    async mounted() {
        await this.$nextTick()
        this.addEventListenersToMentions()
        this.bindImageLoads()
        this.measure()
        this.detectOverlayBg()
        this.wrapImagesForLightbox()
        await this.initLightboxIfNeeded()
        this.setupObservers()
        eventBus.$on('UPDATE_TEXT_VIEWER', async () => {
            await this.$nextTick()
            this.addEventListenersToMentions()
            this.bindImageLoads()
            this.isCollapsed = true
            this.measure()
            this.detectOverlayBg()
            this.wrapImagesForLightbox()
            await this.initLightboxIfNeeded()
        })
    },
    watch: {
        body() {
            this.$nextTick(async () => {
                this.addEventListenersToMentions()
                this.bindImageLoads()
                this.isCollapsed = true
                this.measure()
                this.detectOverlayBg()
                this.wrapImagesForLightbox()
                await this.initLightboxIfNeeded()
            })
        },
        collapsedHeight() {
            this.measure()
        },
        collapsible() {
            this.measure()
        },
        overlayColor() {
            this.detectOverlayBg()
        }
    },
    beforeDestroy() {
        eventBus.$off('UPDATE_TEXT_VIEWER')
        this.cleanupObservers()
        this.destroyLightbox()
    }
}
</script>

<style lang="scss">
@import './scss/variables.scss';

.tv_root{
    width: 100%;
}
.ck_text_viewer_wrap{
    position: relative;
}
.tv_overlay{
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 56px;
    pointer-events: none;
}
.tv_toggle{
    margin-top: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.right{
        text-align: right;
    }
    &.left{
        text-align: left;
    }
    &:hover{
        opacity: 0.6;
    }
}
.ck_text_viewer{
    @include ckeditorStyle;
    word-break: break-word;
    white-space: normal;
    .report_settings_link{
        cursor: pointer;
    }
    .user_chat_mention{
        background: rgba(0, 0, 0, 0.1);
        border-radius: 6px;
        padding: 2px 4px;
    }
    pre{
        background: var(--bgColor2);
        border: 1px solid var(--borderColor);
        border-radius: var(--borderRadius);
        overflow: auto;
        padding: 15px;
        width: auto;
        max-height: 600px;
        overflow-wrap: normal;
    }
}

</style>
