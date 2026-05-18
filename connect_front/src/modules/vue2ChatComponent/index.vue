<template>
    <component :is="chat" />
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
            chat: null
        }
    },
    created() {
        this.chat = this.isMobile
            ? () => import('./ChatComponentMobile.vue')
            : () => import('./ChatComponent.vue')
    }
}
</script>