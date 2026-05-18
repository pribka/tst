<template>
    <div class="file_manager" :class="!isMobile && 'h-full'">
        <Files
            :showFileCreate="showFileCreate"
            :showFoldersCount="showFoldersCount"
            :rootId="sourceId"
            :isMyFiles="isMyFiles"
            :isFounder="isFounder"
            :oneUpload="oneUpload"
            :useIconButton="useIconButton"
            :mobileApp="mobileApp"
            :showHeader="showHeader"
            :fileDragCreate="fileDragCreate"
            :attachmentFiles="attachmentFiles"
            :showFilter="showFilter"
            :createFounder="createFounder"
            :widgetEmbed="widgetEmbed"
            :isStudent="isStudent" />
    </div>
</template>

<script>
import myRolesProps from './mixins/myRolesProps'
export default {
    mixins: [myRolesProps],
    props: {
        active: {
            type: [String, Number],
            default: ''
        },
        sourceId: {
            type: String,
            default: '' 
        },
        isMyFiles: {
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
        showFilter: {
            type: Boolean,
            default: true
        },
        fileDragCreate: {
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
        showHeader: {
            type: Boolean,
            default: true
        }
    },
    components: {
        Files: () => import('./components/Files')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        showFileCreate() {
            return this.active !== 'chat_files'
        },
        showFoldersCount() {
            return this.active !== 'chat_files'
        }
    }
}
</script>
