<template>
    <div 
        v-if="news.attachments && news.attachments.length"
        :ref="`files_${news.id}`"
        class="news_files">
        <div class="mb-2 text-sm font-semibold">{{ $t('project.at_files') }}</div>
        <div class="file_list grid grid-cols-6">
            <div 
                v-for="file in news.attachments" 
                :key="file.id" 
                class="file_item">
                <div class="file_cont">
                    <a-dropdown 
                        :trigger="['click']" 
                        :getPopupContainer="getPopupContainer">
                        <a-button
                            type="ui_ghost"
                            flaticon
                            shape="circle"
                            icon="fi-rr-menu-dots-vertical"
                            class="file_actions_btn"
                            @click.stop></a-button>
                        <a-menu slot="overlay">
                            <a-menu-item
                                v-if="isPreviewableFile(file)"
                                key="open"
                                class="flex items-center"
                                @click="openFilePreview(file)">
                                <i class="fi fi-rr-eye mr-2" />
                                {{ $t('open') }}
                            </a-menu-item>
                            <a-menu-item 
                                key="download"
                                class="flex items-center"
                                @click="downloadFile(file)">
                                <i class="fi fi-rr-download mr-2" />
                                Скачать
                            </a-menu-item>
                        </a-menu>
                    </a-dropdown>
                    
                    <div v-if="file.is_image">
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
                    <div
                        v-else
                        class="file_link"
                        @click.stop>
                        <div class="icon">
                            <img :src="fileIcon(file)" />
                        </div>
                        <div class="file_name">
                            {{file.name ? file.name : file.path}}<template v-if="file.extension">.{{ file.extension }}</template>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'
import { isOnlyofficePreviewable, openOnlyofficePreview } from '@/utils/onlyoffice'
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
        getPopupContainer(trigger) {
            return trigger?.parentNode || document.body
        },
        isPreviewableFile(file) {
            return !!file?.id && !file?.is_image && isOnlyofficePreviewable(file)
        },
        openFilePreview(file) {
            if (!this.isPreviewableFile(file)) return

            openOnlyofficePreview(this.$store, {
                scope: 'file',
                file_id: file.id
            })
        },
        downloadFile(file) {
            const link = document.createElement('a')
            link.href = file.path
            link.target = '_blank'
            link.rel = 'noopener noreferrer'
            link.download = `${file.name ? file.name : 'file'}${file.extension ? `.${file.extension}` : ''}`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
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
    grid-template-columns: repeat(6, minmax(0, 1fr));
    .file_cont{
        padding: 20px;
        border: 1px solid var(--borderColor);
        cursor: pointer;
        position: relative;
        overflow: hidden;
        &:hover{
            border-color: var(--blue);
        }
        .file_actions_btn{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 2;
        }
        .file_link{
            display: block;
            text-align: center;
            color: var(--text);
            padding-top: 18px;
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

@media (max-width: 767.98px) {
    .file_list{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .file_list .file_cont{
        padding: 16px 12px;
    }
}
</style>
