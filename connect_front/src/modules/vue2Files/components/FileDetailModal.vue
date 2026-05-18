<template>
    <a-modal
        class="file_detail_modal"
        :visible="visible"
        :footer="null"
        :closable="true"
        :getContainer="getContainer"
        :width="isMobile ? 'calc(100vw - 24px)' : 560"
        @cancel="$emit('close')">
        <div class="file_detail_modal__body">
            <div class="file_detail_modal__header">
                <div class="file_detail_modal__title_wrap">
                    <div class="file_detail_modal__title_icon">
                        <i class="fi fi-rr-info"></i>
                    </div>
                    <div class="file_detail_modal__title truncate">
                        {{ file.name }}
                    </div>
                </div>
            </div>

            <div class="file_detail_modal__preview">
                <img
                    v-if="file.is_image"
                    :src="file.path"
                    :alt="file.name"
                    class="file_detail_modal__preview_image">
                <div v-else class="file_detail_modal__preview_fallback">
                    <img
                        :src="fileIcon"
                        :alt="file.name"
                        class="file_detail_modal__preview_icon">
                    <div class="file_detail_modal__preview_type">
                        {{ previewTypeLabel }}
                    </div>
                </div>
            </div>

            <div
                v-if="file.description"
                class="file_detail_modal__description">
                {{ file.description }}
            </div>

            <div class="file_detail_modal__meta">
                <div class="file_detail_modal__meta_item">
                    <div class="file_detail_modal__meta_label">
                        {{ $t('Size') }}
                    </div>
                    <div class="file_detail_modal__meta_value">
                        {{ formattedSize }}
                    </div>
                </div>
                <div class="file_detail_modal__meta_item">
                    <div class="file_detail_modal__meta_label">
                        {{ $t('files.file_type') }}
                    </div>
                    <div class="file_detail_modal__meta_value">
                        {{ normalizedFileType }}
                    </div>
                </div>
                <div class="file_detail_modal__meta_item">
                    <div class="file_detail_modal__meta_label">
                        {{ $t('Modified') }}
                    </div>
                    <div class="file_detail_modal__meta_value">
                        {{ formattedDate }}
                    </div>
                </div>
                <div class="file_detail_modal__meta_item">
                    <div class="file_detail_modal__meta_label">
                        {{ $t('Resolution') }}
                    </div>
                    <div class="file_detail_modal__meta_value">
                        {{ resolutionLabel }}
                    </div>
                </div>
            </div>

            <div class="file_detail_modal__related">
                <div class="file_detail_modal__related_label">
                    {{ $t('Related objects') }}
                </div>

                <div
                    v-if="relatedLoading"
                    class="file_detail_modal__related_loading">
                    <a-spin />
                </div>

                <div
                    v-else-if="relatedItems.length"
                    class="file_detail_modal__related_list">
                    <button
                        v-for="relatedItem in relatedItems"
                        :key="relatedItem.key"
                        type="button"
                        class="file_detail_modal__related_chip"
                        @click="$emit('related-click', relatedItem)">
                        <i class="fi fi-rr-arrow-up-right-from-square"></i>
                        <span>{{ relatedItem.label }}</span>
                    </button>
                </div>

                <div
                    v-else
                    class="file_detail_modal__related_empty">
                    {{ $t('None') }}
                </div>
            </div>

            <div class="file_detail_modal__footer">
                <a-button
                    type="primary"
                    class="file_detail_modal__download"
                    @click="$emit('download')">
                    <i class="fi fi-rr-download mr-2"></i>
                    <span>{{ downloadLabel }}</span>
                </a-button>

                <a-button
                    v-if="showShare"
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_detail_modal__icon_button"
                    @click="$emit('share')">
                    <i class="fi fi-rr-share"></i>
                </a-button>

                <a-button
                    v-if="showDelete"
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_detail_modal__icon_button file_detail_modal__icon_button--danger"
                    @click="$emit('remove')">
                    <i class="fi fi-rr-trash"></i>
                </a-button>
            </div>
        </div>
    </a-modal>
</template>

<script>
import { filesFormat } from '@/utils'

