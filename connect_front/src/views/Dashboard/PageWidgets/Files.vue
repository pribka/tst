<template>
    <div class="my_files_widget h-full">
        <vue2Files 
            :isMyFiles="true"
            :isFounder="true"
            :isStudent="true"/>
    </div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    name: 'PageWidgetsFiles',
    components: {
        vue2Files: () => import('@apps/vue2Files'),
    },
    
}
</script>

<style lang="scss" scoped>
.my_files_widget {
    padding: 15px;
}
</style>
