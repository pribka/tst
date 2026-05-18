<template>
    <div>
        <template v-if="!activeChat.is_support">
            <a-button
                v-if="isMobile"
                type="flat_primary"
                class="ant-btn-icon-only flex justify-center items-center"
                shape="circle"
                icon="fi-ai-rr-sparkles"
                flaticon
                @click="open" />
            <a-button
                v-else
                type="flat_primary"
                class="ant-btn-icon-only flex justify-center items-center"
                v-tippy
                icon="fi-ai-rr-sparkles"
                flaticon
                shape="circle"
                :content="$t('chat.ai_summary')"
                @click="open" />
        </template>
        <DrawerTemplate
            v-model="visible"
            destroyOnClose
            :title="$t('chat.ai_summary')"
            :width="drawerWidth"
            @afterVisibleChange="afterVisibleChange"
            @close="visible = false">

            <a-alert
                type="info"
                showIcon
                :message="$t('chat.summary_description')" />

            <div class="mb-1 mt-3">
                <a-range-picker
                    v-model="range"
                    class="w-full range_input"
                    format="DD.MM.YYYY"
                    separator="-"
                    allowClear
                    :ranges="presets"
                    :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
                    :placeholder="[$t('from'), $t('to')]"
                    @change="onChange" />
            </div>

            <a-spin :spinning="summaryLoading" class="w-full mt-4" size="small">
                <div v-if="!summaryData && generateStatus || summaryData && summaryPending" class="summary_card rounded-lg">
                    <div class="mt-3 mb-2 summary_text flex items-center">
                        <video
                            v-if="pendingAnimationSrc"
                            class="summary_text__anim mr-3"
                            :src="pendingAnimationSrc"
                            autoplay
                            loop
                            muted
                            playsinline />
                        {{ $t('chat.summary_success_2') }}
                    </div>
                </div>

                <div v-if="summaryData && !summaryPending" class="summary_card rounded-lg">
                    <div class="summary_card__header select-none flex items-center justify-between truncate">
                        <h4 class="summary_card__label truncate font-semibold mb-0">
                            <i class="fi fi-rr-pen-field mr-2" />
                            {{ $t('chat.analysis') }}
                        </h4>
                    </div>
                    <div class="flex items-center gap-2 mt-3">
                        <a-button 
                            flaticon 
                            icon="fi-rr-undo" 
                            @click="sendToChat()">
                            {{ $t('chat.send_to_chat') }}
                        </a-button>
                        <a-button 
                            flaticon 
                            v-tippy
                            :content="$t('chat.copy_to_clipboard')"
                            icon="fi-rr-copy-alt" 
                            @click="textCopy()" />
                        <a-button 
                            flaticon 
                            v-tippy
                            :content="$t('chat.text_print')"
                            icon="fi-rr-print" 
                            @click="textPrint()" />
                    </div>
                    <div v-if="summaryData.completed_at" class="mt-2">
                        {{ $t('chat.generation_date') }} {{ $moment(summaryData.completed_at).format('DD.MM.YYYY HH:mm') }}
                    </div>
                    <div v-html="summaryHtml" class="mt-2 mb-2 summary_text" />
                </div>
            </a-spin>

            <template #footer>
                <ai-button
                    type="primary"
                    size="large"
                    block
                    class="flex items-center justify-center"
                    :loading="loading"
                    @click="generate">
                    {{ $t('chat.generate_ai_btn') }}
                </ai-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
