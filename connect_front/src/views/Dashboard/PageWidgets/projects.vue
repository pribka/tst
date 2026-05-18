<template>
    <div :class="!isMobile && 'min-h-0 flex flex-col flex-grow'">
        <component 
            v-if="!isError && isStoreLoaded"
            :is="checkError" 
            storeName="projects"
            :pageConfig="pageConfig" />
        <a-spin 
            v-if="!isError && !isStoreLoaded" 
            class="py-4" />
    </div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
import { hasInInjectInit } from '@/utils/checkStore.js'
export default {
    mixins: [pageMeta],
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        pageConfig() {
            return this.$route.meta?.pageConfig || null
        },
        isError() {
            return !hasInInjectInit('Projects')
        },
        isStoreLoaded() {
            return this.$store.state.connectedModules.includes('projects')
        }
    },
    data() {
        return {
            checkError: null
        }
    },
    created() {
        this.checkError = this.isError
            ? () => import('@/components/PageStoreError.vue')
            : () => import('@apps/Projects/index.vue')
    }
}
</script>

