<template>
    <component :is="listComponent" />
</template>

<script>
export default {
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            listComponent: null
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('../components/List.vue')
            : () => import('../components/NewClients/Table.vue')
    }
}
</script>