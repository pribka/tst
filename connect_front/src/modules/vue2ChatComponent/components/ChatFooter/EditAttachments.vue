<!--EditAttachments.vue-->
<template>
    <div
        class="edit_files"
        :ref="wrapRef">
        <div class="edit_files__row">
            <div
                v-for="(item, index) in message.attachments"
                :key="item.id || index"
                class="edit_files__item">
                <div class="edit_files__remove" @click.stop="remove(item, index)">
                    <i class="fi fi-rr-trash" />
                </div>

                <a
                    v-if="item.is_image"
                    class="edit_files__img lht_l"
                    :href="path(item.path)">
                    <img
                        class="lazyload"
                        :data-src="path(item.path)"
                        :alt="item.name" />
                </a>

                <a
                    v-else
                    class="edit_files__doc"
                    target="_blank"
                    download
                    :href="path(item.path)">
                    <a-icon type="file" class="mr-2" />
                    <span class="truncate">{{ item.name || $t('file') }}</span>
                </a>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
    props: {
        message: {
            type: Object,
            required: true
        },
        activeChat: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        wrapRef() {
            return 'edit_files_wrap'
        }
    },
    data() {
        return {
            lg: null,
            lgWrapInst: null
        }
    },
    methods: {
        path(p) {
            if(this.config?.chat_setting?.fix_file_path) {
                if(p.includes('chat_attachments')) {
                    return p
                } else {
                    return p + encodeURIComponent(`&chat_uid=${this.message.chat_uid}&message_uid=${this.message.message_uid}&target=chat_attachments`)
                }
            } else {
                return p
            }
        },
        remove(item, index) {
            this.$store.commit('chat/REMOVE_CHAT_MESSAGE_ATTACHMENT', {
                id: this.activeChat.chat_uid,
                attachmentId: item?.id,
                index
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
        destroyLG() {
            const inst = this.lgWrapInst
            if (inst && inst.destroy) {
                try { inst.destroy(true) } catch(e) {}
                this.lgWrapInst = null
            }
        },
        async ensureLG() {
            await this.$nextTick()
            const wrap = this.$refs[this.wrapRef]
            if (!wrap) return

            const items = wrap.querySelectorAll('.lht_l')
            if (!items || !items.length) {
                this.destroyLG()
                return
            }

            const LG = await this.getLG()
            this.destroyLG()
            this.lgWrapInst = LG(wrap, {
                selector: '.lht_l',
                thumbnail: true,
                rotateLeft: true,
                rotateRight: true,
                fullScreen: true,
                animateThumb: true,
                showThumbByDefault: true,
                download: true,
                flipHorizontal: false,
                flipVertical: false,
                zoom: true,
                speed: 300,
                enableZoomAfter: 300
            })
        }
    },
    mounted() {
        this.ensureLG()
    },
    watch: {
        'message.attachments': {
            deep: true,
            handler() {
                this.ensureLG()
            }
        }
    },
    beforeDestroy() {
        this.destroyLG()
    }
}
</script>

<style lang="scss" scoped>
.edit_files{
    width: 100%;
}
.edit_files__row{
    display: flex;
    gap: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
}
.edit_files__item{
    position: relative;
    flex: 0 0 auto;
    width: 54px;
    height: 54px;
    border: 1px solid var(--border2);
    border-radius: 10px;
    overflow: hidden;
    background: var(--card);
}
.edit_files__remove{
    position: absolute;
    top: 1px;
    right: 1px;
    width: 18px;
    height: 18px;
    font-size: 13px;
    border-radius: 50%;
    background: rgba(0,0,0,0.55);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    cursor: pointer;
}
.edit_files__img{
    display: flex;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
}
.edit_files__img img{
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.05s ease-in-out;
}
.edit_files__img img.lazyloaded{
    opacity: 1;
}
.edit_files__doc{
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    padding: 6px;
    font-size: 11px;
    line-height: 1.2;
}
</style>