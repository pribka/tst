<template>
    <a-breadcrumb class="breadcrumbs">
        <a-breadcrumb-item 
            v-for="crumb in breadcrumbs" 
            :key="crumb.folder_id">
            <span   
                class="breadcrumb title" 
                :class="[(crumb.folder_id === sourceId) && 'current_breadcrumb', 
                         (breadcrumbs.length > 1) && 'title_mini']"
                @click="setCurrentSource(crumb.folder_id)">
                {{ crumb.name }}
            </span>
        </a-breadcrumb-item>
    </a-breadcrumb>
</template>

<script>
import { mapState } from 'vuex'

import fileSourcesProps from '../mixins/fileSourcesProps'

export default {
    mixins: [fileSourcesProps],
    props: {
        setCurrentSource: {
            type: Function,
            required: true
        },
        isMyFiles: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            files: state => state.files.files,
        }),
        currentSourceName() {
            const defaultSourceName = this.$t('All files')
            return this.files[this.sourceId].name || defaultSourceName
        },
        breadcrumbs() {
            const breadcrumbs = this.files[this.sourceId]?.breadcrumbs || []
            const rootCrumb = {
                name: this.$t("All files"),
                folder_id: this.isMyFiles ? 'my_files' : this.rootId
            }
            // if root crumb is undefined
            if(!breadcrumbs.length)
                return breadcrumbs.concat(rootCrumb)
            else if(breadcrumbs[0].folder_id === null)
                breadcrumbs[0].folder_id = this.isMyFiles ? 'my_files' : this.rootId
            const currentCrumb = {
                name: this.currentSourceName,
                folder_id: this.sourceId
            }
            return breadcrumbs.concat(currentCrumb)
        }
    },
}
</script>

<style scoped lang="scss">
.breadcrumbs {
    .breadcrumb {        
        cursor: pointer;
        &:hover {
            color: var(--text);
        }
    }
    .current_breadcrumb {
        color: var(--text);
    }
}
.title {
    font-weight: 300;
    font-size: 18px;
    @media(min-width: 1024px) {
        font-size: 24px;
    }
}
.title_mini{
    font-size: 16px;
    @media(min-width: 1024px) {
        font-size: 20px;
    }
}
</style>