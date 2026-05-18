<template>
    <div 
        v-if="news.attachments && news.attachments.length"
        :ref="`files_${news.id}`"
        class="news_files">
        <div class="mb-2 text-sm font-semibold">{{ $t('wgr.at_files') }}</div>
        <div class="file_list grid grid-cols-6">
            <div 
                v-for="file in news.attachments" 
                :key="file.id" 
                class="file_item">
                <a-dropdown 
                    :trigger="['contextmenu']" 
                    :getPopupContainer="getPopupContainer">
                    <div class="file_cont" v-if="file.is_image">
                        <a
                            :href="file.path"
                            class="file_link lht_ct">
                            <div class="pick_img">
                                <div class="img_wrap">
                                    <img 
                                        :src="file.path" 
                                        :alt="file.name ? file.name : file.path" />
                                </div>
                            </div>
                            <div class="file_name">
                                {{file.name ? file.name : file.path}}<template v-if="file.extension">.{{ file.extension }}</template>
                            </div>
                        </a>
                    </div>
                    <div class="file_cont" v-else>
                        <a
                            :href="file.path"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="file_link">
                            <div class="icon">
                                <img :src="fileIcon(file)" />
                            </div>
                            <div class="file_name">
                                {{file.name ? file.name : file.path}}<template v-if="file.extension">.{{ file.extension }}</template>
                            </div>
                        </a>
                    </div>
                    <a-menu slot="overlay">
                        <a-menu-item 
                            key="file_info"
                            class="file_info_drop"
                            @click="fileOpen(file)">
                            <div class="ico">
                                <img :src="fileIcon(file)" />
                            </div>
                            <div class="text_info">
                                <div class="filename">{{file.name ? file.name : file.path}}<template v-if="file.extension">.{{ file.extension }}</template></div>
                                <div class="filesize">
                                    {{ fileSize(file) }}
                                </div>
                            </div>
                        </a-menu-item>
                        <a-menu-item 
                            key="share" 
                            @click="share(file)">
                            {{ $t('wgr.share') }}
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
            </div>
        </div>
    </div>
</template>

<script>
import { filesFormat, conv_size } from '@/utils'
export default {
    props: {
        news: {
            type: Object,
            required: true
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    created () {
        this.initLightbox()
    },
    methods: {
        share(file) {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'files',
                shareId: file.id,
                object: file,
                bodySelector: '.news_detail',
                shareUrl: file.path,
                shareTitle: `Файл - ${file.name}`
            })
        },
        getPopupContainer() {
            return document.querySelector('.news_detail')
        },
        fileSize(file) {
            return conv_size(file.size)
        },
        fileOpen(file) {
            window.open(file.path, '_blank')
        },
        initLightbox() {
            this.$nextTick(() => {
                if(this.news.attachments?.length) {
                    const lightboxWrap = this.$refs[`files_${this.news.id}`],
                        lightbox = lightboxWrap.querySelectorAll('.lht_ct')

                    if(lightbox?.length) {
                        lightGallery(lightboxWrap, {
                            selector: ".lht_ct",
                            thumbnail: true,
                            rotateLeft: true,
                            rotateRight: true,
                            flipHorizontal: false,
                            flipVertical: false,
                            fullScreen: true,
                            animateThumb: true,
                            showThumbByDefault: true,
                            download: true,
                            speed: 300
                        })
                    }
                }
            })
        },
        fileIcon(file) {
            const find = filesFormat.find(f => f === file.extension)
            if(find)
                return require(`@/assets/images/files/${file.extension}.svg`)
            else
                return require(`@/assets/images/files/file.svg`)
        }
    }
}
</script>

<style lang="scss">
.file_info_drop{
    display: flex;
    align-items: center;
    .ico{
        margin-right: 10px;
        img{
            max-width: 20px;
        }
    }
    .text_info{
        max-width: 160px;
        .filename{
            word-break: break-word;
            white-space: normal;
            margin-bottom: 5px;
        }
    }
}
.doc_modal{
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
</style>

<style lang="scss" scoped>
.news_files{
    margin-top: 30px;
    h4{
        font-weight: 600;
        margin-bottom: 15px;
        font-size: 18px;
    }
}
.file_list{
    gap: 5px;
    .file_cont{
        padding: 20px;
        border: 1px solid var(--borderColor);
        cursor: pointer;
        position: relative;
        overflow: hidden;
        &:hover{
            border-color: var(--blue);
        }
        .file_link{
            display: block;
            text-align: center;
            color: var(--text);
            .pick_img{
                margin-bottom: 15px;
                .img_wrap{
                    width: 45px;
                    height: 45px;
                    margin: 0 auto;
                    background: #fafafa;
                    border-radius: 5px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    img{
                        width: 100%;
                        object-fit: cover;
                        vertical-align: middle;
                        -o-object-fit: cover;
                    }
                }
            }
            .icon{
                margin-bottom: 15px;
                min-height: 45px;
                img{
                    max-width: 45px;
                    margin: 0 auto;
                }
            }
            .file_name{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        }
    }
}
</style>