export default {
    name: 'FileDetailModal',
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        file: {
            type: Object,
            required: true
        },
        isFolder: {
            type: Boolean,
            default: false
        },
        relatedItems: {
            type: Array,
            default: () => []
        },
        relatedLoading: {
            type: Boolean,
            default: false
        },
        showShare: {
            type: Boolean,
            default: false
        },
        showDelete: {
            type: Boolean,
            default: false
        },
        getContainer: {
            type: Function,
            default: () => document.body
        }
    },
    data() {
        return {
            imageMeta: {
                width: null,
                height: null
            }
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        fileIcon() {
            if(this.isFolder)
                return require('@/assets/images/files/folder.svg')

            const extension = filesFormat.find(format => format === this.file.extension)
            if(extension)
                return require(`@/assets/images/files/${extension}.svg`)

            return require('@/assets/images/files/file.svg')
        },
        previewTypeLabel() {
            if(this.isFolder)
                return this.$t('Folder')

            return (this.file.extension || this.$t('files.file')).toUpperCase()
        },
        formattedSize() {
            if(this.isFolder)
                return '--'
            if(!this.file.size)
                return `0 ${this.$t('KB')}`

            const megabytes = this.file.size / 1024 / 1024
            if(megabytes >= 1)
                return `${megabytes.toFixed(1)} ${this.$t('MB')}`

            return `${(this.file.size / 1024).toFixed(1)} ${this.$t('KB')}`
        },
        normalizedFileType() {
            if(this.isFolder)
                return this.$t('Folder').toUpperCase()

            return (this.file.file_type?.name || this.file.extension || '--').toUpperCase()
        },
        formattedDate() {
            const rawDate = this.file.attachment_date || this.file.updated_at || this.file.created_at
            if(!rawDate)
                return '--'

            return this.$moment(rawDate).format('DD.MM.YYYY')
        },
        resolutionLabel() {
            if(!this.file.is_image)
                return '--'
            if(!this.imageMeta.width || !this.imageMeta.height)
                return '--'

            return `${this.imageMeta.width}x${this.imageMeta.height}`
        },
        downloadLabel() {
            return this.isFolder
                ? this.$t('files.download_as_zip')
                : this.$t('files.download')
        }
    },
    watch: {
        visible: {
            immediate: true,
            handler(isVisible) {
                if(isVisible)
                    this.loadImageMeta()
            }
        },
        file: {
            deep: true,
            handler() {
                this.imageMeta = {
                    width: null,
                    height: null
                }
                if(this.visible)
                    this.loadImageMeta()
            }
        }
    },
    methods: {
        loadImageMeta() {
            if(!this.file.is_image || !this.file.path)
                return

            const image = new Image()
            image.onload = () => {
                this.imageMeta = {
                    width: image.naturalWidth,
                    height: image.naturalHeight
                }
            }
            image.src = this.file.path
        }
    }
}
</script>

<style lang="scss">
.file_detail_modal {
    .ant-modal-content {
        overflow: hidden;
        border-radius: 24px;
    }

    .ant-modal-body {
        padding: 0;
    }
}
</style>

<style scoped lang="scss">
.file_detail_modal__body {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 24px;
}

.file_detail_modal__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.file_detail_modal__title_wrap {
    display: flex;
    align-items: center;
    min-width: 0;
    gap: 12px;
}

.file_detail_modal__title_icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 12px;
    background: rgba(46, 107, 255, 0.1);
    color: #2e6bff;
    font-size: 16px;
}

.file_detail_modal__title {
    font-size: 30px;
    font-weight: 600;
    line-height: 1.2;
    color: #222b45;
}

.file_detail_modal__preview {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 224px;
    padding: 18px;
    border: 1px solid #edf1f7;
    border-radius: 20px;
    background: #f9fbff;
}

.file_detail_modal__preview_image {
    max-width: 100%;
    max-height: 320px;
    object-fit: contain;
    border-radius: 14px;
}

.file_detail_modal__preview_fallback {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
}

.file_detail_modal__preview_icon {
    width: 96px;
    height: 96px;
    object-fit: contain;
}

.file_detail_modal__preview_type {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #8d99ae;
}

.file_detail_modal__description {
    padding: 16px 18px;
    border-radius: 16px;
    background: #f5f7fb;
    color: #4f5d75;
    line-height: 1.5;
}

.file_detail_modal__meta {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px 24px;
}

.file_detail_modal__meta_label {
    margin-bottom: 6px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #a0aec0;
}

.file_detail_modal__meta_value {
    font-size: 22px;
    font-weight: 600;
    line-height: 1.2;
    color: #2d3748;
}

.file_detail_modal__related {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.file_detail_modal__related_label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #a0aec0;
}

.file_detail_modal__related_loading,
.file_detail_modal__related_empty {
    color: #718096;
}

.file_detail_modal__related_list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.file_detail_modal__related_chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border: 1px solid #d7e3ff;
    border-radius: 999px;
    background: #eef4ff;
    color: #2e6bff;
    transition: background-color 0.2s ease, border-color 0.2s ease;
    cursor: pointer;
}

.file_detail_modal__related_chip:hover {
    background: #e3ecff;
    border-color: #b7ccff;
}

.file_detail_modal__footer {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
    padding-top: 20px;
    border-top: 1px solid #edf1f7;
}

.file_detail_modal__download {
    flex: 1 1 auto;
    height: 48px;
    border-radius: 14px;
    font-weight: 600;
}

.file_detail_modal__icon_button {
    flex: 0 0 auto;
    width: 46px;
    height: 46px;
    border-radius: 14px;
    color: #607087;
}

.file_detail_modal__icon_button--danger {
    color: #f04438;
}

@media (max-width: 767px) {
    .file_detail_modal__body {
        gap: 18px;
        padding: 18px;
    }

    .file_detail_modal__title {
        font-size: 20px;
    }

    .file_detail_modal__meta {
        gap: 14px;
    }

    .file_detail_modal__meta_value {
        font-size: 18px;
    }

    .file_detail_modal__footer {
        gap: 10px;
    }
}
</style>
