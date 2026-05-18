<template>
    <div ref="fileCreateWrap" class="file_create">
        <template v-if="oneUpload && !createFounder">
            <a-upload
                name="upload"
                multiple
                class="w-full upload_wfull"
                :showUploadList="false"
                :customRequest="uploadRequest"
                @change="hideDragField">
                <a-button
                    v-if="viewType === 'card'"
                    class="create_item_grid flex items-center justify-center w-full">
                    <div class="create_item_icon_grid mr-2">
                        <i class="fi fi-rr-plus"></i>
                    </div>
                    <span>{{ $t('Upload file') }}</span>
                </a-button>

                <a-button
                    v-else
                    class="create_item_list flex items-center justify-center w-full">
                    <div class="create_item_icon_list mr-2">
                        <i class="fi fi-rr-plus"></i>
                    </div>
                    <span>{{ $t('Upload from device') }}</span>
                </a-button>
            </a-upload>
        </template>

        <template v-else>
            <div class="flex justify-end items-center gap-2 flex-wrap">
                <template v-if="!isMyFiles && !oneUpload">
                    <a-button
                        v-if="useIconButton"
                        v-tippy
                        :content="$t('Attach file')"
                        class="file_create__action_button">
                        <FileAttach
                            :showAttached="false"
                            :attachmentFiles="attachmentFiles"
                            :zIndex="zIndex"
                            :attachingRootId="rootId"
                            :attachingSourceId="sourceId">
                            <template v-slot:openButton>
                                <div class="text-center flex items-center">
                                    <i class="fi fi-rr-clip" />
                                </div>
                            </template>
                        </FileAttach>
                    </a-button>

                    <a-button
                        v-else
                        class="file_create__action_button">
                        <FileAttach
                            :showAttached="false"
                            :attachmentFiles="attachmentFiles"
                            :zIndex="zIndex"
                            :attachingRootId="rootId"
                            :attachingSourceId="sourceId">
                            <template v-slot:openButton>
                                <div class="text-center flex items-center">
                                    <i class="fi fi-rr-clip"></i>
                                    <template v-if="md">
                                        <span class="ml-2">{{ $t('Attach file') }}</span>
                                    </template>
                                </div>
                            </template>
                        </FileAttach>
                    </a-button>
                </template>

                <template v-if="showDeviceUpload">
                    <a-upload
                        name="upload"
                        multiple
                        :showUploadList="false"
                        :customRequest="uploadRequest"
                        @change="hideDragField">
                        <a-button
                            v-if="useIconButton"
                            v-tippy
                            :content="$t('Upload from device')"
                            class="file_create__action_button">
                            <div class="text-center flex items-center">
                                <i class="fi fi-rr-file-upload" />
                            </div>
                        </a-button>

                        <a-button
                            v-else
                            class="file_create__action_button">
                            <div class="text-center flex items-center">
                                <i class="fi fi-rr-file-upload"></i>
                                <template v-if="md">
                                    <span class="ml-2">{{ $t('Upload from device') }}</span>
                                </template>
                            </div>
                        </a-button>
                    </a-upload>
                </template>

                <template v-if="(rootId || sourceId) && createFounder">
                    <a-button
                        v-if="useIconButton"
                        v-tippy
                        :content="$t('Create folder')"
                        key="createFolder_ico"
                        class="flex items-center"
                        @click="modalVisible.folder = true">
                        <i class="fi fi-rr-add-folder"></i>
                    </a-button>

                    <a-button
                        v-else
                        key="createFolder"
                        class="flex items-center"
                        @click="modalVisible.folder = true">
                        <i class="fi fi-rr-add-folder"></i>
                        <template v-if="md">
                            <span class="ml-2">{{ $t('Create folder') }}</span>
                        </template>
                    </a-button>
                </template>
            </div>
        </template>

        <a-modal
            v-model="modalVisible.folder"
            :title="$t('Create folder')"
            :cancelText="$t('Cancel')"
            :zIndex="zIndex"
            :getContainer="getCreateContainer"
            :okText="$t('Create')"
            @ok="confirmFolderUpload">
            <a-form-model
                :label="$t('folder_name')"
                prop="folder_name">
                <a-form-model-item>
                    <a-input
                        v-model="createFolderName"
                        :placeholder="$t('Folder name')" />
                </a-form-model-item>
                <a-form-model-item>
                    <a-textarea
                        v-model="createFolderDesc"
                        :placeholder="$t('Description')"
                        :rows="4" />
                </a-form-model-item>
            </a-form-model>
        </a-modal>

        <template v-if="fileDragCreate">
            <a-upload-dragger
                v-show="showDragField"
                name="upload"
                class="files_drag_field"
                :multiple="true"
                :showUploadList="false"
                :customRequest="uploadRequest"
                @change="hideDragField">
                <div class="text-center flex justify-center items-center">
                    <a-spin v-if="hasActiveUploads || fileLoading" />
                    <template v-else>
                        <a-icon type="file-add" :style="{ fontSize: '54px', color: '#0e4682' }" />
                        <span class="text-xl" :style="`color:#0e4682`">{{ $t('Drag files here') }}</span>
                    </template>
                </div>
            </a-upload-dragger>
        </template>

        <transition name="upload-queue">
            <div
                v-if="uploadQueueVisible"
                class="upload_queue"
                :class="uploadQueueCollapsed && 'collapsed'">
                <div class="upload_queue__header">
                    <div class="upload_queue__title">
                        {{ uploadQueueTitle }}
                    </div>

                    <div class="upload_queue__header_actions">
                        <button
                            type="button"
                            class="upload_queue__header_button"
                            @click="uploadQueueCollapsed = !uploadQueueCollapsed">
                            <i
                                class="fi fi-rr-angle-small-down"
                                :class="uploadQueueCollapsed && 'is-collapsed'"></i>
                        </button>

                        <button
                            type="button"
                            class="upload_queue__header_button"
                            @click="closeUploadQueue">
                            <i class="fi fi-rr-cross"></i>
                        </button>
                    </div>
                </div>

                <template v-if="!uploadQueueCollapsed">
                    <div class="upload_queue__status">
                        <span>{{ uploadQueueSubtitle }}</span>
                        <button
                            type="button"
                            class="upload_queue__status_action"
                            @click="hasActiveUploads ? cancelActiveUploads() : clearUploadQueue()">
                            {{ hasActiveUploads ? $t('Cancel') : $t('Clear') }}
                        </button>
                    </div>

                    <div class="upload_queue__list">
                        <div
                            v-for="uploadFile in uploadingFiles"
                            :key="uploadFile.uid"
                            class="upload_queue__item">
                            <div class="upload_queue__item_main">
                                <img
                                    :src="queueItemIcon(uploadFile)"
                                    :alt="uploadFile.name"
                                    class="upload_queue__item_icon">
                                <div class="upload_queue__item_name truncate">
                                    {{ uploadFile.name }}
                                </div>
                            </div>

                            <div class="upload_queue__item_state">
                                <div
                                    v-if="uploadFile.status === 'done'"
                                    class="upload_queue__badge upload_queue__badge--done">
                                    <i class="fi fi-rr-check"></i>
                                </div>

                                <div
                                    v-else-if="uploadFile.status === 'error'"
                                    class="upload_queue__badge upload_queue__badge--error">
                                    <i class="fi fi-rr-cross"></i>
                                </div>

                                <a-progress
                                    v-else
                                    type="circle"
                                    :width="24"
                                    :showInfo="false"
                                    :percent="uploadFile.percent || 0"
                                    :strokeWidth="14" />
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </transition>
    </div>
