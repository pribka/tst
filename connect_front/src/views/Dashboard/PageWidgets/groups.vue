<template>
    <div :class="!isMobile && 'min-h-0 flex flex-col flex-grow'">
        <component 
            v-if="!isError && isStoreLoaded"
            :is="checkError" 
            storeName="workgroups"
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
            return !hasInInjectInit('Groups')
        },
        isStoreLoaded() {
            return this.$store.state.connectedModules.includes('workgroups')
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
            : () => import('@apps/Groups/index.vue')
    }
}
</script>

