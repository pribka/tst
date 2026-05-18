<template>
    <div class="grid page_grid gap-5 2xl:gap-8">
        <Aside :loading="loading" :project="project" />
        <ProjectForm 
            v-if="project" 
            :actionInfo="actionInfo"
            :actions="actions"
            :project="project"
            :viewMode="viewMode"
            :statusList="statusList" />
        <a-skeleton v-else active />
    </div>
</template>

<script>
import Aside from '../components/ProjectAside.vue'
import ProjectForm from '../components/ProjectForm.vue'
export default {
    props: {
        loading: {
            type: Boolean,
            default: false
        },
        viewMode: {
            type: Boolean,
            default: false
        },
        project: {
            type: Object,
            default: () => {}
        },
        actionInfo: {
            type: Object,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => {}
        },
        statusList: {
            type: Array,
            default: () => []
        }
    },
    components: {
        Aside,
        ProjectForm
    }
}
</script>

<style lang="scss" scoped>
.page_grid{
    grid-template-columns: 1fr;
    @media (min-width: 1100px) {
        grid-template-columns: 420px 1fr;
    }
    @media (min-width: 1200px) {
        grid-template-columns: 520px 1fr;
    }
    @media (min-width: 1400px) {
        grid-template-columns: 620px 1fr;
    }
    @media (min-width: 1600px) {
        grid-template-columns: 720px 1fr;
    }
}
</style>