</template>

<script>
import axios from 'axios'
import { mapState, mapActions, mapMutations } from 'vuex'
import TokenService from '@/config/TokenService'
import fileSourcesProps from '../mixins/fileSourcesProps'
import FileAttach from './FileAttach.vue'
import { errorHandler, filesFormat } from '@/utils/index.js'

export default {
    name: 'FileCreate',
    mixins: [fileSourcesProps],
    components: {
        FileAttach
    },
    props: {
        viewType: {
            type: String,
            required: true
        },
        isMyFiles: {
            type: Boolean,
            default: false
        },
        oneUpload: {
            type: Boolean,
            default: false
        },
        createFounder: {
            type: Boolean,
            default: true
        },
        mobileApp: {
            type: Boolean,
            default: false
        },
        fileDragCreate: {
            type: Boolean,
            default: true
        },
        getCreateContainer: {
            type: Function,
            default: () => document.body
        },
        showDeviceUpload: {
            type: Boolean,
            default: true
        },
        attachmentFiles: {
            type: Array,
            default: () => []
        },
        useIconButton: {
            type: Boolean,
            default: false
        },
    },
    data() {
        return {
            modalVisible: {
                folder: false
            },
            createFolderName: '',
            createFolderDesc: '',
            form: {
                uploadingFiles: []
            },
            fileLoading: false,
            showDragField: false,
            includeHeader: {},
            uploadQueueCollapsed: false,
            uploadQueueHidden: false,
            dragOverHandler: null,
            dropHandler: null,
            dragLeaveHandler: null
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        isFolder() {
            const rootIds = ['trash', 'my_files', this.rootId]
            return !rootIds.includes(this.sourceId)
        },
        md() {
            return this.windowWidth >= 768
        },
        zIndex() {
            if(this.$route.query?.sprint)
                return 999999
            return 1000
        },
        uploadingFiles() {
            return this.form.uploadingFiles
        },
        uploadQueueVisible() {
            return !!this.uploadingFiles.length && !this.uploadQueueHidden
        },
        hasActiveUploads() {
            return this.uploadingFiles.some(file => file.status === 'uploading')
        },
        uploadQueueTitle() {
            return this.$t('Uploading files count', {count: this.uploadingFiles.length})
        },
        uploadQueueSubtitle() {
            if(this.hasActiveUploads)
                return this.$t('Upload started')

            if(this.uploadingFiles.some(file => file.status === 'error'))
                return this.$t('Upload finished with errors')

            return this.$t('Upload complete')
        }
    },
    created() {
        if(this.mobileApp)
            this.getHeaders()
    },
    mounted() {
        this.$nextTick(() => {
            this.dragOverHandler = event => this.dragOver(event)
            this.dropHandler = event => this.dropComplete(event)
            this.dragLeaveHandler = event => this.dragLeave(event)

            window.addEventListener('dragover', this.dragOverHandler)
            window.addEventListener('drop', this.dropHandler)
            window.addEventListener('dragleave', this.dragLeaveHandler)
        })
    },
    beforeDestroy() {
        if(this.dragOverHandler)
            window.removeEventListener('dragover', this.dragOverHandler)
        if(this.dropHandler)
            window.removeEventListener('drop', this.dropHandler)
        if(this.dragLeaveHandler)
            window.removeEventListener('dragleave', this.dragLeaveHandler)
    },
    methods: {
        ...mapActions('files', [
            'uploadFiles',
            'createFolder',
            'createMyFolder',
            'moveMyFiles'
        ]),
        ...mapMutations('files', ['ADD_FILE']),
        async getHeaders() {
            try {
                const token = await TokenService.getAccessToken()
                if(token) {
                    this.includeHeader = {
                        Authorization: `Bearer ${token}`
                    }
                }
            } catch(error) {
                console.log(error)
            }
        },
        async confirmFolderUpload() {
            try {
                let folderId = this.sourceId
                if(folderId === this.rootId || folderId === 'my_files')
                    folderId = null

                if(this.isMyFiles) {
                    await this.createMyFolder({
                        folderName: this.createFolderName,
                        folderDesc: this.createFolderDesc,
                        folderId
                    })
                } else {
                    await this.createFolder({
                        folderName: this.createFolderName,
                        folderDesc: this.createFolderDesc,
                        rootId: this.rootId,
                        folderId
                    })
                }

                this.$message.success(this.$t('Folder created successfully'))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.modalVisible.folder = false
                this.createFolderName = ''
                this.createFolderDesc = ''
            }
        },
        hideDragField() {
            this.showDragField = false
        },
        getFileExtension(fileName = '') {
            const parts = fileName.split('.')
            return parts.length > 1 ? parts.pop().toLowerCase() : ''
        },
        queueItemIcon(uploadFile) {
            const extension = filesFormat.find(format => format === uploadFile.extension)
            if(extension)
                return require(`@/assets/images/files/${extension}.svg`)

            return require('@/assets/images/files/file.svg')
        },
        upsertQueueItem(queueItem) {
            const currentIndex = this.uploadingFiles.findIndex(file => file.uid === queueItem.uid)

            if(currentIndex === -1) {
                this.uploadingFiles.unshift(queueItem)
                return
            }

            this.$set(this.uploadingFiles, currentIndex, {
                ...this.uploadingFiles[currentIndex],
                ...queueItem
            })
        },
        async uploadRequest({ file, onProgress, onSuccess, onError }) {
            const uid = file.uid || `${Date.now()}-${Math.random()}`
            const cancelSource = axios.CancelToken.source()
            this.uploadQueueHidden = false
            this.upsertQueueItem({
                uid,
                name: file.name,
                extension: this.getFileExtension(file.name),
                percent: 0,
                status: 'uploading',
                cancelSource
            })

            try {
                const data = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload',
                    fileName: file.name,
                    headers: this.includeHeader,
                    cancelToken: cancelSource.token,
                    onProgress: ({ percent }) => {
                        onProgress({ percent })
                        this.upsertQueueItem({
                            uid,
                            percent,
                            status: 'uploading'
                        })
                    }
                })

                const uploadedFile = Array.isArray(data) ? data[0] : data
                this.upsertQueueItem({
                    uid,
                    percent: 100,
                    status: 'done'
                })
                onSuccess(uploadedFile)
                await this.handleUploadedFile(uploadedFile, file.name)
            } catch(error) {
                if(axios.isCancel(error)) {
                    this.upsertQueueItem({
                        uid,
                        status: 'error'
                    })
                    return
                }

                this.upsertQueueItem({
                    uid,
                    status: 'error'
                })
                onError(error)
                this.$message.error(this.$t('files.file_upload_error_with_name', {name: file.name}))
            } finally {
                this.showDragField = false
            }
        },
        async handleUploadedFile(file, rawFileName) {
            try {
                if(!this.sourceId && !this.rootId) {
                    this.attachmentFiles.push(file)
                    this.$message.success(this.$t('files.file_uploaded_successfully_alt', {name: file.name || rawFileName}))
                } else {
                    await this.confirmUpload(file)
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        async confirmUpload(file) {
            try {
                this.fileLoading = true
                const folderId = this.isFolder ? this.sourceId : null
                if(!this.isMyFiles) {
                    await this.uploadFiles({
                        files: [file.id],
                        rootId: this.rootId,
                        folderId
                    })
                } else {
                    this.ADD_FILE({
                        data: file,
                        key: 'my_files'
                    })
                    if(this.isFolder) {
                        await this.moveMyFiles({
                            from: 'my_files',
                            where: folderId,
                            files: [file],
                        })
                    }
                }

                this.$message.success(this.$t('files.file_uploaded_successfully_alt', {name: file.name}))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.fileLoading = false
            }
        },
        cancelActiveUploads() {
            this.uploadingFiles.forEach(file => {
                if(file.status === 'uploading' && file.cancelSource)
                    file.cancelSource.cancel('Upload cancelled')
            })
        },
        clearUploadQueue() {
            this.form.uploadingFiles.splice(0)
        },
        closeUploadQueue() {
            this.uploadQueueHidden = true
            if(!this.hasActiveUploads)
                this.clearUploadQueue()
        },
        dragOver(event) {
            event.stopPropagation()
            event.preventDefault()
            event.dataTransfer.dropEffect = 'copy'
            this.showDragField = true
        },
        dragLeave(event) {
            event.stopPropagation()
            event.preventDefault()
            if(event.clientX === 0 && event.clientY === 0)
                this.showDragField = false
        },
        dropComplete(event) {
            event.stopPropagation()
            event.preventDefault()
        }
    },
}
</script>

<style scoped lang="scss">
.file_create {
    position: relative;
}

.file_create__action_button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.create_item_grid {
    display: flex;
    width: 170px;
    height: 200px;
    padding: 20px;
    border: 2px dashed var(--borderColor);
    border-radius: var(--borderRadius);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
        background-color: #f0f3f7;
    }

    .create_item_icon_grid {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        background-color: var(--grayColor);
        border-radius: var(--borderRadius);
    }
}

.create_item_list {
    .create_item_icon_list {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        font-size: 10px;
        background-color: var(--grayColor);
        border-radius: 4px;
    }
}

.files_drag_field {
    position: absolute;
    top: 0;
    left: 50%;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 80%;
    height: 100%;
    max-height: 400px;
    border: 3px dashed var(--primaryColor);
    border-radius: 8px;
    background: #fff;
    transform: translateX(-50%);
}

.upload_queue {
    position: fixed;
    right: 24px;
    bottom: 24px;
    z-index: 1700;
    width: min(380px, calc(100vw - 32px));
    overflow: hidden;
    border: 1px solid rgba(46, 107, 255, 0.32);
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 12px 32px rgba(31, 41, 55, 0.12);
}

.upload_queue.collapsed {
    border-radius: 8px;
}

.upload_queue__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px 10px;
}

