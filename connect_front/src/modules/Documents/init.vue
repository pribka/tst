<template>
    <div>
        <CreateDocument />
        <DocumentView />
    </div>
</template>

<script>
export default {
    components: {
        CreateDocument: () => import('./components/CreateDocument'),
        DocumentView: () => import('./components/DocumentView.vue')
    }
}
</script>