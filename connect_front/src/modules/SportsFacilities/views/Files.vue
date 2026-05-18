<template>
    <div class="documents-wrap">
        <Files
            :sourceId="sourceId"
            :isFounder="fileFounder"
            :isStudent="false" />
    </div>
</template>
<script>
export default {
    name: 'Documents',
    components: {
        Files: () => import('@apps/vue2Files')
    },
    computed: {
        sourceId() {
            return this.$route.params.id
        },
        fileFounder() {
            return (this.actionInfo && this.actionInfo.documents) ? true : false
        }
    },
    props: {
        actionInfo: {
            type: Object,
            default: () => {}
        }
    }
}
</script>