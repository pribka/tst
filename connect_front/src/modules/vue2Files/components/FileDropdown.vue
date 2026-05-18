<template>
    <div
        ref="dropWrapper"
        class="file_dropdown"
        @contextmenu.prevent.stop="openMenu">
        <slot
            name="fileItem"
            :openMenu="openMenu"
            :openFileDetail="openFileDetail"
            :downloadCurrentFile="downloadCurrentFile"
            :shareFile="share"
            :confirmDelete="confirmDelete"
            :canShowShare="canShowShare"
            :canDelete="canDelete" />

        <a-dropdown
            v-if="!isMobile"
            :visible="menuVisible"
            :trigger="[]"
            placement="bottomRight"
            :getPopupContainer="getDropContainer"
            @visibleChange="menuVisible = $event">
            <span class="file_dropdown__anchor"></span>

            <a-menu slot="overlay">
                <a-menu-item
                    key="detail"
                    @click="handleMenuAction(openFileDetail)">
                    <i class="fi fi-rr-info mr-2"></i>
                    <span>{{ $t('files.info') }}</span>
                </a-menu-item>

                <template v-if="sourceId || rootId">
                    <a-menu-item
                        v-if="isTrash"
                        key="restore_from_trash"
                        @click="handleMenuAction(openRestoreModal)">
                        <i class="fi fi-rr-time-past mr-2"></i>
                        <span>{{ $t('files.restore') }}</span>
                    </a-menu-item>

                    <a-menu-item
                        key="download"
                        @click="handleMenuAction(downloadCurrentFile)">
                        <i class="fi fi-rr-download mr-2"></i>
                        <span>{{ downloadLabel }}</span>
                    </a-menu-item>

                    <a-menu-item
                        v-if="canRename"
                        key="rename"
                        @click="handleMenuAction(openRenameModal)">
                        <i class="fi fi-rr-pencil mr-2"></i>
                        <span>{{ $t('files.edit') }}</span>
                    </a-menu-item>

                    <template v-if="!isFolder && !appType">
                        <a-menu-item
                            key="share"
                            @click="handleMenuAction(share)">
                            <i class="fi fi-rr-share mr-2"></i>
                            <span>{{ $t('files.share') }}</span>
                        </a-menu-item>

                        <a-menu-item
                            key="task"
                            @click="handleMenuAction(createTask)">
                            <i class="fi fi-rr-add mr-2"></i>
                            <span>{{ $t('files.create_task') }}</span>
                        </a-menu-item>

                        <a-menu-item
                            v-if="canOpenInNewTab"
                            key="open_in_new_tab"
                            @click="handleMenuAction(openInNewTab)">
                            <i class="fi fi-rr-arrow-up-right-from-square mr-2"></i>
                            <span>{{ $t('files.open_in_new_tab') }}</span>
                        </a-menu-item>
                    </template>
                </template>

                <a-menu-item
                    v-if="canDelete"
                    key="delete"
                    @click="handleMenuAction(confirmDelete)">
                    <i class="fi fi-rr-trash mr-2"></i>
                    <template v-if="!sourceId && !rootId">
                        <span>{{ $t('files.detach') }}</span>
                    </template>
                    <template v-else>
                        <span>{{ $t('files.delete') }}</span>
                    </template>
                </a-menu-item>

                <template v-if="sourceId || rootId">
                    <a-menu-item
                        v-if="isAttaching"
                        key="attach_file"
                        @click="handleMenuAction(confirmUpload)">
                        <i class="fi fi-rr-add-document mr-2"></i>
                        <span>{{ $t('files.pin') }}</span>
                    </a-menu-item>

                    <a-menu-item
                        v-if="canPreviewDoc"
                        key="preview_doc"
                        @click="handleMenuAction(openPreviewModal)">
                        <i class="fi fi-rr-expand mr-2"></i>
                        <span>{{ $t('Preview') }}</span>
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>

        <a-drawer
            v-else
            placement="bottom"
            :visible="menuVisible"
            class="file_dropdown_mobile_drawer"
            height="auto"
            :closable="false"
            destroyOnClose
            :getContainer="getDrawerContainer"
            @close="closeMenu">
            <div class="file_dropdown_mobile_drawer__sheet">
                <div class="file_dropdown_mobile_drawer__handle">
                    <span></span>
                </div>

                <div class="file_dropdown_mobile_drawer__title truncate">
                    {{ file.name }}
                </div>

                <div class="file_dropdown_mobile_drawer__list">
                    <button
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(openFileDetail)">
                        <i class="fi fi-rr-info"></i>
                        <span>{{ $t('files.info') }}</span>
                    </button>

                    <button
                        v-if="isTrash"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(openRestoreModal)">
                        <i class="fi fi-rr-time-past"></i>
                        <span>{{ $t('files.restore') }}</span>
                    </button>

                    <button
                        v-if="sourceId || rootId"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(downloadCurrentFile)">
                        <i class="fi fi-rr-download"></i>
                        <span>{{ downloadLabel }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && canRename"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(openRenameModal)">
                        <i class="fi fi-rr-pencil"></i>
                        <span>{{ $t('files.edit') }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && !isFolder && !appType"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(share)">
                        <i class="fi fi-rr-share"></i>
                        <span>{{ $t('files.share') }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && !isFolder && !appType"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(createTask)">
                        <i class="fi fi-rr-add"></i>
                        <span>{{ $t('files.create_task') }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && canOpenInNewTab"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(openInNewTab)">
                        <i class="fi fi-rr-arrow-up-right-from-square"></i>
                        <span>{{ $t('files.open_in_new_tab') }}</span>
                    </button>

                    <button
                        v-if="canDelete"
                        type="button"
                        class="file_dropdown_mobile_drawer__action file_dropdown_mobile_drawer__action--danger"
                        @click="handleMenuAction(confirmDelete)">
                        <i class="fi fi-rr-trash"></i>
                        <span>{{ !sourceId && !rootId ? $t('files.detach') : $t('files.delete') }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && isAttaching"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(confirmUpload)">
                        <i class="fi fi-rr-add-document"></i>
                        <span>{{ $t('files.pin') }}</span>
                    </button>

                    <button
                        v-if="(sourceId || rootId) && canPreviewDoc"
                        type="button"
                        class="file_dropdown_mobile_drawer__action"
                        @click="handleMenuAction(openPreviewModal)">
                        <i class="fi fi-rr-expand"></i>
                        <span>{{ $t('Preview') }}</span>
                    </button>
                </div>
            </div>
        </a-drawer>

        <FileDetailModal
            :visible="visible.detail"
            :file="file"
            :isFolder="isFolder"
            :relatedItems="relatedItemList"
            :relatedLoading="relatedLoading"
            :showShare="canShowShare"
            :showDelete="canDelete"
            :getContainer="getDropContainer"
            @close="visible.detail = false"
            @download="downloadCurrentFile"
            @share="share"
            @remove="confirmDelete"
            @related-click="getRelatedUrl" />

        <a-modal
            v-model="visible.rename"
            :title="$t('Edit name or description')"
            :getContainer="getDropContainer"
            :cancelText="$t('Cancel')"
            :okText="$t('Confirm')"
            @ok="rename">
            <a-input
                v-model="newFileName"
                :placeholder="$t('Folder name')" />
            <a-textarea
                v-model="newFileDesc"
                class="mt-2"
                :placeholder="$t('Description')"
                :rows="4" />
        </a-modal>

        <a-modal
            v-model="visible.restore"
            :width="700"
            :getContainer="getDropContainer"
            class="file_restore"
            :title="$t('Restore')"
            :cancelText="$t('Cancel')"
            :okText="$t('Restore to current')"
            @ok="restoreTo">
            <Files
                :showFileCreate="false"
                :isRestoring="true"
                :restoreDest="restoreDest"
                :isMyFiles="true"
                :isFounder="true"
                :isStudent="true" />
        </a-modal>

        <a-modal
            v-if="!isFolder"
            :title="$t('File preview')"
            :visible="visible.docPreview"
            :getContainer="getDropContainer"
            :destroyOnClose="true"
            class="doc_view_modal"
            :width="windowWidth"
            :dialog-style="{
                top: '0px',
                left: '0px',
                right: '0px',
                bottom: '0px'
            }"
            :footer="null"
            @cancel="visible.docPreview = false">
            <component
                :is="docPreviewWidget"
                :file="file" />
        </a-modal>
    </div>
</template>

<script>
import fileSourcesProps from '../mixins/fileSourcesProps'
import attachingSourcesProps from '../mixins/attachingSourcesProps'
import myRolesProps from '../mixins/myRolesProps'
import Files from './Files'
import FileDetailModal from './FileDetailModal.vue'

import eventBus from '@/utils/eventBus'
import { mapActions, mapMutations, mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'FileDropdown',
    mixins: [fileSourcesProps, attachingSourcesProps, myRolesProps],
    components: {
        FileDetailModal,
        Files
    },
    props: {
        file: {
            type: Object,
            required: true
        },
        removeFiles: {
            type: Function,
            default: () => {}
        },
        restoreFiles: {
            type: Function,
            default: () => {}
        },
        isMyFiles: {
            type: Boolean,
            default: false
        },
        isTrash: {
            type: Boolean,
            default: false
        },
        setCurrentSource: {
            type: Function,
            default: () => {}
        },
        getDropContainer: {
            type: Function,
            default: () => document.body
        }
    },
    data() {
        return {
            menuVisible: false,
            fileLoading: false,
            newFileName: this.file.name,
            newFileDesc: this.file.description,
            visible: {
                detail: false,
                rename: false,
                docPreview: false,
                restore: false
            },
            relatedLoading: false,
            restoreDest: [],
            relatedObjects: {}
        }
    },
    computed: {
        ...mapState({
            appType: state => state.appType
        }),
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isFolder() {
            return this.file.obj_type === 'folder'
        },
        isAttaching() {
            return !!this.attachingRootId
        },
        isFileChanged() {
            return (this.file.name !== this.newFileName) ||
                (this.file.description !== this.newFileDesc)
        },
        docPreviewWidget() {
            if(['pdf'].includes(this.file.extension))
                return () => import('./DocPreview/PDFViewer.vue')
            if(['doc', 'docx'].includes(this.file.extension))
                return () => import('./DocPreview/WordViewer.vue')
            if(['xls', 'xlsx'].includes(this.file.extension))
                return () => import('./DocPreview/SheetsViewer.vue')
            return false
        },
        canRename() {
            return this.isFounder && !(this.isMyFiles && !this.isFolder)
        },
        canDelete() {
            return !this.file.is_dynamic && this.isFounder
        },
        canOpenInNewTab() {
            return this.file.is_image || this.file.is_video || this.file.extension === 'pdf'
        },
        canPreviewDoc() {
            return ['pdf'].includes(this.file.extension)
        },
        canShowShare() {
            return !this.isFolder && !this.appType
        },
        downloadLabel() {
            return this.isFolder
                ? this.$t('files.download_as_zip')
                : this.$t('files.download')
        },
        relatedItemList() {
            return Object.entries(this.relatedObjects)
                .reduce((items, [category, relatedList]) => {
                    relatedList.forEach((relatedObject, index) => {
                        items.push({
                            key: `${category}-${relatedObject.id || index}`,
                            label: this.textCrop(this.getRelatedObjectStringView(relatedObject), 28),
                            object: relatedObject
                        })
                    })
                    return items
                }, [])
        }
    },
    methods: {
        ...mapActions('files', [
            'renameFile',
            'renameMyFile',
            'renameFolder',
            'renameMyFolder',
            'uploadFiles',
            'downloadFolderAsZIP',
            'downloadMyFolderAsZIP'
        ]),
        ...mapMutations('files', ['ADD_FILE']),
        openMenu() {
            this.menuVisible = true
        },
        closeMenu() {
            this.menuVisible = false
        },
        handleMenuAction(action) {
            this.closeMenu()
            if(typeof action === 'function')
                action()
        },
        openPreviewModal() {
            this.menuVisible = false
            this.visible.docPreview = true
        },
        openRenameModal() {
            this.visible.rename = true
        },
        confirmContainer() {
            return () => this.getDropContainer()
        },
        getDrawerContainer() {
            return document.body
        },
        triggerBrowserDownload(url, fileName) {
            const link = document.createElement('a')
            link.href = url
            link.target = '_blank'
            link.rel = 'noopener'
            link.download = fileName || ''
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        },
        downloadCurrentFile() {
            if(this.isFolder) {
                this.downloadFolder()
                return
            }

            this.triggerBrowserDownload(this.file.path, this.file.name)
        },
        openInNewTab() {
            window.open(this.file.path, '_blank', 'noopener')
        },
        share() {
            this.visible.detail = false
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'files.files',
                shareId: this.file.id,
                object: this.file,
                shareUrl: this.file.path,
                shareTitle: `${this.$t('files.file')} - ${this.file.name}`
            })
        },
        async createTask() {
            this.visible.detail = false

            let query = Object.assign({}, this.$route.query)

            if(query && query.task) {
                this.$store.commit('task/CHANGE_TASK_SHOW', false)
                delete query.task
                await this.$router.push({query})
            }

            const form = {
                attachments: [this.file],
                reason_model: 'files',
                reason_id: this.file.id
            }

            this.$store.commit('task/SET_TASK_TYPE', 'task')
            eventBus.$emit('ADD_WATCH', {type: 'add_task', data: form})
        },
        async rename() {
            if(!this.newFileName)
                return

            this.visible.rename = false

            try {
                if(this.isFolder) {
                    if(this.isMyFiles) {
                        await this.renameMyFolder({
                            rootId: this.rootId,
                            folderId: this.sourceId,
                            fileId: this.file.id,
                            newFileName: this.newFileName,
                            newFileDesc: this.newFileDesc,
                        })
                    } else {
                        await this.renameFolder({
                            rootId: this.rootId,
                            folderId: this.sourceId,
                            fileId: this.file.id,
                            newFileName: this.newFileName,
                            newFileDesc: this.newFileDesc,
                        })
                    }
                } else if(this.isMyFiles) {
                    await this.renameMyFile({
                        folderId: this.sourceId,
                        fileId: this.file.id,
                        newFileName: this.newFileName,
                        newFileDesc: this.newFileDesc,
                    })
                } else {
                    await this.renameFile({
                        rootId: this.rootId,
                        folderId: this.sourceId,
                        fileId: this.file.id,
                        newFileName: this.newFileName,
                        newFileDesc: this.newFileDesc,
                    })
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        async confirmUpload() {
            const file = this.file
            let rootId = this.rootId
            let folderId = this.isFolder ? this.sourceId : null
            if(this.attachingRootId) {
                rootId = this.attachingRootId
                folderId = this.attachingSourceId
                folderId = (folderId && (folderId !== rootId)) ? folderId : null
            }
            try {
                this.fileLoading = true
                if(!this.isMyFiles || this.attachingRootId) {
                    await this.uploadFiles({
                        files: [file.id],
                        rootId,
                        folderId
                    })
                } else {
                    this.ADD_FILE({
                        data: file,
                        key: 'my_files'
                    })
                }
                this.$message.success(this.$t('files.file_uploaded_successfully', {name: file.name}))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.fileLoading = false
            }
        },
        async downloadFolder() {
            try {
                let status
                if(this.isMyFiles) {
                    status = await this.downloadMyFolderAsZIP({
                        rootId: this.rootId,
                        folderId: this.file.id
                    })
                } else {
                    status = await this.downloadFolderAsZIP({
                        rootId: this.rootId,
                        folderId: this.file.id
                    })
                }

                if(status.alreadyWorking)
                    this.$message.success(this.$t('files.archive_is_already_working'))
                else
                    this.$message.success(this.$t('files.archive_is_working'))
            } catch(error) {
                errorHandler({error})
            }
        },
        confirmDelete() {
            const self = this
            this.visible.detail = false

            let title = self.isTrash
                ? (self.isFolder ? this.$t('Delete folder forever?') : this.$t('Delete file forever?'))
                : (self.isFolder ? this.$t('Delete folder?') : this.$t('Delete file?'))
            let content = self.isTrash
                ? this.$t('Object will be deleted permanently', {name: self.file.name})
                : (self.isFolder
                    ? this.$t('Object will be deleted with all children', {name: self.file.name})
                    : this.$t('Object will be deleted', {name: self.file.name}))

            if(!this.sourceId && !this.rootId) {
                title = this.$t('Detach file?')
                content = this.$t('Object will be detached', {name: self.file.name})
            }

            this.$confirm({
                title,
                content,
                getContainer: this.confirmContainer(),
                okText: this.$t('Yes'),
                okType: 'danger',
                cancelText: this.$t('No'),
                onOk() {
                    if(!self.sourceId && !self.rootId) {
                        eventBus.$emit('detach_file', self.file.id)
                    } else {
                        self.removeFiles(self.isFolder ? {folders: self.file} : {files: self.file})
                    }
                },
            })
        },
        restoreTo() {
            const file = !this.isFolder ? this.file : []
            const folder = this.isFolder ? this.file : []
            const dest = this.restoreFiles({
                files: file,
                folders: folder,
                dest: this.restoreDest[0]
            })
            this.restoreNotification(dest)
        },
        async openRestoreModal() {
            await this.$http('/files/folders/')
            this.visible.restore = true
        },
        restoreNotification(dest) {
            const key = `open${Date.now()}`
            this.$notification.open({
                message: this.$t('Object restored', {name: this.file.name}),
                getContainer: this.confirmContainer(),
                btn: h => {
                    return h(
                        'a-button',
                        {
                            props: {
                                type: 'primary',
                                size: 'default',
                            },
                            on: {
                                click: () => {
                                    if(dest === null)
                                        dest = 'my_files'
                                    this.setCurrentSource(dest, 'my_files')
                                    this.$notification.close(key)
                                },
                            },
                        },
                        this.$t('Go to folder'),
                    )
                },
                placement: 'bottomRight',
                key,
            })
        },
        async openFileDetail() {
            try {
                this.menuVisible = false
                this.visible.detail = true
                this.relatedLoading = true

                if(!this.isFolder) {
                    const { data } = await this.$http(`/files/${this.file.id}/related_objects/`)
                    this.relatedObjects = Object.keys(data)
                        .filter(category => data[category].length)
                        .reduce((destObject, category) => {
                            return Object.assign(destObject, {
                                [category]: data[category]
                            })
                        }, {})
                } else {
                    this.relatedObjects = {}
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.relatedLoading = false
            }
        },
        getRelatedObjectType(relatedObject) {
            switch(relatedObject.object_type) {
            case 'workgroups.WorkgroupModel':
                return {
                    name: this.$t('Workgroup (project)'),
                    url: {
                        name: 'viewGroup',
                        value: relatedObject.id
                    }
                }
            case 'comments.CommentModel':
                return { name: this.$t('Comment') }
            case 'chat.MessageModel':
                return {
                    name: this.$t('Chat message'),
                    url: {
                        name: 'chat_id',
                        value: relatedObject.chat
                    }
                }
            case 'meetings.PlannedMeetingModel':
                return { name: this.$t('Meetings') }
            case 'bpms_common.NewsModel':
                return { name: this.$t('News') }
            case 'processes.FinancialApplicationModel':
                return { name: this.$t('Financial application') }
            case 'tasks.TaskModel':
                return {
                    name: this.$t('Tasks'),
                    url: {
                        name: 'task',
                        value: relatedObject.id
                    }
                }
            case 'catalogs.GoodsModel':
                return { name: this.$t('Goods') }
            case 'crm.GoodsOrderModel':
                return {
                    name: this.$t('Order'),
                    url: {
                        name: 'order',
                        value: relatedObject.id
                    }
                }
            default:
                return null
            }
        },
        getRelatedUrl(relatedItem) {
            const relatedObject = relatedItem.object || relatedItem
            const urlConfig = this.getRelatedObjectType(relatedObject)?.url
            if(!urlConfig)
                return

            const query = Object.assign({}, this.$route.query)
            const queryValue = Number(query[urlConfig.name])
            if(!query[urlConfig.name] || queryValue !== urlConfig.value) {
                query[urlConfig.name] = urlConfig.value
                this.$router.push({query})
                this.visible.detail = false
            }
        },
        getRelatedObjectStringView(relatedObject) {
            if(relatedObject.object_type === 'chat.MessageModel')
                return relatedObject.text
            if(relatedObject.object_type === 'crm.GoodsOrderModel')
                return relatedObject.counter
            if(relatedObject.object_type === 'comments.CommentModel') {
                return `${relatedObject.text} ${this.$t('files.from')} ${this.$moment(relatedObject.created_at).format('DD-MM-YY HH:mm:ss')}`
            }

            return relatedObject.name || relatedObject.string_view
        },
        textCrop(text, length) {
            if(text?.length > length)
                return text.slice(0, length) + '...'
            return text
        }
    }
}
</script>

<style lang="scss">
.file_restore {
    .filter_pop_wrapper {
        min-width: 0 !important;
    }
}

.doc_view_modal {
    .ant-modal-body {
        padding: 0;
        height: calc(100% - 36px);
    }

    .ant-modal {
        padding: 0;
        height: 100vh;
    }

    .ant-modal-content {
        height: 100%;
        border-radius: 0;
    }

    .ant-modal-wrap {
        overflow: hidden;
    }

    .ant-modal-header {
        padding: 7px 18px;
        border-bottom: 0;
        border-radius: 0;

        .ant-modal-title {
            font-size: 14px;
        }
    }

    .ant-modal-close-x {
        width: 36px;
        height: 36px;
        line-height: 30px;
    }
}

.file_dropdown_mobile_drawer {
    .ant-drawer-content {
        background: transparent;
    }

    .ant-drawer-wrapper-body,
    .ant-drawer-content {
        overflow: hidden;
    }

    .ant-drawer-content-wrapper {
        max-height: calc(90% - env(safe-area-inset-top) - env(safe-area-inset-bottom));
    }

    .ant-drawer-body {
        padding: 0;
        background: transparent;
    }
}
</style>

<style scoped lang="scss">
.file_dropdown {
    position: relative;
}

.file_dropdown__anchor {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 1px;
    height: 1px;
    pointer-events: none;
    opacity: 0;
}

.file_dropdown_mobile_drawer__sheet {
    padding: 8px 12px calc(12px + env(safe-area-inset-bottom));
    background: #fff;
    border-radius: 12px 12px 0 0;
}

.file_dropdown_mobile_drawer__handle {
    display: flex;
    justify-content: center;
    padding: 4px 0 10px;

    span {
        width: 42px;
        height: 4px;
        border-radius: 999px;
        background: #d7dee9;
    }
}

.file_dropdown_mobile_drawer__title {
    margin-bottom: 10px;
    padding: 0 4px;
    font-size: 15px;
    font-weight: 700;
    color: #1f2937;
}

.file_dropdown_mobile_drawer__list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.file_dropdown_mobile_drawer__action {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    min-height: 46px;
    padding: 0 12px;
    border: 1px solid #e8edf5;
    border-radius: 8px;
    background: #fff;
    color: #24324a;
    text-align: left;
    cursor: pointer;

    i {
        font-size: 16px;
        color: #607087;
    }
}

.file_dropdown_mobile_drawer__action--danger {
    color: #d92d20;

    i {
        color: inherit;
    }
}
</style>
