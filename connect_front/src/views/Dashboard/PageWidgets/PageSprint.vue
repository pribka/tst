<template>
    <sprintList showPageTitle />
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        sprintList: () => import('@apps/vue2TaskComponent/components/Sprint/Sprints.vue'),
    },
    computed: {
        pageConfig() {
            return this.$route.meta?.pageConfig ? this.$route.meta.pageConfig : null
        }
    }
}
</script>