import ChatEventBus from '../../utils/ChatEventBus.js'
import { mapState } from 'vuex'
export default {
    props: {
        activeChat: {
            type: Object,
            default: () => null
        }
    },
    components: {
        AiButton: () => import('@apps/UIModules/AIButton/index.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    data() {
        return {
            visible: false,
            loading: false,
            range: null,
            summaryLoading: false,
            summaryData: null,
            generateStatus: false,
            pendingAnimationSrc: ''
        }
    },
    watch: {
        activeChat() {
            this.visible = false
            this.$nextTick(() => {
                this.checkSummaryActive()
            })
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            isSafari: state => state.isSafari
        }),
        summaryPending() {
            return this.summaryData?.status === 'pending' ? true : false
        },
        summaryHtml() {
            if (!this.summaryData.summary) return ''

            return this.summaryData.summary
                .replace(/(^|\n)\s*(\d+\.)\s*\.?\s*_+/g, '$1$2 ')
                .replace(/_+(\s*\n|$)/g, '$1')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .trim()
                .replace(/^/, '<p>')
                .replace(/$/, '</p>')
        },
        drawerWidth() {
            if(this.isMobile) {
                return '100%'
            } else {
                return 660
            }
        },
        presets() {
            const now = this.$moment()
            return {
                [this.$t('today')]: [now.clone().startOf('day'), now.clone().endOf('day')],
                [this.$t('yesterday')]: [now.clone().subtract(1, 'day').startOf('day'), now.clone().subtract(1, 'day').endOf('day')],
                [this.$t('current_week')]: [now.clone().startOf('week'), now.clone().endOf('week')],
                [this.$t('current_month')]: [now.clone().startOf('month'), now.clone().endOf('month')],
                [this.$t('current_year')]: [now.clone().startOf('year'), now.clone().endOf('year')]
            }
        }
    },
    sockets: {
        notify({ data }) {
            if (data.event_type !== 'new_notification') return
            const res = data.obj
            this.checkAiSummaryNotify(res)
        }
    },
    methods: {
        async loadPendingAnimation() {
            try {
                if (this.isSafari) {
                    this.pendingAnimationSrc = `${process.env.BASE_URL}animate/AI_mov.mov`
                    return
                }
                const animationModule = await import('@/assets/animate/AI.webm')
                this.pendingAnimationSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.pendingAnimationSrc = ''
            }
        },
        checkAiSummaryNotify(res) {
            try {
                const msg = String(res?.message || '')
                if (!msg) return
                if (!this.activeChat?.chat_uid) return
                if (!msg.includes('data-link-type="chat"')) return
                if (!msg.includes('data-link-query')) return

                const div = document.createElement('div')
                div.innerHTML = msg

                const el = div.querySelector('span[data-link-type="chat"][data-link-query]')
                if (!el) return

                let q = el.getAttribute('data-link-query') || ''
                if (!q) return

                q = q
                    .replace(/&quot;/g, '"')
                    .replace(/&#34;/g, '"')
                    .replace(/\\"/g, '"')
                    .replace(/\\'/g, "'")
                    .trim()

                if ((q.startsWith("'") && q.endsWith("'")) || (q.startsWith('"') && q.endsWith('"')))
                    q = q.slice(1, -1)

                let query = null
                try {
                    query = JSON.parse(q)
                } catch (e) {
                    query = JSON.parse(q.replace(/\\/g, ''))
                }

                const chatId = String(query?.chat_id || '')
                const ai = query?.ai_summary === true || String(query?.ai_summary) === 'true'

                if (ai && chatId && chatId === String(this.activeChat.chat_uid)) {
                    this.getSummary()
                }
            } catch (e) {}
        },
        splitSummaryHtml(html, limit = 4096) {
            const src = String(html || '').trim()
            if (!src) return []

            const wrapP = s => `<p>${s}</p>`

            const unwrap = s => s
                .replace(/^\s*<p>/i, '')
                .replace(/<\/p>\s*$/i, '')
                .trim()

            const body = unwrap(src)

            const splitBy = (text, sep) => {
                if (!text) return []
                return text.split(sep).map(x => x.trim()).filter(Boolean)
            }

            const hardSplit = (text) => {
                const out = []
                let t = String(text || '').trim()
                while (t.length > limit) {
                    let cut = t.slice(0, limit)
                    const lastSpace = cut.lastIndexOf(' ')
                    if (lastSpace > 50) cut = cut.slice(0, lastSpace)
                    out.push(cut.trim())
                    t = t.slice(cut.length).trim()
                }
                if (t) out.push(t)
                return out
            }

            const chunks = []
            let current = ''

            const pushCurrent = () => {
                const c = current.trim()
                if (c) chunks.push(wrapP(c))
                current = ''
            }

            const tryAdd = (piece, joiner) => {
                const next = current ? `${current}${joiner}${piece}` : piece
                if (wrapP(next).length <= limit) {
                    current = next
                    return true
                }
                return false
            }

            const blocks = splitBy(body, /<br\s*\/?>\s*<br\s*\/?>/i)

            blocks.forEach(block => {
                if (wrapP(block).length <= limit) {
                    if (!tryAdd(block, '<br><br>')) {
                        pushCurrent()
                        current = block
                    }
                    return
                }

                const lines = splitBy(block, /<br\s*\/?>/i)

                lines.forEach(line => {
                    if (wrapP(line).length <= limit) {
                        if (!tryAdd(line, '<br>')) {
                            pushCurrent()
                            current = line
                        }
                        return
                    }

                    const parts = hardSplit(line)
                    parts.forEach(part => {
                        if (!tryAdd(part, ' ')) {
                            pushCurrent()
                            current = part
                        }
                    })
                })
            })

            pushCurrent()
            return chunks
        },

        sendToChat() {
            const base = {
                attachments: [],
                chat: this.summaryData.chat,
                chat_uid: this.summaryData.chat,
                is_ai_message: true
            }

            const parts = this.splitSummaryHtml(this.summaryHtml, 4096)

            parts.forEach((text, idx) => {
                this.$socket.client.emit('message', {
                    ...base,
                    text,
                    ai_part: idx + 1,
                    ai_part_total: parts.length
                })
            })

            this.visible = false
            ChatEventBus.$emit('arreaScrollDown', false)
        },
        textCopy() {
            if (!this.summaryData?.summary) return

            const div = document.createElement('div')
            div.innerHTML = this.summaryHtml
            const text = div.innerText || div.textContent || ''

            navigator.clipboard.writeText(text).then(() => {
                this.$message.success(this.$t('copied'))
            }).catch(() => {
                this.$message.error(this.$t('copy_error'))
            })
        },
        textPrint() {
            if (!this.summaryData?.summary) return

            const win = window.open('', '_blank')
            if (!win) return

            win.document.write(`
            <html>
                <head>
                    <title>${this.$t('chat.ai_summary')}</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            padding: 20px;
                            line-height: 1.5;
                        }
                        p {
                            margin-bottom: 10px;
                        }
                    </style>
                </head>
                <body>
                    ${this.summaryHtml}
                </body>
            </html>
        `)

            win.document.close()
            win.focus()
            win.print()
            win.close()
        },
        open() {
            this.visible = true
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getSummary()
            } else {
                this.close()
                if(!this.isMobile)
                    ChatEventBus.$emit('inputFocus')
            }
        },
        close() {
            this.visible = false
            this.loading = false
            this.range = null
            this.summaryData = null
            this.generateStatus = false
        },
        onChange(value) {
            if (!value || !value.length) {
                this.range = null
            }
        },
        async getSummary() {
            try {
                this.generateStatus = false
                this.summaryLoading = true
                const { data } = await this.$http.get(`/chat/${this.activeChat.chat_uid}/summary/`)
                if(data) {
                    this.summaryData = data
                }
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.summaryLoading = false
            }
        },
        async generate() {
            if (!this.range?.[0] || !this.range?.[1]) {
                this.$message.error(this.$t('chat.summary_select_date'))
                return
            }

            const start = this.range[0].format('YYYY-MM-DD')
            const end = this.range[1].format('YYYY-MM-DD')

            this.loading = true
            try {
                await this.$http.post(`/chat/${this.activeChat.chat_uid}/summary/`, { start, end })
                this.generateStatus = true
                this.range = null
                this.summaryData = null
                this.$message.success(this.$t('chat.summary_success'), 6)
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.loading = false
            }
        },
        checkSummaryActive() {
            if(this.$route.query?.ai_summary) {
                this.visible = true
                const query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.ai_summary
                this.$router.replace({ query })
            }
        }
    },
    mounted() {
        this.loadPendingAnimation()
        this.checkSummaryActive()
        eventBus.$on('chat_ai_summary_show', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('chat_ai_summary_show')
    }
}
</script>

<style lang="scss" scoped>
.range_input{
    &::v-deep{
        .ant-calendar-range-picker-input{
            text-transform: capitalize!important;
            &::placeholder{
                &::first-letter{
                    text-transform: uppercase!important;
                }
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

.summary_text__anim {
    width: 22px;
    height: 22px;
    object-fit: contain;
    flex: 0 0 22px;
}
</style>
