<template>
    <SprintsList 
        :showPageTitle="showPageTitle">
        <slot />
    </SprintsList>
</template>

<script>
import '../../assets/main.scss'
export default {
    components: {
        SprintsList: () => import('../../components/Sprint/Sprints.vue')
    },
    props: {
        showPageTitle: {
            type: Boolean,
            default: false
        }
    }
}
</script>
