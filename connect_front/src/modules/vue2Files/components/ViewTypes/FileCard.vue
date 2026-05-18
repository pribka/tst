<template>
    <div
        class="file_card_wrap w-full h-full"
        :class="[isCutted && 'cutted_file', isMobile && 'mobile']">
        <a-checkbox
            :checked="isChecked"
            class="file_select"
            @change="changeSelectFile" />

        <div class="file_card_actions">
            <a-button
                v-if="!isMobile"
                type="ui"
                ghost
                shape="circle"
                class="file_card_actions__button"
                @click.stop="openFileDetail">
                <i class="fi fi-rr-info"></i>
            </a-button>

            <a-button
                type="ui"
                ghost
                shape="circle"
                class="file_card_actions__button"
                @click.stop="openMenu">
                <i class="fi fi-rr-menu-dots-vertical"></i>
            </a-button>
        </div>

        <div
            :ref="`file_${file.id}`"
            class="file_card w-full h-full"
            @click="handleOpen">
            <div class="file_image_wrapper">
                <img
                    :data-src="file.is_image ? file.path : fileIcon"
                    alt=""
                    class="file_icon lazyload"
                    :class="[
                        file.is_image && 'file_image',
                        isImageLoaded && 'file_loaded_image'
                    ]"
                    @load="onImageLoaded">
            </div>

            <div class="file_name font-light text-center truncate">
                {{ file.name }}
            </div>

            <div
                v-if="!isFolder && file.attachment_date"
                class="attachment_date text-center truncate">
                <a-icon type="cloud-upload" class="truncate" />
                {{ attachmentDate }}
            </div>

            <div
                v-if="file.is_dynamic"
                class="dynamic_icon_wrap">
                <i class="fi fi-rr-engine-warning"></i>
            </div>
        </div>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'
import fileSourcesProps from '../../mixins/fileSourcesProps'

export default {
    name: 'FileCard',
    mixins: [fileSourcesProps],
    props: {
        file: {
            type: Object,
            required: true
        },
        setCurrentSource: {
            type: Function,
            default: () => {}
        },
        selectedFiles: {
            type: Object,
            default: () => {}
        },
        cuttedFiles: {
            type: Object,
            default: () => {}
        },
        fileOpenSwitch: {
            type: Function,
            default: () => {}
        },
        openMenu: {
            type: Function,
            default: () => {}
        },
        openFileDetail: {
            type: Function,
            default: () => {}
        },
        oneUpload: {
            type: Boolean,
            default: false
        },
        mobileApp: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            isImageLoaded: false
        }
    },
    computed: {
        attachmentDate() {
            return this.$moment(this.file.attachment_date).format('DD.MM.YYYY HH:mm')
        },
        isFolder() {
            return this.file.obj_type === 'folder'
        },
        fileIcon() {
            if(this.isFolder)
                return require('@/assets/images/files/folder.svg')

            const extension = filesFormat.find(format => format === this.file.extension)
            if(extension)
                return require(`@/assets/images/files/${extension}.svg`)

            return require('@/assets/images/files/file.svg')
        },
        isChecked() {
            return this.selectedFiles.list.includes(this.file)
        },
        isCutted() {
            return this.cuttedFiles?.list?.includes(this.file)
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        onImageLoaded() {
            this.isImageLoaded = true
        },
        handleOpen() {
            if(this.isFolder) {
                this.setCurrentSource(this.file.id)
                return
            }

            this.fileOpenSwitch(this.file)
        },
        changeSelectFile(event) {
            this.selectedFiles.from = this.sourceId
            const isChecked = event.target.checked

            if(isChecked) {
                this.selectedFiles.list.push(this.file)
            } else if(this.selectedFiles.list.includes(this.file)) {
                const fileIndex = this.selectedFiles.list.findIndex(file => file.id === this.file.id)
                this.selectedFiles.list.splice(fileIndex, 1)

                if(this.cuttedFiles?.list?.includes(this.file)) {
                    const cuttedFileIndex = this.cuttedFiles.list.findIndex(file => file.id === this.file.id)
                    this.cuttedFiles.list.splice(cuttedFileIndex, 1)
                }
            }
        }
    },
}
</script>

<style scoped lang="scss">
.attachment_date {
    opacity: 0.6;
    font-size: 0.8rem;
}

.cutted_file {
    opacity: 0.5;
}

.file_card_wrap {
    position: relative;
    width: 170px;
    height: 200px;

    .file_select {
        position: absolute;
        top: 8px;
        left: 8px;
        z-index: 2;
    }

    &:hover {
        .file_card_actions {
            opacity: 1;
            pointer-events: auto;
        }
    }

    &.mobile {
        .file_card_actions {
            opacity: 1;
            pointer-events: auto;
        }
    }
}

.file_card_actions {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 2;
    display: flex;
    gap: 6px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
}

.file_card_actions__button {
    color: #607087;
    backdrop-filter: blur(10px);
}

.file_card {
    border-radius: var(--borderRadius);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
        background-color: #f0f3f7;
    }

    .file_image_wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 150px;
        padding: 0 15px;

        .file_icon {
            width: 100%;
            max-height: 100px;
            object-fit: contain;
        }

        .file_image {
            border: 1px solid var(--borderColor);
            border-radius: 4px;
            opacity: 0;
        }

        .file_loaded_image {
            opacity: 1;
        }
    }

    .file_name {
        margin-top: 10px;
        padding: 0 15px;
    }

    .dynamic_icon_wrap {
        position: absolute;
        top: 44px;
        right: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        line-height: 1;
    }
}
</style>

<style lang="scss">
.file_card_wrap {
    .file_select {
        .ant-checkbox:hover::after {
            border-radius: 100%;
        }

        .ant-checkbox-inner::after {
            position: absolute;
            top: 50%;
            left: 50%;
            transform:
                translate(-50%, -50%)
                rotate(45deg);
        }

        .ant-checkbox-inner {
            width: 24px;
            height: 24px;
            border-radius: 100%;
        }
    }
}
</style>
