<template>
    <a-drawer
        :title="drawerTitle"
        class="drawer"
        :width="drawerWidth"
        :destroyOnClose="true"
        :zIndex="1000"
        @close="closeDrawer"
        :visible="drawerVisible">
        <div class="drawer_header"></div>
        <div class="drawer_body">
            <Files
                :attachmentFiles="attachmentFiles"
                :sourceId="rootId"
                isFounder
                isStudent />

        </div>
        <div class="drawer_footer"></div>
    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        Files: () => import('@apps/vue2Files')
    },
    props: {
        driwerTitle: {
            type: String,
            default: ''
        },
        rootId: {
            type: String,
            default: ''
        },
        attachmentFiles: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            drawerVisible: false
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        drawerTitle() {
            return this.driwerTitle || this.$t('task.file_upload')
        },
        drawerWidth() {
            if(this.windowWidth > 900)
                return 900
            if(this.windowWidth < 800 && this.windowWidth > 500)
                return this.windowWidth - 30
            return this.windowWidth
        },
    },
    methods: {
        openDrawer() {
            this.drawerVisible = true
        },
        closeDrawer() {
            this.drawerVisible = false
        },
    }    
}
</script>

<style lang="scss" scoped>

::v-deep.drawer {
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
    }
    .drawer_footer{
        border-top: 1px solid var(--borderColor);
        height: 40px;
        padding-left: 15px;
        padding-right: 15px;
    }
    .drawer_header{
        border-bottom: 1px solid var(--borderColor);
    }
    .drawer_body{
        height: calc(100% - 40px);
        padding: 30px;

        .drawer_scroll{
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
        }
    }
}
</style>