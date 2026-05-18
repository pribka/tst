<template>
    <div></div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
//import { checkStore } from '@/utils/checkStore.js'
export default {
    mixins: [pageMeta],
    /*computed: {
        checkError() {
            if(checkStore('mybases')) {
                return () => import('@apps/MyBases')
            } else {
                return () => import('@/components/PageStoreError.vue')
            }
        }
    }*/
}
</script>
