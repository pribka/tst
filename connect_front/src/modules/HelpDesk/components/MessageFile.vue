<template>
    <div
        class="comment_file"
        :title="file.name"
        :ref="wrapRef">
        <a
            v-if="isImage"
            class="lht_l"
            :href="file.path"
            @click.prevent>
            <img
                class="lazyload"
                :data-src="file.path"
                :alt="file.name" />
        </a>
        <template v-else>
            <a
                download
                class="truncate doc_file"
                target="_blank"
                :href="file.path">
                <a-tooltip :title="fileName">
                    <img
                        :src="fileIcon"
                        class="file_icon" />
                    <span class="truncate">
                        {{ fileName }}
                    </span>
                </a-tooltip>
            </a>
        </template>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'

export default {
    props: {
        file: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            lg: null,
            lgWrapInst: null,
            moWrap: null,
            lazyHandler: null,
            initTimer: null
        }
    },
    computed: {
        wrapRef() {
            return `comment_file_${this._uid}`
        },
        fileIcon() {
            const find = filesFormat.find(f => f === this.file.extension)
            if (find)
                return require(`@/assets/images/files/${this.file.extension}.svg`)
            else
                return require(`@/assets/images/files/file.svg`)
        },
        fileName() {
            if (this.file.name) {
                return `${this.file.name}.${this.file.extension}`
            } else {
                return this.$t('file')
            }
        },
        office() {
            switch (this.file.extension) {
            case 'doc':
                return 'docx'
            case 'docx':
                return 'docx'
            case 'xlsx':
                return 'xlsx'
            case 'xls':
                return 'xlsx'
            case 'pptx':
                return 'pptx'
            case 'ppt':
                return 'pptx'
            default:
                return ''
            }
        },
        isDoc() {
            switch (this.file.extension) {
            case 'doc':
                return true
            case 'docx':
                return true
            case 'xlsx':
                return true
            case 'xls':
                return true
            case 'pptx':
                return true
            case 'ppt':
                return true
            default:
                return false
            }
        },
        isImage() {
            return this.file.is_image
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
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
        destroyLG() {
            const inst = this.lgWrapInst
            if (inst && inst.destroy) {
                try { inst.destroy(true) } catch (e) {}
            }
            this.lgWrapInst = null
        },
        async ensureLG() {
            if (!this.isImage) {
                this.destroyLG()
                return
            }

            await this.$nextTick()

            const wrap = this.$refs[this.wrapRef]
            if (!wrap) return

            const items = wrap.querySelectorAll('.lht_l')
            if (!items || !items.length) return

            if (this.initTimer) {
                clearTimeout(this.initTimer)
                this.initTimer = null
            }

            this.initTimer = setTimeout(async () => {
                const LG = await this.getLG()
                this.destroyLG()

                this.lgWrapInst = LG(wrap, {
                    selector: '.lht_l',
                    thumbnail: true,
                    rotateLeft: true,
                    rotateRight: true,
                    fullScreen: this.isMobile ? false : true,
                    animateThumb: true,
                    showThumbByDefault: this.isMobile ? false : true,
                    download: this.isMobile ? false : true,
                    flipHorizontal: false,
                    flipVertical: false,
                    zoom: true,
                    speed: 300,
                    enableZoomAfter: 300
                })
            }, 50)
        },
        attachObservers() {
            const wrap = this.$refs[this.wrapRef]
            if (wrap && !this.moWrap) {
                this.moWrap = new MutationObserver(() => this.ensureLG())
                this.moWrap.observe(wrap, { childList: true, subtree: true })
            }

            if (!this.lazyHandler) {
                this.lazyHandler = e => {
                    const t = e && e.target
                    if (!t) return
                    const wrap2 = this.$refs[this.wrapRef]
                    if (wrap2 && wrap2.contains(t)) this.ensureLG()
                }
                document.addEventListener('lazyloaded', this.lazyHandler, true)
            }
        },
        detachObservers() {
            if (this.moWrap) {
                this.moWrap.disconnect()
                this.moWrap = null
            }
            if (this.lazyHandler) {
                document.removeEventListener('lazyloaded', this.lazyHandler, true)
                this.lazyHandler = null
            }
            if (this.initTimer) {
                clearTimeout(this.initTimer)
                this.initTimer = null
            }
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.ensureLG()
            this.attachObservers()
        })
    },
    watch: {
        isImage() {
            this.ensureLG()
        },
        'file.path'() {
            this.ensureLG()
        }
    },
    updated() {
        this.ensureLG()
    },
    beforeDestroy() {
        this.detachObservers()
        this.destroyLG()
    }
}
</script>

<style lang="scss" scoped>
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
</style>