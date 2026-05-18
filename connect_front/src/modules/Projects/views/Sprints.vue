<template>
    <Sprints 
        :showHead="false"
        :pageName="page_name" />
</template>

<script>
export default {
    components: {
        Sprints: () => import('@apps/vue2TaskComponent/components/Sprint/Sprints.vue')
    },
    props: {
        page_name: {
            type: String,
            required: true
        }
    }
}
</script>