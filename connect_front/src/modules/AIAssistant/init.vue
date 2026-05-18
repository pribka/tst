<template>
    <component :is="drawerAsync" v-if="$route.query.ai_chat" />
</template>

<script>
import store from './store/index'

export default {
    name: 'AiInit',
    data() {
        return {
            drawerAsync: null
        }
    },
    watch: {
        '$route.query.ai_chat': {
            immediate: true,
            handler(v) {
                if (v && !this.drawerAsync)
                    this.drawerAsync = () => import('./Drawer/index.vue')
            }
        }
    },
    beforeCreate() {
        if (!this.$store.hasModule('ai'))
            this.$store.registerModule('ai', store)
    }
}
</script>
