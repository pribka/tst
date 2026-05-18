<template>
    <component 
        :is="checkError" 
        storeName="contractors" />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
import { checkStore } from '@/utils/checkStore.js'
export default {
    mixins: [pageMeta],
    computed: {
        checkError() {
            if(checkStore('contractors')) {
                return () => import('@apps/Contractors')
            } else {
                return () => import('@/components/PageStoreError.vue')
            }
        }
    }
}
</script>
