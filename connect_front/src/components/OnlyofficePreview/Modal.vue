<template>
    <a-modal
        :visible="visible"
        :footer="null"
        :closable="false"
        destroyOnClose
        wrapClassName="onlyoffice-preview-modal-wrap"
        :width="'100vw'"
        :bodyStyle="{ padding: 0, height: '100vh' }"
        :style="{ top: 0, paddingBottom: 0 }"
        @cancel="close">
        <component
            v-if="visible && query"
            :is="initComponent"
            :query="query"
            modalMode
            showClose
            @close="close" />
    </a-modal>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        OnlyofficePreviewViewer: () => import('./Viewer.vue')
    },
    computed: {
        ...mapState({
            modalState: state => state.onlyofficePreview
        }),
        visible() {
            return !!this.modalState?.visible
        },
        query() {
            return this.modalState?.query || null
        },
        initComponent() {
            if(this.visible && this.query)
                return () => import('./Viewer.vue')
            return null
        }
    },
    methods: {
        close() {
            this.$store.commit('CLOSE_ONLYOFFICE_PREVIEW')
        }
    }
}
</script>

<style lang="scss">
.onlyoffice-preview-modal-wrap{
    top: 0;
    padding: 0;
    overflow: hidden;

    .ant-modal{
        width: 100vw !important;
        max-width: 100vw;
        margin: 0;
        top: 0 !important;
        padding-bottom: 0 !important;
        height: 100vh;
    }

    .ant-modal-content{
        height: 100vh;
        border-radius: 0;
        overflow: hidden;
    }

    .ant-modal-body{
        height: 100vh;
        padding: 0;
    }
}
</style>
