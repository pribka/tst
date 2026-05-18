<template>
    <div ref="noty" :class="`noty_${item.id}`" class="noty_link" v-html="processedMessage" />
</template>

<script>
import { linkifyNotificationHtml, openNotificationLink } from '../utils'
export default {
    name: "NotificationMessage",
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            nLinkListeners: [],
            blockquoteListeners: []
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        processedMessage() {
            return this.linkifyHtml(this.item?.message || '')
        }
    },
    methods: {
        getLinkElement(target) {
            if (!target || typeof target.closest !== 'function') return target

            return target.closest('.n_link') || target.closest('a')
        },
        getLinkDescriptor(target) {
            const link = this.getLinkElement(target)

            if (!link) return null

            if (link.classList && link.classList.contains('n_link')) {
                return {
                    kind: 'notification_link',
                    name: link.getAttribute('data-link-type'),
                    query: link.getAttribute('data-link-query'),
                    toOpen: link.getAttribute('data-link-open')
                }
            }

            if (link.tagName === 'A') {
                return {
                    kind: 'anchor',
                    href: link.getAttribute('href'),
                    target: link.getAttribute('target') || '_blank',
                    rel: link.getAttribute('rel') || 'noopener noreferrer'
                }
            }

            return null
        },
        async open(item) {
            if (item?.preventDefault) item.preventDefault()
            if (item?.stopPropagation) item.stopPropagation()

            const link = this.getLinkDescriptor(item?.target)
            if (!link) return

            this.$emit('read')
            await openNotificationLink(link, {
                router: this.$router,
                route: this.$route,
                messageText: this.$refs?.noty?.textContent || ''
            })
        },
        async openBlockquote(item) {
            const link = this.getBlockquoteLink(item?.target)
            if (!link) return

            await this.open({ target: link })
        },
        getBlockquoteLink(blockquote) {
            if (!blockquote) return null

            let prev = blockquote.previousElementSibling
            while (prev) {
                if (prev.classList && prev.classList.contains('n_link')) return prev
                const nested = prev.querySelector && prev.querySelector('.n_link')
                if (nested) return nested
                prev = prev.previousElementSibling
            }

            return this.$refs?.noty?.querySelector('.n_link')
        },
        setListener(){
            this.$nextTick(()=>{
                try{ 
                    this.removeListeners()
                    const links = document.querySelectorAll(`.noty_${this.item.id} .n_link, .noty_${this.item.id} a`)
                    if(links?.length){
                        links.forEach(el=>{
                            if (el.matches('a') && el.closest('.n_link')) return
                            const handler = item => this.open(item)
                            el.addEventListener('click', handler)
                            this.nLinkListeners.push({ el, handler })
                        })
                    }
                    const blockquotes = document.querySelectorAll(`.noty_${this.item.id} blockquote`)
                    if(blockquotes?.length){
                        blockquotes.forEach(el=>{
                            const handler = item => this.openBlockquote(item)
                            el.addEventListener('click', handler)
                            this.blockquoteListeners.push({ el, handler })
                        })
                    }
                }
                catch(e){
                    console.error("Ошибка открытия. Проверьте backend!" + e)
                }
            })
        },
        removeListeners() {
            if (this.nLinkListeners && this.nLinkListeners.length) {
                this.nLinkListeners.forEach(({ el, handler }) => {
                    el.removeEventListener('click', handler)
                })
                this.nLinkListeners = []
            }
            if (this.blockquoteListeners && this.blockquoteListeners.length) {
                this.blockquoteListeners.forEach(({ el, handler }) => {
                    el.removeEventListener('click', handler)
                })
                this.blockquoteListeners = []
            }
        },
        linkifyHtml(html) {
            return linkifyNotificationHtml(this.fillEmptyBlockquotes(html))
        },
        fillEmptyBlockquotes(html) {
            if (typeof document === 'undefined') return html || ''

            const container = document.createElement('div')
            container.innerHTML = html || ''
            const blockquotes = container.querySelectorAll('blockquote')

            blockquotes.forEach(item => {
                if ((item.textContent || '').trim()) return
                item.textContent = this.$t('noty.fileOrImage')
            })

            return container.innerHTML
        }
    },
    updated(){
        this.setListener()
    },
    mounted(){
        this.setListener()
    },
    beforeDestroy() {
        this.removeListeners()
    }
}
</script>

<style lang="scss">
.noty_link{
    word-break: break-word;
  .n_link{
    color: var(--primaryColor);
  }
  blockquote{
    position: relative;
    display: table;
    width: fit-content;
    max-width: min(520px, 100%);
    margin: 8px 0 0;
    padding: 10px 14px!important;
    border-left: 0!important;
    border-radius: 10px;
    background: #fff0d8;
    color: #4c4f58;
    line-height: 1.35;
    white-space: pre-wrap;
    cursor: pointer;
    &::before{
      content: '';
      position: absolute;
      top: -8px;
      left: 12px;
      width: 0;
      height: 0;
      border-left: 8px solid transparent;
      border-right: 8px solid transparent;
      border-bottom: 8px solid #fff0d8;
    }
  }
  cursor: pointer;
}
</style>

<style scoped>
.ellipsis {
    text-overflow: ellipsis;
}
</style>
