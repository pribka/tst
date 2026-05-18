<template>
    <div>
        <div @click="visible = true" >
            <slot name="openButton" />
        </div>
        <DrawerTemplate
            v-if="isMobile"
            :title="$t('Upload file')"
            placement="bottom"
            class="files_attaching_drawer attaching_drawer_wrap"
            destroyOnClose
            width="100%"
            v-model="visible"
            @close="closeModal">
            <Files
                ref="fileAttachFiles"
                :attachingRootId="attachingRootId"
                :attachingSourceId="attachingSourceId"
                :attachmentFiles="attachmentFiles"
                attaching
                :createFounder="createFounder"
                :oneUpload="oneUpload"
                :changeSelect="changeSelect"
                :mobileApp="mobileApp"
                @closeParentModal="closeModal"
                :isMyFiles="true"
                :isFounder="true"
                :isStudent="true" />
            <template #footer>
                <a-button size="large" :disabled="buttonDisabled" type="primary" class="mb-1" block @click="attachSelected()">
                    {{ $t('Attach') }}
                </a-button>
                <a-button type="ui" ghost block @click="closeModal()">
                    {{ $t('Close') }}
                </a-button>
            </template>
        </DrawerTemplate>
        <a-modal 
            v-else
            :dialogStyle="{ top: '30px' }"
            class="files_attaching_drawer"
            v-model="visible" 
            :title="$t('Upload file')"
            :width="700"
            @ok="attachSelected"
            :getContainer="getModalContainer"
            :okText="$t('Attach')"
            @close="closeModal"
            :cancelText="$t('Cancel')">
            <Files
                ref="fileAttachFiles"
                :attachingRootId="attachingRootId"
                :attachingSourceId="attachingSourceId"
                :attachmentFiles="attachmentFiles"
                :showDeviceUpload="showDeviceUpload"
                attaching
                :createFounder="createFounder"
                :oneUpload="oneUpload"
                :changeSelect="changeSelect"
                :mobileApp="mobileApp"
                @closeParentModal="closeModal"
                :zIndex="zIndex"
                :isMyFiles="true"
                :isFounder="true"
                :isStudent="true" />
            <template slot="footer">
                <div class="flex items-center justify-end">
                    <a-button 
                        type="ui"
                        ghost 
                        @click="closeModal()">
                        {{ $t('Close') }}
                    </a-button>
                    <a-button 
                        :disabled="buttonDisabled" 
                        type="primary" 
                        class="ml-2" 
                        @click="attachSelected()">
                        {{ $t('Attach') }}
                    </a-button>
                </div>
            </template>
        </a-modal>

        <div v-if="showAttached" >
            <template v-if="listType === 'picture'">
                <div class="file-grid">
                    <div 
                        v-for="(file, index) in attachmentFiles" 
                        :key="index"
                        class="flex items-center justify-between px-2 py-1 truncate file_p_card">
                        <div class="flex items-center truncate" :title="file.name">
                            <div class="w-6 aspect-square shrink-0">
                                <img 
                                    :data-src="file.is_image ? file.path : fileIcon(file)" 
                                    alt=""
                                    class="file_icon lazyload"
                                    :class="file.is_image && 'file_image'">
                            </div>
                            <div class="ml-2 truncate">
                                <div class="truncate file_name">
                                    {{ file.name }}
                                </div>
                                <div v-if="file.extension" class="truncate file_desc">
                                    {{ file.extension }}
                                </div>
                            </div>
                        </div>
                        <div :class="!isMobile && 'card_actions'">
                            <a-button
                                @click="deleteFile(file)"
                                type="ui"
                                ghost
                                shape="circle"
                                flaticon
                                icon="fi-rr-trash">
                            </a-button>
                        </div>
                    </div>
                </div>
            </template>
            <template v-else>
                <div class="attached_files">
                    <div 
                        v-for="(file, index) in attachmentFiles" 
                        :key="index"
                        class="attached_file">
                        <a-tooltip :title="`${file.name}.${file.extension}`">
                            <div class="file_image_wrapper">
                                <img 
                                    :data-src="file.is_image ? file.path : fileIcon(file)" 
                                    alt=""
                                    class="file_icon lazyload"
                                    :class="file.is_image && 'file_image'">
                            </div>
                            <div class="file_name font-light text-center truncate">
                                {{ file.name }}
                            </div>
                        </a-tooltip>
                        <span 
                            class="detach_file" 
                            @click="deleteFile(file)">
                            <i class="fi fi-rr-trash"></i>
                        </span>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import { filesFormat } from '@/utils'
