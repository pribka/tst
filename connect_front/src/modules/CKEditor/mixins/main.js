import axios from 'axios'
import mixins from './mixins.js'
import { colors, slashFeed } from '../utils/index.js'
import kk from '../lang/kk.js'

class UploadAdapter {
    constructor(loader, component) {
        this.loader = loader
        this.url = component.editorConfig.simpleUpload.uploadUrl
        this.component = component
    }
    async upload() {
        const file = await this.loader.file
        const loader = this.loader
        const genericErrorText = `Couldn't upload file: ${file.name}.`
        const fieldKey = (this.component && this.component.uploadFieldKey) || 'upload'
        const headersCfg = this.component?.editorConfig?.simpleUpload?.headers
        const headers = typeof headersCfg === 'function' ? headersCfg.call(this.component) : headersCfg

        this.cancelSource = axios.CancelToken.source()

        try {
            const response = await this.component.$uploadFile({
                file,
                url: this.url,
                fieldName: fieldKey,
                fileName: file.name,
                headers,
                cancelToken: this.cancelSource.token,
                onProgress: ({ loaded, total }) => {
                    loader.uploadTotal = total || file.size
                    loader.uploaded = loaded
                }
            })

            if (!response || response.error) {
                throw new Error(response?.error?.message || genericErrorText)
            }

            const urls = response.url ? { default: response.url } : response.urls
            return { ...response, urls }
        } catch (error) {
            if (axios.isCancel?.(error) || error?.code === 'ERR_CANCELED')
                return Promise.reject()

            return Promise.reject(error?.message || genericErrorText)
        }
    }
    abort() {
        if (this.cancelSource)
            this.cancelSource.cancel('Upload aborted')
    }
}

