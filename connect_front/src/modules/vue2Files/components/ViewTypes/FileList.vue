<template>
    <div class="relative flex flex-col" :class="!isMobile && 'h-full'" ref="viewContainer">
        <div 
            class="file_list grow overflow-hidden flex flex-col"
            :class="isMobile ? 'mobile' : 'h-full'">
            <div
                v-if="fileList.length"
                class="file_list_toolbar">
                <div class="file_list_toolbar__label">
                    {{ $t('All files') }}
                </div>

                <a-checkbox
                    :checked="checkAll"
                    @change="switchGlobalCheckbox" />
            </div>

            <div class="list_scroller_wrap grow" :class="!isMobile && 'h-full'">
                <div
                    ref="listScroller"
                    class="file_list_groups"
                    :data-infinite-wrapper="!isMobile ? 'true' : null"
                    :class="attaching || widgetEmbed ? 'attaching_scroller' : ''">
                    <section
                        v-for="group in groupedFiles"
                        :key="group.key"
                        class="file_group">
                        <div
                            v-if="group.label"
                            class="file_group__title">
                            {{ group.label }}
                        </div>

                        <div class="file_group__items">
                            <FileDropdown
                                v-for="(item, index) in group.items"
                                :ref="`file_dropdown_${item.id}`"
                                :key="`${group.key}-${index}-${item.id}`"
                                :file="item"
                                :removeFiles="removeFiles"
                                :restoreFiles="restoreFiles"
                                :setCurrentSource="setCurrentSource"
                                :attachingRootId="attachingRootId"
                                :attachingSourceId="attachingSourceId"
                                :getDropContainer="getDropContainer"
                                :isFounder="isFounder"
                                :isStudent="isStudent"
                                :rootId="rootId"
                                :sourceId="sourceId"
                                :isMyFiles="isMyFiles"
                                :isTrash="isTrash">
                                <template v-slot:fileItem="{ openMenu, openFileDetail, downloadCurrentFile, shareFile, confirmDelete, canShowShare, canDelete }">
                                    <FileListItem 
                                        :file="item"
                                        :setCurrentSource="setCurrentSource"
                                        :rootId="rootId"
                                        :mobileApp="mobileApp"
                                        :sourceId="sourceId"
                                        :fileOpenSwitch="fileOpenSwitch"
                                        :openMenu="openMenu"
                                        :openFileDetail="openFileDetail"
                                        :downloadCurrentFile="downloadCurrentFile"
                                        :shareFile="shareFile"
                                        :confirmDelete="confirmDelete"
                                        :canShowShare="canShowShare"
                                        :canDelete="canDelete"
                                        :selectedFiles="selectedFiles"
                                        :cuttedFiles="cuttedFiles" />
                                </template>
                            </FileDropdown>
                        </div>
                    </section>

                    <slot name="infiniteLoading"></slot>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import myRolesProps from '../../mixins/myRolesProps'
import fileSourcesProps from '../../mixins/fileSourcesProps'
import fileViewsProps from '../../mixins/fileViewsProps'
import attachingSourcesProps from '../../mixins/attachingSourcesProps'
import fileActions from '../../mixins/fileActions'

import FileListItem from './FileListItem.vue'
import FileDropdown from '../FileDropdown.vue'

export default {
    mixins: [myRolesProps, fileSourcesProps, fileViewsProps, attachingSourcesProps, fileActions],
    components: {
        FileListItem,
        FileDropdown
    },
    props: {
        removeFiles: {
            type: Function,
            default: () => {}
        },        
        showFileCreate: {
            type: Boolean,
            default: true
        },
        selectedFiles: {
            type: Object,
            default: () => {}
        },
        cuttedFiles: {
            type: Object,
            default: () => {}
        },
        isSearch: {
            type: Boolean,
            default: false
        },

        isTrash: {
            type: Boolean,
            default: false
        },

        restoreFiles: {
            type: Function,
            default: () => {}
        },
        attaching: {
            type: Boolean,
            default: false
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
        fileDragCreate: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        checkAll() {
            if(!this.fileList.length)
                return false

            return this.fileList.length === this.selectedFiles.list.length
        },
        groupedFiles() {
            const groups = this.fileList.reduce((destGroups, file) => {
                const rawDate = this.getFileDate(file)
                const momentDate = rawDate ? this.$moment(rawDate) : null
                const key = momentDate?.isValid() ? momentDate.format('YYYY-MM-DD') : 'undated'

                if(!destGroups[key]) {
                    destGroups[key] = {
                        key,
                        label: this.getGroupLabel(momentDate),
                        order: momentDate?.isValid() ? momentDate.valueOf() : -1,
                        items: []
                    }
                }

                destGroups[key].items.push(file)
                return destGroups
            }, {})

            return Object.values(groups).sort((leftGroup, rightGroup) => rightGroup.order - leftGroup.order)
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        sourceId() {
            this.$nextTick(() => this.resetFilesScroll())
        }
    },
    methods: {
        resetFilesScroll() {
            const s = this.$refs.listScroller
            if (!s) return

            s.scrollTop = 0
        },
        getDropContainer() {
            return this.$refs.viewContainer
        },
        getFileDate(file) {
            return file.attachment_date || file.updated_at || file.created_at || null
        },
        getGroupLabel(momentDate) {
            if(!momentDate || !momentDate.isValid())
                return ''

            if(momentDate.isSame(this.$moment(), 'day'))
                return this.$t('today')

            if(momentDate.isSame(this.$moment().subtract(1, 'day'), 'day'))
                return this.$t('yesterday')

            return momentDate.format('DD.MM.YYYY')
        },
        switchGlobalCheckbox(event) {
            const isChecked = event.target.checked
            this.selectedFiles.from = this.sourceId
            this.selectedFiles.list.splice(0)
            if(isChecked) {
                this.selectedFiles.list.push(...this.fileList)
            }
        },
    }
}
</script>

<style scoped lang="scss">
.file_list {
    min-height: 80px;
}

.file_list_toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
    padding: 0 4px;
}

.file_list_toolbar__label {
    font-size: 13px;
    font-weight: 600;
    color: #8d99ae;
}

.list_scroller_wrap {
    min-height: 100px;
}

.file_list_groups {
    height: 100%;
    overflow: auto;
    padding-right: 4px;

    &.attaching_scroller {
        max-height: 450px;
    }
}

.file_group + .file_group {
    margin-top: 18px;
}

.file_group__title {
    margin-bottom: 10px;
    padding: 0 4px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #9aa4b2;
}

.file_group__items {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.mobile {
    .file_list_toolbar {
        margin-bottom: 10px;
    }

    .file_list_groups {
        height: auto;
        overflow: visible;
        padding-right: 0;
    }

    .file_group__title {
        margin-bottom: 8px;
    }
}
</style>
