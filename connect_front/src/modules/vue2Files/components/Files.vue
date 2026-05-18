<template>
    <div
        class="files_wrap flex flex-col" 
        ref="filesWrap"
        :class="[loading.global && 'light_wrap', !isMobile && 'h-full']">
        <div>
            <div v-if="showHeader" class="lg:flex justify-between mb-2">
                <a-spin 
                    v-if="loading.global" 
                    class="files_global_spin"/>
                <FileBreadcrumbs
                    :rootId="rootId"
                    :sourceId="sourceId"
                    :isMyFiles="isMyFiles"
                    :setCurrentSource="setCurrentSource" />
                <div class="flex lg:mt-0 justify-between items-center" :class="isMobile ? 'mt-1' : 'mt-2'">
                    <div class="file_count mr-2">
                        <template v-if="isSearch">
                            <div>{{ $t('Search results') }}: {{ searchCount }}</div>
                        </template>
                        <template v-else-if="!isTrash">
                            <a-spin v-if="loading.count && !attaching" />
                            <template v-else>
                                <span v-if="showFoldersCount" class="mr-2">
                                    {{ $t('Folders') }}: {{ count.folders }}
                                </span>
                                <span>
                                    {{ $t('Files') }}: {{ count.files }}
                                </span>
                            </template>
                        </template>
                    </div>
                    <a-radio-group 
                        v-model="activeViewType"
                        size="default"
                        :class="isMobile && 'mobile_list'"
                        class="files_view_type"
                        @change="changeViewType">
                        <a-radio-button 
                            v-for="view in viewTypes" 
                            :key="view.name" 
                            :value="view.name">
                            <i class="fi" :class="view.icon"></i>
                        </a-radio-button>
                    </a-radio-group>
                </div>
            </div>
            <template v-if="isMyFiles">
                <template v-if="!isMobile">
                    <div class="flex">
                        <PageFilter 
                            v-if="showFilter"
                            class="w-full"
                            :model="myFilesModel"
                            :getPopupContainer="getPopupContainer"
                            size="large"
                            :page_name="sourceId" />
                        <DropdownSort
                            class="ml-3"
                            :model="myFilesModel" 
                            :page_name="sourceId" />        
                    </div>
                </template>
            </template>
            <a-auto-complete
                v-else
                v-model="searchText"
                :data-source="dataSource"
                style="width: 100%"
                :placeholder="$t('Search files and folders')"/>
            <!-- Actions -->
            <div
                class="flex justify-between items-center" 
                :class="isMobile ? 'mt-1 mb-1' : 'mt-2 mb-2'">
                <template v-if="showHeaderActions">
                    <div class="file_actions">
                        <a-tooltip 
                            class="action_icon"
                            v-if="!isTrash && canPasteFiles && isFounder">
                            <a-button 
                                type="ui"
                                flaticon
                                icon="fi-rr-copy-alt"
                                @click="pasteFiles" />
                            <template slot="title">                            
                                {{ $t('Paste into current folder') }}
                            </template>
                        </a-tooltip>
                    </div>
                </template>
                <template v-if="isMyFiles && !isAttachingToFiles">
                    <div class="file_trash">
                        <template
                            v-if="isTrash">
                            <div class="file_trash__actions">
                                <a-button
                                    v-if="fileList.length && !allVisibleFilesSelected"
                                    @click="selectAllVisibleFiles">
                                    {{ $t('Select all') }}
                                </a-button>
                                <a-button
                                    v-if="isSelected"
                                    @click="clearSelected">
                                    {{ $t('Deselect all') }}
                                </a-button>
                                <a-button
                                    v-if="fileList.length"
                                    class="file_trash__clear"
                                    @click="clearTrash">
                                    {{ $t('Clear') }}
                                </a-button>
                                <a-button 
                                    v-if="!isMobile"
                                    @click="setCurrentRoot('my_files')"
                                    class="flex items-center">
                                    <i class="btn_icon fi fi-rr-arrow-small-left"></i>
                                    <span class="ml-2">
                                        {{ $t('My files') }}
                                    </span>
                                </a-button>
                            </div>
                        </template>
                        <template v-else>
                            <a-button
                                v-if="!isMobile"
                                @click="setCurrentRoot('trash')"
                                class="flex items-center">
                                <i class="btn_icon fi fi-rr-trash"></i>
                                <span class="ml-2">
                                    {{ $t('Trash') }}
                                </span>
                            </a-button>
                        </template>
                    </div>
                </template>
                <FileCreate 
                    v-if="isFounder && showFileCreate"
                    :rootId="rootId"
                    :sourceId="sourceId"
                    :isMyFiles="isMyFiles"
                    :useIconButton="useIconButton"
                    viewType="button"
                    :showDeviceUpload="showDeviceUpload"
                    :createFounder="createFounder"
                    :oneUpload="oneUpload"
                    :getCreateContainer="getDropContainer"
                    :fileDragCreate="fileDragCreate"
                    :mobileApp="mobileApp"
                    :attachmentFiles="attachmentFiles"
                    :class="isMobile ? 'mb-2' : 'ml-auto'" />
            </div>
        </div>


        <!-- View type -->
        <div class="grow overflow-hidden" :class="!isMobile && 'h-full'">
            <component 
                :key="sourceId"
                :is="viewType"
                :zIndex="zIndex"
                :fileList="fileList"
                :removeFiles="removeFiles"
                :restoreFiles="restoreFiles"
                :fileDragCreate="fileDragCreate"
                :isSearch="isSearch"
                
                :rootId="rootId"
                :sourceId="sourceId"
                :oneUpload="oneUpload"
                :attachingRootId="attachingRootId"
                :attachingSourceId="attachingSourceId"
                :attaching="attaching"
                :widgetEmbed="widgetEmbed"
                :isMyFiles="isMyFiles"
                :isTrash="isTrash"
                :mobileApp="mobileApp"
                :createFounder="createFounder"
                :showFileCreate="showFileCreate && !isTrash"
                
                :selectedFiles="selectedFiles"
                :cuttedFiles="cuttedFiles"
    
                :setCurrentSource="setCurrentSource"
    
                :isFounder="isFounder"
                :isStudent="isStudent">
                <template 
                    v-if="sourceId"
                    #infiniteLoading>
                    <InfiniteLoading
                        ref="infiniteFileLoading"
                        :key="isSearch ? `search-infinity-${sourceId}` : `infinity-${sourceId}`"
                        :force-use-infinite-wrapper="activeViewType === 'list' && !isMobile"
                        @infinite="infiniteFileHandler">
                        <div slot="spinner" >
                            <a-spin class="mt-4"/>
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </InfiniteLoading>
                </template>
            </component>
        </div>

        <FileSelectionActions
            :visible="!!isSelected"
            :count="isSelected"
            :title="selectedActionTitle"
            :canDownload="!!isSelected"
            :canMove="isFounder && createFounder && !isTrash"
            :canDelete="isFounder && !isAttachingToFiles"
            :canRestore="isTrash && !!isSelected"
            :canAttach="attaching"
            :downloadLabel="selectedDownloadLabel"
            :moveLabel="$t('Move')"
            :restoreLabel="$t('files.restore')"
            :deleteLabel="isMyFiles ? $t('files.delete') : $t('files.detach')"
            :attachLabel="$t('Attach')"
            :isMobile="isMobile"
            @download="downloadSelected"
            @move="cutFiles"
            @restore="openRestoreSelectedModal"
            @delete="confirmDelete"
            @attach="attachSelected"
            @clear="clearSelected" />

        <a-modal
            v-model="visible.restoreSelected"
            :width="700"
            :getContainer="getPopupContainer"
            class="file_restore"
            :title="$t('Restore')"
            :cancelText="$t('Cancel')"
            :okText="$t('Restore to current')"
            @ok="restoreSelected">
            <Files
                :showFileCreate="false"
                :isRestoring="true"
                :restoreDest="selectedRestoreDest"
                :isMyFiles="true"
                :isFounder="isFounder"
                :isStudent="isStudent" />
        </a-modal>

        <div v-if="isMobile && isMyFiles" class="float_add">
            <DropdownSort
                class="mb-2"
                :model="myFilesModel" 
                :page_name="sourceId" />  
            <div class="filter_slot">
                <PageFilter
                    class="w-full"
                    :model="myFilesModel"
                    :getPopupContainer="getPopupContainer"
                    size="large"
                    :page_name="sourceId" />
            </div>
            <template v-if="isMyFiles && !isAttachingToFiles" >
                <a-button 
                    v-if="isTrash"
                    flaticon
                    shape="circle"
                    icon="fi-rr-arrow-small-left"
                    @click="setCurrentRoot('my_files')" />
                <a-button
                    v-else
                    flaticon
                    shape="circle"
                    icon="fi-rr-trash"
                    @click="setCurrentRoot('trash')" />
            </template>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions, mapGetters } from 'vuex'
