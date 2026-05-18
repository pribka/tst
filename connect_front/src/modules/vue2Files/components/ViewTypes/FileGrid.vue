<template>
    <div
        ref="fileGridWrap"
        class="w-full h-full">
        <div class="grid_scroller_wrap h-full">
            <RecycleScroller
                v-if="isMounted"
                class="scroller h-full"
                :class="attaching || widgetEmbed ? 'attaching_scroller' : ''"
                :buffer="100"
                :items="virtualFileList"
                keyField="id"
                :pageMode="false"
                :gridItems="gridColumnCount"
                :itemSize="gridItemHeight"
                :itemSecondarySize="gridItemWidth">
                <template #default="{ item }">
                    <!-- <FileCreate 
                        :createFounder="createFounder"
                        :rootId="rootId"
                        :sourceId="sourceId"
                        :oneUpload="oneUpload"
                        :getCreateContainer="getDropContainer"
                        :fileDragCreate="fileDragCreate"
                        :isMyFiles="isMyFiles"
                        :mobileApp="mobileApp"
                        viewType="card" />                     -->
                    <FileDropdown
                        :ref="`file_dropdown_${item.id}`"
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
                        <template v-slot:fileItem="{ openMenu, openFileDetail }">
                            <FileCard
                                :file="item" 
                                :mobileApp="mobileApp"
                                :rootId="rootId"
                                :sourceId="sourceId"
                                :fileOpenSwitch="fileOpenSwitch"
                                :openMenu="openMenu"
                                :openFileDetail="openFileDetail"
                                :selectedFiles="selectedFiles"
                                :cuttedFiles="cuttedFiles"
                
                                :setCurrentSource="setCurrentSource"/>
                        </template>
                    </FileDropdown>
                </template>
                <template #after>
                    <slot name="infiniteLoading"></slot>
                </template>
            </RecycleScroller>
        </div>
    </div>
</template>

<script>
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { RecycleScroller } from 'vue-virtual-scroller'

import myRolesProps from '../../mixins/myRolesProps'
import fileSourcesProps from '../../mixins/fileSourcesProps'
import fileViewsProps from '../../mixins/fileViewsProps'
import attachingSourcesProps from '../../mixins/attachingSourcesProps'
import fileActions from '../../mixins/fileActions'

import FileCard from './FileCard.vue'
import FileDropdown from '../FileDropdown.vue'

export default {
    mixins: [myRolesProps, fileSourcesProps, fileViewsProps, attachingSourcesProps, fileActions],
    components: {
        FileCard,
        FileDropdown,
        RecycleScroller
    },
    props: {
        removeFiles: {
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
        showFileCreate: {
            type: Boolean,
            default: true
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
    watch: {
        sourceId() {
            this.$nextTick(() => {
                const s = this.$refs.scroller
                if (s && s.$el) s.$el.scrollTop = 0
            })
        },
        fileList() {
            this.$nextTick(() => {
                const s = this.$refs.scroller
                if (s && s.$el && s.$el.scrollTop < 0) s.$el.scrollTop = 0
            })
        }
    },
    data() {
        return {
            isMounted: false,
            displayWidth: 0,
            gap: 5,
            trueWidth: 170,
            trueHeight: 200,
            observer: null
        }
    },
    computed: {
        virtualFileList() {
            return this.fileList
        },
        hasFileCreateItem() {
            return !this.isSearch && !this.isTrash && 
                this.isFounder && this.showFileCreate
        },
        gridColumnCount() {
            if(this.isMobile)
                return 2
            else
                return Math.floor(this.displayWidth / ( this.trueWidth + this.gap))
        },
        gridItemWidth() {
            if(this.attaching)
                return this.displayWidth / this.gridColumnCount
            else
                return this.displayWidth / this.gridColumnCount
        },
        gridItemHeight() {
            return this.trueHeight + this.gap
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    mounted() {
        this.isMounted = true

        const fileGridWrap = this.$refs.fileGridWrap
        this.displayWidth = fileGridWrap.clientWidth
        
        this.observer = new ResizeObserver(entries => {
            const element = entries[0]
            this.displayWidth = element.contentRect.width
        })
        
        this.observer.observe(fileGridWrap)
    },
    beforeDestroy() {
        const fileGridWrap = this.$refs.fileGridWrap
        this.observer.unobserve(fileGridWrap)
    },
    methods: {
        getDropContainer() {
            return this.$refs.fileGridWrap
        }
    }
}
</script>

<style scoped lang="scss">

.scroller {
    min-height: 100px;
    &.attaching_scroller{
        max-height: 500px;
    }
}

.file_grid {
    display: grid;
    gap: 8px;
    grid-auto-rows: 200px;
    grid-template-columns: repeat(auto-fit, 170px);
    justify-content: space-between;
}
</style>
