<template>
    <AddProject />
</template>

<script>
export default {
    components: {
        AddProject: () => import('./components/AddProject.vue')
    }
}
</script>