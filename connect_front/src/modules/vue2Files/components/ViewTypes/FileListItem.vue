<template>
    <div
        class="file_list_item"
        :class="[isCutted && 'cutted_file', isMobile && 'mobile', isChecked && 'selected']">
        <div
            class="file_select_wrap"
            @click.stop>
            <a-checkbox
                :checked="isChecked"
                class="file_select"
                @change="changeSelectFile" />
        </div>

        <div
            class="file_list_item__main cursor-pointer"
            @click="handleOpen">
            <div class="file_icon_wrap">
                <img
                    class="file_icon lazyload"
                    :class="file.is_image && 'file_image'"
                    :data-src="file.is_image ? file.path : fileIcon"
                    alt="">
                <span
                    v-if="file.is_dynamic"
                    class="dynamic_icon_wrap">
                    <i class="fi fi-rr-engine-warning"></i>
                </span>
            </div>

            <div class="file_list_item__content">
                <div class="file_name truncate">
                    {{ file.name }}
                </div>

                <div class="file_meta" :class="file.folder_path && 'has-path'">
                    <template v-if="!isFolder">
                        <span>{{ formattedSize }}</span>
                    </template>
                    <span v-if="displayDate">{{ displayDate }}</span>
                </div>

                <button
                    v-if="file.folder_path"
                    type="button"
                    class="file_path truncate"
                    @click.stop="setCurrentSource(file.folder)">
                    {{ file.folder_path }}
                </button>
            </div>
        </div>

        <div
            class="file_hover_actions"
            @click.stop>
            <a-tooltip
                v-if="!isMobile"
                :title="$t('files.info')">
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_hover_actions__button"
                    @click="openFileDetail">
                    <i class="fi fi-rr-info"></i>
                </a-button>
            </a-tooltip>

            <a-tooltip
                v-if="!isMobile"
                :title="downloadTooltip">
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_hover_actions__button"
                    @click="downloadCurrentFile">
                    <i class="fi fi-rr-download"></i>
                </a-button>
            </a-tooltip>

            <a-tooltip
                v-if="canShowShare && !isMobile"
                :title="$t('files.share')">
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_hover_actions__button file_hover_actions__button--active"
                    @click="shareFile">
                    <i class="fi fi-rr-share"></i>
                </a-button>
            </a-tooltip>

            <a-tooltip
                v-if="canDelete && !isMobile"
                :title="$t('files.delete')">
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    class="file_hover_actions__button file_hover_actions__button--danger"
                    @click="confirmDelete">
                    <i class="fi fi-rr-trash"></i>
                </a-button>
            </a-tooltip>

            <a-button
                v-if="isMobile"
                type="ui"
                ghost
                shape="circle"
                class="file_hover_actions__button"
                @click="openMenu">
                <i class="fi fi-rr-menu-dots-vertical"></i>
            </a-button>
        </div>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'
import fileSourcesProps from '../../mixins/fileSourcesProps'

export default {
    name: 'FileListItem',
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
        downloadCurrentFile: {
            type: Function,
            default: () => {}
        },
        shareFile: {
            type: Function,
            default: () => {}
        },
        confirmDelete: {
            type: Function,
            default: () => {}
        },
        canShowShare: {
            type: Boolean,
            default: false
        },
        canDelete: {
            type: Boolean,
            default: false
        },
        mobileApp: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        displayDate() {
            const rawDate = this.file.attachment_date || this.file.updated_at || this.file.created_at
            if(!rawDate)
                return ''

            return this.$moment(rawDate).format('DD.MM.YYYY')
        },
        formattedSize() {
            if(!this.file.size)
                return `0 ${this.$t('KB')}`

            const megabytes = this.file.size / 1024 / 1024
            if(megabytes >= 1)
                return `${megabytes.toFixed(1)} ${this.$t('MB')}`

            return `${(this.file.size / 1024).toFixed(1)} ${this.$t('KB')}`
        },
        downloadTooltip() {
            return this.isFolder
                ? this.$t('files.download_as_zip')
                : this.$t('files.download')
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

                if(this.cuttedFiles.list && this.cuttedFiles.list.includes(this.file)) {
                    const cuttedFileIndex = this.cuttedFiles.list.findIndex(file => file.id === this.file.id)
                    this.cuttedFiles.list.splice(cuttedFileIndex, 1)
                }
            }
        }
    },
}
</script>

<style scoped lang="scss">
.cutted_file {
    opacity: 0.5;
}

.file_list_item {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 74px;
    padding: 10px 14px;
    border: 1px solid #edf1f7;
    border-radius: 8px;
    background: #fff;
    transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;

    &:hover {
        background: #f8fbff;
        border-color: #dbe6ff;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);

        .file_hover_actions {
            opacity: 1;
            pointer-events: auto;
        }
    }

    &.selected {
        border-color: rgba(46, 107, 255, 0.35);
        background: #f4f8ff;
    }

    &.mobile {
        min-height: 68px;
        padding: 10px 12px;
        gap: 8px;

        .file_hover_actions {
            opacity: 1;
            pointer-events: auto;
            gap: 0;
        }

        .file_hover_actions__button {
            width: 34px;
            height: 34px;
        }

        .file_list_item__content {
            margin-left: 10px;
        }
    }
}

.file_list_item__main {
    display: flex;
    align-items: center;
    flex: 1 1 auto;
    min-width: 0;
}

.file_list_item__content {
    min-width: 0;
    margin-left: 12px;
}

.file_name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #25324b;
}

.file_meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 10px;
    margin-top: 4px;
    font-size: 0.78rem;
    color: #8a94a6;

    span {
        position: relative;

        &:not(:last-child)::after {
            content: '';
            position: absolute;
            top: 50%;
            right: -6px;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background: currentColor;
            transform: translateY(-50%);
        }
    }

    &.has-path {
        margin-bottom: 4px;
    }
}

.file_path {
    padding: 0;
    margin-top: 2px;
    border: none;
    background: transparent;
    text-align: left;
    font-size: 0.72rem;
    color: #7b8794;
    cursor: pointer;
}

.file_icon_wrap {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 8px;
    background: #f6f8fc;
    flex-shrink: 0;

    .dynamic_icon_wrap {
        position: absolute;
        top: -4px;
        right: -2px;
        font-size: 1rem;
    }
}

.file_image {
    border: 1px solid #d9e2f1;
    border-radius: 8px;
}

.file_icon {
    width: 44px;
    height: 44px;
    object-fit: cover;
}

.file_select_wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    width: 24px;
}

.file_select::v-deep {
    .ant-checkbox-inner {
        width: 20px;
        height: 20px;
        border-width: 2px;
        border-radius: 50%;
        border-color: #d7deeb;
        background: #fff;
    }

    .ant-checkbox-checked .ant-checkbox-inner {
        border-color: #2e6bff;
        background: #2e6bff;
    }

    .ant-checkbox-inner::after {
        top: 48%;
        left: 24%;
    }
}

.file_hover_actions {
    display: flex;
    justify-content: flex-end;
    flex: 0 0 auto;
    gap: 6px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
}

.file_hover_actions__button {
    width: 34px;
    height: 34px;
    color: #607087;
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.file_hover_actions__button--active {
    color: #2e6bff;
}

.file_hover_actions__button--danger {
    color: #ff5d5d;
}
</style>
