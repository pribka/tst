<template>
    <component 
        :is="checkError" 
        storeName="monitor" />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
import { checkStore } from '@/utils/checkStore.js'
export default {
    mixins: [pageMeta],
    computed: {
        checkError() {
            if(checkStore('monitor')) {
                return () => import('@apps/LogisticMonitor')
            } else {
                return () => import('@/components/PageStoreError.vue')
            }
        }
    },
    components: {
        LogisticMonitor: () => import('@apps/LogisticMonitor')
    }
}
</script>