import { mapActions } from 'vuex'
import attachingSourcesProps from '../mixins/attachingSourcesProps'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [attachingSourcesProps],
    props: {
        action: {
            type: String,
            // default: "/api/v1/common/upload/"
            default: `${process.env.VUE_APP_API_URL}/common/upload/`        
        },
        zIndex: {
            type: Number,
            default: null
        },
        attachmentFiles: {
            type: Array,
            default: ()=> []
        },
        attachmentFileIds: {
            type: Array,
            default: ()=> []
        },
        maxFileCount: {
            type: Number,
            default: 5
        },
        maxMBSize: {
            type: Number,
            default: 1
        },
        showAttached: {
            type: Boolean,
            default: true
        },
        listType: {
            type: String,
            default: 'default'
        },
        mobileApp: {
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
        getModalContainer: {
            type: Function,
            default: () => document.body
        },
        clearAttachmentsAfterAttach: {
            type: Boolean,
            default: true
        },
        showDeviceUpload: {
            type: Boolean,
            default: true
        }
    },
    components: {
        Files: () => import('./Files'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    data() {
        return {
            visible: false,
            buttonDisabled: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        zIndexAfterDrawer() {
            const openDrawers = this.$store.state.openDrawers
            return openDrawers?.[openDrawers.length - 1]?.zIndex
        }
    },
    methods: {
        ...mapActions('files', ['uploadFiles']),
        changeSelect(select) {
            select > 0 ? this.buttonDisabled = false : this.buttonDisabled = true
        },
        async handleChange(info) {
            const status = info.file.status;
            if (status === 'done') {
                const file = info.file.response[0]
                if(this.attachingRootId)
                    await this.confirmUpload(file)
                else
                    this.attachmentFiles.push(file)
                this.closeModal()
            } else if (status === 'error') {
                this.$message.error(this.$t('files.file_upload_error') + ` "${info.file.name}"`);
            }
        },
        async confirmUpload(file) {
            try {
                const folderId = this.attachingSourceId !== this.attachingRootId ? this.attachingSourceId : null
                if(!this.isMyFiles) {
                    await this.uploadFiles({
                        files: [file.id], 
                        rootId: this.attachingRootId, 
                        folderId: folderId
                    })
                } else {
                    this.ADD_FILE({
                        data: file, 
                        key: 'my_files'
                    })
                }
                this.$message.success(this.$t('files.file_uploaded_successfully', {name: file.name}));
                
            } catch(error) {
                errorHandler({error})
            }
        },
        fileIcon(file) {
            const extension = filesFormat.find(format => format === file.extension)
            if(extension)
                return require(`@/assets/images/files/${extension}.svg`)
            else
                return require(`@/assets/images/files/file.svg`)
        },
        openFileModal() {
            this.visible = true
        },
        deleteFile(file) {
            const deletingFileIndex = this.attachmentFiles.findIndex(attachedFile => attachedFile.id === file.id)
            this.attachmentFiles.splice(deletingFileIndex, 1)
        },
        attachFiles(files) {
            if(files.length > this.maxFileCount)
                this.$message.warning(this.$t('chat.file_max_count', {count: this.maxFileCount}))
            else
                this.handleFileUpload(files)
        },
        handleFileUpload(files) {
            Array.prototype.forEach.call(files, async (file, i) => {
                if(this.isMoreThanMaxSize(file.size)) {
                    this.$message.warning(this.$t('chat.file_size_error', {
                        name: file.name, 
                        filesize: this.maxMBSize
                    }))
                    return false
                }

                try {
                    // this.fileLoading = true
                    const data = await this.$uploadFile({
                        file,
                        url: this.action,
                        fieldName: 'upload',
                        fileName: file.name
                    })
                    if(data?.length)
                        this.attachmentFiles.push(data[0])
        
                } catch(error) {
                    errorHandler({error})
                } finally {
                    // this.fileLoading = false
                }
            })
        },
        isMoreThanMaxSize(size) {
            return size > (this.maxMBSize * (1024 ** 2))
        },
        closeModal() {
            this.visible = false
        },
        attachSelected() {
            this.$nextTick(() => {
                this.$refs.fileAttachFiles.attachSelected()
                if(this.clearAttachmentsAfterAttach) {
                    // this.$refs.fileAttachFiles.clearAttachments()
                }
            })
        }

    },
}
</script>

<style scoped lang="scss">
.attaching_drawer_wrap{
    &::v-deep{
        .drawer_body{
            overflow: hidden!important;
            display: flex;
            flex-direction: column;
            .files_wrap{
                height: 100%;
                .grow.overflow-hidden{
                    height: calc(100% - 119px);
                    display: flex;
                    flex-direction: column;
                    overflow: initial!important;
                    .relative.flex.flex-col{
                        height: 100%;
                        .file_list{
                            height: 100%!important;
                            .list_scroller_wrap{
                                height: calc(100% - 38px);
                            }
                        }
                    }
                }
            }
        }
    }
}
.files_attaching_drawer{
    &::v-deep{
        .ant-drawer-content-wrapper{
            height: 100%!important;
        }
        .ant-drawer-content,
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-modal-footer{
            position: sticky;
            bottom: 0;
            z-index: 100;
            background: #ffffff;
            width: 100%;
        }
        .ant-modal-body{
            height: calc(100vh - 220px);
            overflow: hidden;
        }
        .ant-drawer-body{
            height: 100%;
            padding: 0px;
            position: relative;
        }
        .drawer_footer{
            height: 90px;
            padding: 5px 15px;
            border-top: 1px solid var(--borderColor);
        }
        .float_add{
            --safe-area-inset-bottom: env(safe-area-inset-bottom);
            bottom: calc(100px + var(--safe-area-inset-bottom));
        }
        .file_list{
            min-height: 100%;
            .vue-recycle-scroller{
                max-height: 100%;
            }
        }
        .attaching_scroller{
            max-height: 100%!important;
        }
    }
}
.attached_files {
    display: grid;
    gap: 8px;
    grid-auto-rows: 100px;
    grid-template-columns: repeat(auto-fit, 100px);
    .attached_file {
        position: relative;

        border: 1px solid #d9d9d9;
        border-radius: 4px;
        .file_image_wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
    
            height: 70px;
            
            padding: 8px;
            .file_icon {
                width: 100%;
                max-height: 100%;
                
                object-fit: contain;
            }
            .file_image {
                border: 1px solid var(--borderColor);
                border-radius: 4px;
            }
        }
        .file_name {
            margin-top: 4px;
            padding: 0 8px;

            line-height: 1.1;
        }
        .detach_file {
            position: absolute;
            top: 8px;
            right: 6px;

            line-height: 1;
            font-size: 18px;

            cursor: pointer;
        }
    }
}

.file-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
.file_p_card{
    background: #f7f9fc;
    border-radius: 8px;
    min-height: 50px;
    position: relative;
    max-height: 50px;
    .card_actions{
        position: absolute;
        top: 0;
        height: 100%;
        right: 0;
        padding: 0 15px;
        background: #e6ebf7;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &:hover{
        .card_actions{
            opacity: 1;
        }
    }
    .file_desc{
        color: #888888;
        font-size: 12px;
        line-height: 18px;
    }
    .file_name{
        line-height: 22px;
    }
}
</style>

<style lang="scss">
.files_attaching_drawer {
    .filter_pop_wrapper {
        min-width: 0 !important;
    }
    @media(max-width: 1024px) {
        .list_scroller_wrap .scroller {
            max-height: calc(var(--vh, 1vh) * 100 - 450px);
        }
        .ant-modal {
            $top-indent: 30px;
            top: $top-indent;
        }
        .ant-modal-header {
            padding-left: 15px;
            padding-right: 15px;
        }
        .ant-modal-body {
            padding: 15px;
        }
    }
}
.shrink-0 {
    flex-shrink: 0;
}
</style>