export default {
    name: 'CKEditor',
    mixins: [mixins],
    model: { prop: 'value', event: 'input' },

    data() {
        return {
            editorRef: null,
            editorConfig: {
                language: this.$i18n.locale,
                translations: { kk },
                placeholder: this.placeholder,
                mediaEmbed: { previewsInData: true },
                fontBackgroundColor: { colors },
                fontColor: { colorPicker: { format: 'hex' }, colors },
                link: { addTargetToExternalLinks: true },
                simpleUpload: {
                    uploadUrl: this.uploadUrl,
                    withCredentials: true,
                    headers: { 'X-CSRFToken': this.$cookies.get('csrftoken') }
                }
            },
            fromLocalChange: false,
            editorReady: false,
            lastEmittedData: '',
            _domPasteHandler: null,
            _toolbarUpdateTimers: [],
            __toolbarUpdateTimers: [],
            _resizeObserver: null
        }
    },

    created() {
        if(this.chatEditor) {
            this.editorConfig = {
                ...this.editorConfig,
                toolbar: {
                    shouldNotGroupWhenFull: this.shouldNotGroupWhenFull,
                    items: [
                        'bold','italic','underline','strikethrough','link','blockQuote', 'codeBlock'
                    ]
                },
                mention: {
                    dropdownLimit: 20,
                    feeds: this.useUserMentions
                        ? [
                            {
                                marker: '@',
                                feed: this.getChatMemberFeed,
                                itemRenderer: this.renderChatMember
                            },
                            slashFeed
                        ]
                        : [ slashFeed ]
                }
            }
        } else if (this.commentEditor) {
            this.editorConfig = {
                ...this.editorConfig,
                toolbar: {
                    shouldNotGroupWhenFull: this.shouldNotGroupWhenFull,
                    items: [
                        'bold','italic','link',
                        'bulletedList','numberedList','blockQuote',
                        'fontColor','fontBackgroundColor',
                        'imageInsert','mediaEmbed','codeBlock'
                    ]
                },
                mention: {
                    dropdownLimit: 20,
                    feeds: this.useUserMentions
                        ? [
                            {
                                marker: '@',
                                feed: this.getChatMemberFeed,
                                itemRenderer: this.renderChatMember
                            }
                        ]
                        : [ ]
                }
            }
        } else if (this.missionEditor) {
            this.editorConfig = {
                ...this.editorConfig,
                toolbar: {
                    viewportTopOffset: 0,
                    items: ['bold','italic','fontColor','bulletedList','numberedList']
                }
            }
        } else {
            this.editorConfig = {
                ...this.editorConfig,
                toolbar: {
                    shouldNotGroupWhenFull: this.shouldNotGroupWhenFull,
                    items: [
                        'heading','|','alignment','|',
                        'bold','italic','link',
                        'bulletedList','numberedList','blockQuote',
                        'fontColor','fontBackgroundColor',
                        'indent','outdent','pageBreak','|',
                        'imageInsert','insertTable','mediaEmbed',
                        'undo','redo','codeBlock'
                    ]
                },
                image: {
                    toolbar: [
                        'imageStyle:inline','imageStyle:block','imageStyle:side',
                        '|','imageTextAlternative','|','linkImage'
                    ]
                },
                table: {
                    contentToolbar: [
                        'toggleTableCaption','|',
                        'tableColumn','tableRow','mergeTableCells','|',
                        'tableProperties','tableCellProperties'
                    ],
                    tableProperties: { borderColors: colors, backgroundColors: colors },
                    tableCellProperties: { borderColors: colors, backgroundColors: colors }
                },
                mention: {
                    feeds: [{ marker: '#', feed: this.getFeedItems, itemRenderer: this.customItemRenderer }]
                }
            }
        }

        if (this.showTextDecorations && this.editorConfig?.toolbar?.items) {
            const items = this.editorConfig.toolbar.items
            if (!items.includes('underline')) {
                const i = items.indexOf('italic')
                if (i !== -1) items.splice(i + 1, 0, 'underline')
                else items.unshift('underline')
            }
            if (!items.includes('strikethrough')) {
                const j = items.indexOf('underline')
                if (j !== -1) items.splice(j + 1, 0, 'strikethrough')
                else {
                    const b = items.indexOf('bold')
                    if (b !== -1) items.splice(b + 1, 0, 'strikethrough')
                    else items.unshift('strikethrough')
                }
            }
        }
    },

    beforeDestroy() {
        if (this.editorRef && this._domPasteHandler) {
            const domRoot = this.editorRef.editing.view.getDomRoot()
            if (domRoot) domRoot.removeEventListener('paste', this._domPasteHandler, true)
        }
        this.clearToolbarUpdateTimers()
        if (this._resizeObserver) {
            this._resizeObserver.disconnect()
            this._resizeObserver = null
        }
    },

    methods: {
        ensureToolbarTimers() {
            if (!Array.isArray(this._toolbarUpdateTimers)) {
                this._toolbarUpdateTimers = []
            }
            if (!Array.isArray(this.__toolbarUpdateTimers)) {
                this.__toolbarUpdateTimers = this._toolbarUpdateTimers
            }
            if (this.__toolbarUpdateTimers !== this._toolbarUpdateTimers) {
                this.__toolbarUpdateTimers = this._toolbarUpdateTimers
            }
            return this._toolbarUpdateTimers
        },
        clearToolbarUpdateTimers() {
            const timers = this.ensureToolbarTimers()
            timers.forEach(timerId => clearTimeout(timerId))
            timers.length = 0
        },
        forceToolbarUpdate(editor = this.editorRef) {
            if (!editor || !editor.ui) return
            editor.ui.update()
            window.dispatchEvent(new Event('resize'))
        },
        scheduleToolbarReflow(editor = this.editorRef) {
            this.clearToolbarUpdateTimers()
            const timers = this.ensureToolbarTimers()

            requestAnimationFrame(() => this.forceToolbarUpdate(editor))

            ;[80, 180, 320, 520].forEach(delay => {
                const timerId = setTimeout(() => this.forceToolbarUpdate(editor), delay)
                timers.push(timerId)
            })
        },
        observeEditorResize(editor = this.editorRef) {
            if (!window.ResizeObserver || !editor) return
            if (this._resizeObserver) this._resizeObserver.disconnect()

            const host = this.$el
            if (!host) return

            this._resizeObserver = new ResizeObserver(() => {
                this.forceToolbarUpdate(editor)
            })
            this._resizeObserver.observe(host)
        },
        escapeAttr(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/"/g, '&quot;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
        },

        sanitizeChatHtml(html) {
            if (!html) return ''

            const ALLOWED = new Set([
                'A',
                'B',
                'STRONG',
                'I',
                'U',
                'S',
                'DEL',
                'STRIKE'
            ])

            const doc = new DOMParser().parseFromString(String(html), 'text/html')

            const render = node => {
                let out = ''

                node.childNodes.forEach(child => {
                    if (child.nodeType === Node.TEXT_NODE) {
                        out += child.textContent
                        return
                    }

                    if (child.nodeType !== Node.ELEMENT_NODE) return

                    if (ALLOWED.has(child.tagName) || child.tagName === 'SPAN') {
                        if (child.tagName === 'A') {
                            const href = child.getAttribute('href')
                            if (href) out += `<a href="${this.escapeAttr(href)}" target="_blank">${render(child)}</a>`
                            else out += render(child)
                            return
                        }

                        if (child.tagName === 'SPAN') {
                            const cls = child.getAttribute('class')
                            const dataMention = child.getAttribute('data-mention')
                            const dataId = child.getAttribute('data-id')
                            const dataType = child.getAttribute('data-type')

                            let attrs = ''
                            if (cls) attrs += ` class="${this.escapeAttr(cls)}"`
                            if (dataMention) attrs += ` data-mention="${this.escapeAttr(dataMention)}"`
                            if (dataId) attrs += ` data-id="${this.escapeAttr(dataId)}"`
                            if (dataType) attrs += ` data-type="${this.escapeAttr(dataType)}"`

                            out += `<span${attrs}>${render(child)}</span>`
                            return
                        }

                        const tag = child.tagName.toLowerCase()
                        out += `<${tag}>${render(child)}</${tag}>`
                        return
                    }

                    out += render(child)
                })

                return out
            }

            return render(doc.body)
                .replace(/(\r\n|\n|\r)/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()
        },

        looksLikeCode(text) {
            if (!text) return false

            const lines = text.split('\n')
            if (lines.length < 2) return false

            const indentLines = lines.filter(l => /^\s{2,}|\t/.test(l))
            if (indentLines.length >= Math.max(2, lines.length / 2)) return true

            return /[{}();<>]=|=>|<\/\w+>/.test(text)
        },
        fixMentionClassesHtml(html) {
            if (!html) return html
            const doc = new DOMParser().parseFromString(String(html), 'text/html')
            const nodes = Array.from(doc.body.querySelectorAll('span.mention[data-type="user"]'))
            nodes.forEach(el => {
                if (!el.classList.contains('user_chat_mention')) el.classList.add('user_chat_mention')
            })
            return doc.body.innerHTML
        },
        applyMentionClassesInView(editor) {
            const view = editor.editing.view
            const root = view.document.getRoot()

            view.change(writer => {
                const range = writer.createRangeIn(root)
                for (const item of range.getItems()) {
                    if (!item.is('attributeElement')) continue
                    if (!item.hasClass('mention')) continue

                    const type = item.getAttribute('data-type')
                    if (type === 'user' && !item.hasClass('user_chat_mention')) {
                        writer.addClass('user_chat_mention', item)
                    }
                }
            })
        },
        normalizeTables(html) {
            if (!html) return html
            const doc = new DOMParser().parseFromString(html, 'text/html')
            const tables = Array.from(doc.body.querySelectorAll('table'))
            tables.forEach(t => {
                t.classList.add('ck-table')
                const parent = t.parentElement
                if (parent && parent.classList.contains('table-scroll')) return
                const wrapper = doc.createElement('div')
                wrapper.className = 'table-scroll'
                parent.replaceChild(wrapper, t)
                wrapper.appendChild(t)
            })
            return doc.body.innerHTML
        },

        normalizeHref(href) {
            let url = String(href)

            if (!/^https?:\/\//i.test(url) && /^www\./i.test(url)) url = 'http://' + url

            url = url
                .replace(/"/g, '%22')
                .replace(/{/g, '%7B')
                .replace(/}/g, '%7D')

            return url
        },

        stripBackgroundHtml(html) {
            const doc = new DOMParser().parseFromString(html, 'text/html')
            const all = doc.body.querySelectorAll('[style], [bgcolor]')
            all.forEach(el => {
                if (el.hasAttribute('bgcolor')) el.removeAttribute('bgcolor')
                const style = el.getAttribute('style') || ''
                if (!style) return
                const cleaned = style
                    .split(';')
                    .map(s => s.trim())
                    .filter(s =>
                        s &&
                        !/^background(?:-color)?\s*:/i.test(s) &&
                        !/^color\s*:/i.test(s)
                    )
                    .join('; ')
                if (cleaned) el.setAttribute('style', cleaned)
                else el.removeAttribute('style')
            })

            const tableEls = doc.body.querySelectorAll('table, td, th, col, colgroup')
            tableEls.forEach(el => {
                el.removeAttribute('style')
                el.removeAttribute('width')
                el.removeAttribute('height')
                el.removeAttribute('border')
                el.removeAttribute('cellpadding')
                el.removeAttribute('cellspacing')
                el.removeAttribute('align')
                el.removeAttribute('valign')
                el.removeAttribute('bgcolor')
            })

            const colgroups = doc.body.querySelectorAll('colgroup')
            colgroups.forEach(cg => cg.remove())

            return doc.body.innerHTML
        },

        linkifyTextNode(node, doc) {
            const re = /(https?:\/\/[^\s<>']+|www\.[^\s<>']+)/gi
            const text = node.nodeValue
            if (!re.test(text)) return null

            const frag = doc.createDocumentFragment()
            let lastIndex = 0

            text.replace(re, (m, offset) => {
                if (offset > lastIndex)
                    frag.appendChild(doc.createTextNode(text.slice(lastIndex, offset)))

                const a = doc.createElement('a')
                a.setAttribute('href', this.normalizeHref(m))
                a.textContent = m
                frag.appendChild(a)

                lastIndex = offset + m.length
            })

            if (lastIndex < text.length)
                frag.appendChild(doc.createTextNode(text.slice(lastIndex)))

            return frag
        },

        linkifyRoot(root) {
            let changed = false
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false)
            let node
            const toReplace = []
            while ((node = walker.nextNode())) {
                if (node.parentElement && node.parentElement.closest('a')) continue
                const frag = this.linkifyTextNode(node, root.ownerDocument || document)
                if (frag) toReplace.push([node, frag])
            }
            toReplace.forEach(([n, f]) => {
                n.replaceWith(f)
                changed = true
            })
            return changed
        },

        linkifyHtml(html) {
            const doc = new DOMParser().parseFromString(html, 'text/html')
            const changed = this.linkifyRoot(doc.body)
            return changed ? doc.body.innerHTML : html
        },

        linkifyAll() {
            if (!this.editorRef) return

            const html = this.editorRef.getData()
            const linked = this.linkifyHtml(html)

            if (linked !== html) {
                this.editorRef.setData(linked)
            }
        },

        onReady(editor) {
            this.editorRef = editor

            const mentionCommand = editor.commands.get('mention')

            if (mentionCommand && !mentionCommand.__slashWrapped) {
                mentionCommand.__slashWrapped = true

                const originalExecute = mentionCommand.execute.bind(mentionCommand)

                mentionCommand.execute = options => {
                    const mention = options && options.mention

                    if (
                        mention &&
                        mention.action &&
                        String(mention.id).startsWith('/')
                    ) {
                        editor.model.change(writer => {
                            if (options.range) writer.remove(options.range)
                        })

                        this.sendChatEvent(mention.action)
                        return
                    }

                    return originalExecute(options)
                }
            }

            editor.model.document.on('change:data', () => {
                if (!this.editorReady) return

                const data = editor.getData()
                const next = this.fixMentionClassesHtml(this.normalizeTables(data))

                this.fromLocalChange = true
                this.lastEmittedData = next
                this.$emit('input', next)
                this.$emit('change', next)
                this.$nextTick(() => { this.fromLocalChange = false })
            })

            const initial = String(this.value || '')
            const normalizedInitial = this.normalizeTables(initial)
            const fixedInitial = this.fixMentionClassesHtml(normalizedInitial)
            if (fixedInitial !== editor.getData()) editor.setData(fixedInitial)

            requestAnimationFrame(() => this.applyMentionClassesInView(editor))

            const view = editor.editing.view
            view.change(writer => {
                writer.setAttribute('placeholder', this.placeholder, view.document.getRoot())
            })

            if (this.initFocus) {
                this.editorFocus()
                if (this.commentEditor || this.chatEditor) this.EnterShiftHandler()
            }

            editor.plugins.get('FileRepository').createUploadAdapter = loader => new UploadAdapter(loader, this)

            const pipeline = editor.plugins.get('ClipboardPipeline')

            pipeline.on('clipboardInput', (evt, data) => {
                if (!this.chatEditor) return

                const dt = data.dataTransfer
                const directFiles = this.extractFilesFromDataTransfer(dt)

                if (directFiles.length) {
                    evt.stop()
                    data.preventDefault()
                    this.$emit('uploadFiles', directFiles)
                }
            }, { priority: 'highest' })

            pipeline.on('inputTransformation', (evt, data) => {
                const html = editor.data.processor.toData(data.content)
                const next = this.normalizeTables(this.linkifyHtml(html))

                if (next !== html)
                    data.content = editor.data.processor.toView(next)
            })

            const domRoot = editor.editing.view.getDomRoot()
            if (domRoot && !this._domPasteHandler) {
                this._domPasteHandler = e => {
                    if (!this.chatEditor) return

                    const dt = e.clipboardData
                    const directFiles = this.extractFilesFromDataTransfer(dt)

                    if (directFiles.length) {
                        e.preventDefault()
                        e.stopPropagation()
                        this.$emit('uploadFiles', directFiles)
                    }
                }

                domRoot.addEventListener('paste', this._domPasteHandler, true)
            }

            const viewDoc = editor.editing.view.document
            viewDoc.on('blur', () => {
                this.linkifyAll()
                this.applyMentionClassesInView(editor)
            })

            viewDoc.on('clipboardInput', (evt, data) => {
                if (!this.chatEditor) return

                const html = data.dataTransfer.getData('text/html')
                const text = data.dataTransfer.getData('text/plain')

                if (text && this.looksLikeCode(text)) {
                    evt.stop()
                    editor.model.change(writer => {
                        const codeBlock = writer.createElement('codeBlock')
                        writer.appendText(text, codeBlock)
                        editor.model.insertContent(codeBlock)
                    })
                    return
                }

                if (html) {
                    evt.stop()

                    const cleaned = this.stripBackgroundHtml(
                        this.sanitizeChatHtml(html)
                    )

                    editor.model.change(() => {
                        const view = editor.data.processor.toView(cleaned)
                        const model = editor.data.toModel(view)
                        editor.model.insertContent(model)
                    })
                }
            })

            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    this.scheduleToolbarReflow(editor)
                    this.observeEditorResize(editor)
                    this.$emit('onReady')
                    this.editorReady = true
                })
            })
        },

        EnterShiftHandler() {
            this.editorRef.editing.view.document.on(
                'enter',
                (evt, data) => {
                    const isShift = data.domEvent.shiftKey
                    const isEnter = data.domEvent.keyCode === 13

                    if (!isEnter) return

                    const shouldSend = this.behaviorStatus
                        ? !isShift
                        : isShift

                    if (!shouldSend) return

                    data.preventDefault()
                    evt.stop()
                    this.enterShifthHand()
                },
                { priority: 'high' }
            )
        },

        editorFocus() {
            if (!this.editorRef) return
            this.editorRef.focus()
            this.editorRef.model.change(writer => {
                writer.setSelection(
                    writer.createPositionAt(this.editorRef.model.document.getRoot(), 'end')
                )
            })
        },

        focus() {
            this.editorFocus()
        },

        clearContent() {
            if (!this.editorRef) return

            this.fromLocalChange = true
            this.lastEmittedData = ''
            this.editorRef.setData('')

            requestAnimationFrame(() => {
                this.applyMentionClassesInView(this.editorRef)
                this.fromLocalChange = false
            })
        },

        insertText(text) {
            if (!this.editorRef) return
            this.editorRef.focus()
            this.editorRef.model.change(writer => {
                const pos = this.editorRef.model.document.selection.getFirstPosition()
                writer.insertText(text, pos)
            })
        }
    },

    watch: {
        value(n) {
            if (!this.editorRef || !this.editorReady) return
            const normalized = this.normalizeTables(n || '')
            const fixed = this.fixMentionClassesHtml(normalized)
            const cur = this.editorRef.getData()

            if (fixed === cur) return
            if (this.fromLocalChange && fixed !== '') return
            if (fixed === this.lastEmittedData && fixed !== '') return

            this.editorRef.setData(fixed)

            requestAnimationFrame(() => this.applyMentionClassesInView(this.editorRef))
        },
        placeholder(n) {
            if (!this.editorRef) return
            const view = this.editorRef.editing.view
            view.change(writer => {
                writer.setAttribute('placeholder', n, view.document.getRoot())
            })
        }
    }
}