.upload_queue__title {
    font-size: 14px;
    font-weight: 700;
    color: #1f2937;
}

.upload_queue__header_actions {
    display: flex;
    gap: 4px;
}

.upload_queue__header_button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #111827;
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease;

    &:hover {
        background: #f3f6fb;
        color: #2e6bff;
    }

    .is-collapsed {
        transform: rotate(180deg);
    }
}

.upload_queue__status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 16px;
    background: #f4f7fc;
    color: #667085;
    font-size: 14px;
}

.upload_queue__status_action {
    border: none;
    background: transparent;
    color: #2e6bff;
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
}

.upload_queue__list {
    max-height: 280px;
    overflow: auto;
    padding: 4px 0;
}

.upload_queue__item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 12px 16px;
}

.upload_queue__item:not(:last-child) {
    border-bottom: 1px solid #eef2f7;
}

.upload_queue__item_main {
    display: flex;
    align-items: center;
    min-width: 0;
    gap: 10px;
}

.upload_queue__item_icon {
    width: 20px;
    height: 20px;
    object-fit: contain;
}

.upload_queue__item_name {
    font-size: 14px;
    line-height: 1.35;
    color: #374151;
}

.upload_queue__item_state {
    flex: 0 0 auto;
}

.upload_queue__badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
}

.upload_queue__badge--done {
    background: #22c55e;
    color: #fff;
}

.upload_queue__badge--error {
    background: #fee2e2;
    color: #ef4444;
}

.upload-queue-enter-active,
.upload-queue-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.upload-queue-enter,
.upload-queue-leave-to {
    opacity: 0;
    transform: translateY(12px);
}

@media (max-width: 767px) {
    .upload_queue {
        right: 12px;
        bottom: 12px;
        width: calc(100vw - 24px);
    }
}
</style>

<style lang="scss">
.files_drag_field {
    .ant-upload-drag {
        border: none;
        border-radius: 8px;
    }
}

.file_create_menu {
    .ant-upload-select {
        display: block;
    }
}

.files_attaching_drawer {
    .ant-upload-select {
        display: block;
    }
}

.upload_wfull {
    .ant-upload {
        width: 100%;
    }
}
</style>