import eventBus from '@/utils/eventBus.js'
import myRolesProps from '../mixins/myRolesProps'
import attachingSourcesProps from '../mixins/attachingSourcesProps'

import debounce from '@/utils/lodash/debounce'
const PREFIX_RESTORE = 'restore-'
export default {
    name: 'Files',
    mixins: [attachingSourcesProps, myRolesProps],
    components: {
        FileCreate: () => import('./FileCreate.vue'),
        FileBreadcrumbs: () => import('./FileBreadcrumbs.vue'),
        FileSelectionActions: () => import('./FileSelectionActions.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        DropdownSort: () => import('./DropdownSort.vue')
    },
    props: {
        showHeader: {
            type: Boolean,
            default: true
        },
        useIconButton: {
            type: Boolean,
            default: false
        },
        rootId: {
            type: [String, Number],
            default: ''
        },
        isMyFiles: {
            type: Boolean,
            default: false
        },
        showFileCreate: {
            type: Boolean,
            default: true
        },
        showFoldersCount: {
            type: Boolean,
            default: true
        },
        attachmentFiles: {
            type: Array,
            default: () => []
        },
        attaching: {
            type: Boolean,
            default: false
        },
        isRestoring: {
            type: Boolean,
            default: false
        },
        restoreDest: {
            type: Array,
            default: () => []
        },
        widgetEmbed: {
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
        changeSelect: {
            type: Function,
            default: () => {}
        },
        showFilter: {
            type: Boolean,
            default: true
        },
        fileDragCreate: {
            type: Boolean,
            default: true
        },
        zIndex: {
            type: Number,
            default: 1000
        },
        showDeviceUpload: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            loading: {
                global: false,
                files: false,
                count: false,
            },
            fileListLoading: false,
            currentRootId: this.rootId,

            isSearch: false,
            searchText: '',
            dataSource: [],

            sourceId: null,
            activeViewType: 'list',
            count: {
                files: 0,
                folders: 0
            },
            pageSize: 15,
            selectedFiles: {
                from: null,
                list: []
            },
            visible: {
                restoreSelected: false
            },
            selectedRestoreDest: [],
            cuttedFiles: {},
            myFilesModel: 'common.File'
        } 
    },
    computed: {
        ...mapState({
            files: state => state.files.files,
            config: state => state.config.config
        }),
        ...mapGetters('files', [
            'getFilesViewType', 
        ]),
        showHeaderActions() {
            return this.canPasteFiles && this.isFounder
        },
        getDropContainer() {
            return this.$refs.filesWrap
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        defaultView() {
            return this.config?.files_setting?.default_view || 'list'
        },
        viewTypes() {
            return this.config?.files_setting?.available_views?.length ? this.config.files_setting.available_views : [
                {
                    icon: "fi-rr-list",
                    name: "list"
                },
                {
                    icon: "fi-rr-apps",
                    name: "grid"
                }
            ]
        },
        fileList() {
            if (!this.sourceId && !this.rootId) {
                return this.attachmentFiles
            }
            if (this.isSearch) 
                return this.files['found_files']?.results || []
            return this.files[this.sourceId]?.results || []
        },
        searchCount() {
            return this.files['found_files']?.count || 0
        },
        nextPage() {
            const defaultPage = 1
            const sourceId = this.isSearch ? 'found_files' : this.sourceId 
            const currentPage = this.files[sourceId]?.page
            return currentPage ? (currentPage + 1) : defaultPage
        },
        currentNext() {
            const sourceId = this.isSearch ? 'found_files' : this.sourceId
            if(this.files[sourceId]?.next === null)
                return null
            return true
        },
        isFolder() {
            const rootIds = ['trash', 'my_files', this.currentRootId]
            return !rootIds.includes(this.sourceId.replace(PREFIX_RESTORE, ''))
            // if(this.isTrash) {
            //     if('trash' !== this.sourceId)
            //         return true
            // }
            // else if(this.isMyFiles) {
            //     if('my_files' !== this.sourceId)
            //         return true
            // } else if(this.rootId !== this.sourceId)
            //     return true
            // return false
        },
        isTrash() {
            return this.currentRootId === "trash"
        },
        viewType() {
            switch(this.activeViewType) {
            case 'grid': 
                return () => import('./ViewTypes/FileGrid.vue')
            case 'list': 
                return () => import('./ViewTypes/FileList.vue')
            default:
                return () => import('./ViewTypes/FileList.vue')
            }
        },
        isSelected() {
            return this.selectedFiles.list.length
        },
        allVisibleFilesSelected() {
            if(!this.fileList.length)
                return false

            return this.fileList.every(file =>
                this.selectedFiles.list.some(selectedFile => selectedFile.id === file.id)
            )
        },
        selectedActionTitle() {
            return this.$t('Selected')
        },
        selectedDownloadLabel() {
            return this.$t('files.download')
        },
        isCutted() {
            return this.cuttedFiles?.list?.length 
        },
        canPasteFiles() {
            if(this.isCutted) {
                if(this.sourceId !== this.cuttedFiles.from) {
                    for(const file of this.cuttedFiles.list) {
                        if(file.id === this.sourceId)
                            return false
                    }
                    return true
                }
            }
            return false 
        },
        isAttachingToFiles() {
            return !!this.attachingRootId
        },
        infiniteFileHandler() {
            return this.isSearch ? this.getFoundFileList : this.getFileList
        }
    },
    watch: {
        searchText: async function(newText) {
            if(newText.length > 2) {
                

                this.debouncedRestartSearch()
                // await this.setCurrentSource('found_files')

            } else {
                this.isSearch = false
                await this.setCurrentSource(this.sourceId)
            }
        },
        isSelected(val) {
            this.changeSelect(val)
        }
    },
    async created() {
        this.debouncedRestartSearch = debounce(this.restartSearch, 1000)

        this.initViewType()

        if(this.attachmentFiles.length) {
            this.selectedFiles.list.splice(0)
            this.selectedFiles.list.push(...this.attachmentFiles)
        }

        const query = JSON.parse(JSON.stringify(this.$route.query))

        const defaultSourceId = query.folder || this.rootId
        let initSourceId = this.isMyFiles ? 'my_files' : defaultSourceId 
        if(this.isRestoring)
            initSourceId = PREFIX_RESTORE + initSourceId
        await this.setCurrentSource(initSourceId)
    },
    methods: {
        ...mapActions('files', [
            'getFiles', 
            'getFoundFiles', 
            'getMyFiles', 
            'getTrashFiles',
            'getFoldersForRestore',
            'deleteFiles', 
            'deleteMyFiles',
            'fileCount', 
            'myFileCount', 
            'moveFiles', 
            'moveMyFiles',
            'uploadFiles',
            'downloadFolderAsZIP',
            'downloadMyFolderAsZIP',
            'clearTrash'
        ]),
        getPopupContainer() {
            return this.$refs.filesWrap
        },
        async getFileList($state) {
            if(!this.fileListLoading) {
                if(this.currentNext) {
                    try {
                        this.fileListLoading = true
                        this.loading.files = true
                        const folderId = this.isFolder ? this.sourceId.replace(PREFIX_RESTORE, '') : null
                        if(this.isMyFiles) {
                            if(this.isRestoring) {
                                await this.getFoldersForRestore({
                                    folderId: folderId, 
                                    params: {
                                        page_size: this.pageSize,
                                        page: this.nextPage,
                                        page_name: this.sourceId
                                    }
                                })
                            }
                            else if(this.isTrash)
                                await this.getTrashFiles({
                                    folderId: folderId, 
                                    params: {
                                        page_size: this.pageSize,
                                        page: this.nextPage,
                                        page_name: this.sourceId
                                    }
                                })
                            else
                                await this.getMyFiles({
                                    folderId: folderId, 
                                    params: {
                                        page_size: this.pageSize,
                                        page: this.nextPage,
                                        page_name: this.sourceId
                                    }
                                })
                        } else {
                            await this.getFiles({
                                rootId: this.rootId, 
                                folderId: folderId,
                                params: {
                                    page_size: this.pageSize,
                                    page: this.nextPage,
                                    page_name: this.sourceId
                                }
                            })
                        }
                    
                        if(this.currentNext) {
                            $state.loaded()
                        } else {
                            $state.complete()
                        }
                    } catch(error) {
                        this.$message.error(error?.data?.detail || this.$t('File loading error'))
                        console.log(error)
                    } finally {
                        this.loading.files = false
                        this.fileListLoading = false
                    }
                } else {
                    $state.complete()
                }
            }
        },
        async getFoundFileList($state) {
            if(!this.fileListLoading) {
                if(this.currentNext) {
                    try {
                        this.fileListLoading = true
                        this.loading.files = true
    
                        const folderId = this.isFolder ? this.sourceId : null
                        if(this.isMyFiles) {
                            // await this.getMyFiles({ 
                            //     params: {
                            //         page_size: this.pageSize,
                            //         page: this.nextPage,
                            //         page_name: this.sourceId
                            //     }
                            // })
                        } else {
                            await this.getFoundFiles({
                                rootId: this.rootId, 
                                folderId: folderId,
                                params: {
                                    page_size: this.pageSize,
                                    page: this.nextPage,
                                    page_name: this.sourceId,
                                    search: this.searchText,
                                    folder: folderId
                                }
                            })
                        }
                        if(this.currentNext) {
                            $state.loaded()
                        } else {
                            $state.complete()
                        }
                    } catch(error) {
                        this.$message.error(error?.data?.detail || this.$t('File loading error'))
                        console.log(error)
                    } finally {
                        this.loading.files = false
                        this.fileListLoading = false
                    }
                } else {
                    $state.complete()
                }
            }
        },
        async removeFiles({files = [], folders = []}) {
            this.loading.global = true

            if(files)
                files = Array.isArray(files) ? files : [files]
            if(folders)
                folders = Array.isArray(folders) ? folders : [folders]

            const folderId = this.isFolder ? this.sourceId : null
            const removedItems = [...folders, ...files]

            try {
                if(this.isTrash) {
                    await this.$store.dispatch('files/deleteFilesFromTrash', {
                        folderId: folderId,
                        folders: folders,
                        files: files
                    })
                } else if(this.isMyFiles) {
                    await this.deleteMyFiles({
                        folderId: folderId,
                        folders: folders,
                        files: files
                    })
                } else {
                    await this.deleteFiles({
                        rootId: this.rootId,
                        folderId: folderId,
                        files: files,
                        folders: folders
                    })
                }

                this.syncRemovedFilesState(removedItems)
            } finally {
                this.loading.global = false
            }
        },
        async setCurrentSource(sourceId, rootId = null) {
            if(this.isRestoring) {
                this.restoreDest.splice(0)
                this.restoreDest.push(sourceId)
                if (!sourceId.includes(PREFIX_RESTORE)) 
                    sourceId = PREFIX_RESTORE + sourceId
            } 

            if(this.isSearch) {
                this.isSearch = false
                this.searchText = ''
            }
            if(sourceId === 'trash')
                this.currentRootId = 'trash'
            if(sourceId === 'my_files')
                this.currentRootId = 'my_files'
            if(rootId !== null)
                this.currentRootId = rootId

            this.sourceId = sourceId
            
            this.selectedFiles = {
                from: null,
                list: []
            }
            
            if(!this.isAttachingToFiles && !this.attaching) {
                this.setCurrentRouteQuery()
            }
            if(!this.isTrash) {
                if (this.sourceId) {
                    await this.updateFileCount()
                }
            }

        },
        async setCurrentRoot(rootId) {
            this.currentRootId = rootId
            this.setCurrentSource(rootId)
        },
        setCurrentRouteQuery() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            
            if(this.isFolder) {
                if(query.folder !== this.sourceId) {
                    query.folder = this.sourceId
                    this.$router.replace({ query })
                }
            } else if(query.folder) {
                delete query['folder']
                this.$router.replace({ query })
            }
        },
        changeViewType(event) {
            const viewType = event.target.value
            this.$store.commit('files/SET_FILE_VIEW_TYPE', viewType)

        },
        initViewType() {
            let viewType = this.getFilesViewType
            if(!viewType)
                viewType = this.defaultView || 'list'
            this.activeViewType = viewType 
        },
        async updateFileCount() {
            this.loading.count = true

            let count = 0
            const folderId = this.isFolder ? this.sourceId.replace(PREFIX_RESTORE, '') : null
            if(this.isMyFiles)
                count = await this.myFileCount({ 
                    folderId: folderId
                })
            else {
                count = await this.fileCount({
                    rootId: this.rootId,
                    folderId: folderId
                })
            }

            this.count = count

            this.loading.count = false
        },
        async pasteFiles() {
            const where = this.isFolder ? this.sourceId : null
            try {
                if(this.isMyFiles) {
                    await this.moveMyFiles({
                        from: this.cuttedFiles.from,
                        where: where,
                        files: this.cuttedFiles.list,
                    })
                } else {
                    await this.moveFiles({
                        rootId: this.rootId,
                        from: this.cuttedFiles.from,
                        where: where,
                        files: this.cuttedFiles.list,
                    })
                }
                this.$message.success(this.$t("Files moved successfully"))
            } catch(error) {
                this.$message.error(this.$t("File move error") + error)
            } finally {
                this.cuttedFiles = {}
            }
        },
        syncRemovedFilesState(removedItems = []) {
            if(!removedItems.length)
                return

            const removedIds = new Set(removedItems.map(file => file.id))

            for(let index = this.selectedFiles.list.length - 1; index >= 0; index -= 1) {
                if(removedIds.has(this.selectedFiles.list[index].id))
                    this.selectedFiles.list.splice(index, 1)
            }

            if(!this.selectedFiles.list.length)
                this.selectedFiles.from = null

            if(this.cuttedFiles?.list?.length) {
                for(let index = this.cuttedFiles.list.length - 1; index >= 0; index -= 1) {
                    if(removedIds.has(this.cuttedFiles.list[index].id))
                        this.cuttedFiles.list.splice(index, 1)
                }

                if(!this.cuttedFiles.list.length)
                    this.cuttedFiles = {}
            }
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
        async downloadSelectedFolder(folder) {
            if(!folder)
                return

            let status
            if(this.isMyFiles) {
                status = await this.downloadMyFolderAsZIP({
                    folderId: folder.id
                })
            } else if(this.rootId) {
                status = await this.downloadFolderAsZIP({
                    rootId: this.rootId,
                    folderId: folder.id
                })
            }

            if(!status)
                return

            if(status.alreadyWorking)
                this.$message.success(this.$t('files.archive_is_already_working'))
            else
                this.$message.success(this.$t('files.archive_is_working'))
        },
        async downloadSelected() {
            const selectedItems = [...this.selectedFiles.list]
            for(const item of selectedItems) {
                if(item.obj_type === 'folder')
                    await this.downloadSelectedFolder(item)
                else
                    this.triggerBrowserDownload(item.path, item.name)
            }
        },
        cutFiles() {
            this.cuttedFiles = {
                from: this.selectedFiles.from,
                list: [...this.selectedFiles.list] 
            }
            this.selectedFiles.list.splice(0)
        },
        async attachSelected() {
            this.attachmentFiles.push(...this.selectedFiles.list) 
            if(this.isAttachingToFiles) {
                const fileIListId = this.attachmentFiles.map(file => file.id)

                const folderId = this.attachingSourceId !== this.attachingRootId ? this.attachingSourceId : null
                const alreadyExistFiles = await this.uploadFiles({
                    files: fileIListId, 
                    rootId: this.attachingRootId, 
                    folderId: folderId
                })
                alreadyExistFiles.forEach(file => 
                    this.$message.warning(this.$t('files.file_already_attached', {name: file.name}))
                )
            }
            this.clearSelected()
            this.$emit('closeParentModal')
        },
        openRestoreSelectedModal() {
            this.visible.restoreSelected = true
        },
        restoreSelected() {
            const files = []
            const folders = []

            for(const file of this.selectedFiles.list) {
                if(file.obj_type === 'folder')
                    folders.push(file)
                else
                    files.push(file)
            }

            this.restoreFiles({
                folders: folders,
                files: files,
                dest: this.selectedRestoreDest[0] || `${PREFIX_RESTORE}my_files`
            })

            this.visible.restoreSelected = false
            this.clearSelected()
        },
        selectAllVisibleFiles() {
            this.selectedFiles.from = this.sourceId
            this.selectedFiles.list.splice(0)
            this.selectedFiles.list.push(...this.fileList)
        },
        clearSelected() {
            this.selectedFiles.list.splice(0)
            this.selectedFiles.from = null
        },
        clearAttachments() {
            this.attachmentFiles.splice(0)
        },
        async confirmDelete() {
            const self = this
            this.$confirm({
                title: self.isMyFiles ? this.$t('Are you sure you want to delete the file?') : this.$t('Are you sure you want to detach the file?'),
                okText: this.$t('Yes'),
                okType: 'danger',
                getContainer: this.getPopupContainer(),
                cancelText: this.$t('No'),
                async onOk() {
                    await self.deleteSelected()
                },
            })
        },
        async deleteSelected() {
            const files = [],
                folders = []
            for(const file of this.selectedFiles.list) 
                if(file.obj_type === 'folder')
                    folders.push(file)
                else 
                    files.push(file)

            await this.removeFiles({folders: folders, files: files})
            this.selectedFiles.list.splice(0)
        },
        restartSearch() {
            if(this.files['found_files']) {
                this.clearFoundFiles()
            }
            this.resetInfiniteLoading()        
            this.isSearch = true
        },
        clearFoundFiles() {
            const foundFiles = this.files['found_files']
            foundFiles.results.splice(0)
            foundFiles.page = 0
            foundFiles.next = true
        },
        resetInfiniteLoading() {
            this.$nextTick(() => {
                if(this.$refs.infiniteFileLoading)
                    this.$refs.infiniteFileLoading.stateChanger.reset()
            })
        },
        restoreFiles({files = [], folders = [], dest = null}) {
            if(files)
                files = Array.isArray(files) ? files : [files]
            if(folders)
                folders = Array.isArray(folders) ? folders : [folders]
            
            dest = dest || `${PREFIX_RESTORE}my_files`
            dest = dest.replace(PREFIX_RESTORE, '')
            dest = dest !== 'my_files' ? dest : null

            this.$store.dispatch('files/restoreFiles', {
                folderId: dest,
                folders: folders,
                files: files
            })

            return dest
        },
    },

    mounted() {
        eventBus.$on(`update_filter_${this.myFilesModel}`, () => {
            this.resetInfiniteLoading()
            this.$store.commit('files/CLEAR_ALL', this.sourceId)
        })
        eventBus.$on(`detach_file`, (fileId) => {
            const foundIndex = this.attachmentFiles.findIndex(file => fileId === file.id)
            if (foundIndex !== -1) {
                this.attachmentFiles.splice(foundIndex, 1)
            }
        })
    },

    beforeDestroy() {
        eventBus.$off(`update_filter_${this.myFilesModel}`)
        eventBus.$off('detach_file')
        
        const query = JSON.parse(JSON.stringify(this.$route.query))
        if(query.folder) {
            delete query['folder']
            this.$router.replace({ query })
        }
    },
}
</script>

<style scoped lang="scss">
.files_wrap {
    transition: opacity 0.2s ease;
}
.files_global_spin {
    position: absolute;
    z-index: 2000;
    top: 40px;
    left: 50%;
    transform: translateX(-50%);
}
.light_wrap {
    opacity: 0.3;
}
.action_icon {
    &:not(:last-child) {
        margin-right: 0.5rem;
    }
}

.file_trash__actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.file_trash__clear {
    margin-right: 0;
}

</style>

<style lang="scss">
.files_view_type {
    display: flex;
    .ant-radio-button-wrapper{
        border: none;
        font-size: 20px;
        padding: 0 10px;
        &::before{
            display: none;
        }
    }
    .ant-radio-button{
        display: none;
    }
    &.mobile_list{
        .ant-radio-button-wrapper{
            display: flex;
            align-items: center;
            span{
                display: flex;
                align-items: center;
            }
        }
    }
}
.btn_icon {
    line-height: 100%;
}
</style>
