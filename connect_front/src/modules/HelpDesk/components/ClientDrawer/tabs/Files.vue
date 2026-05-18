<template>
    <Files
        :sourceId="client.id"
        :isFounder="actions && actions.edit ? true : false"
        widgetEmbed
        isStudent />
</template>

<script>
export default {
    components: {
        Files: () => import('@apps/vue2Files')
    },
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    }
}
</script>