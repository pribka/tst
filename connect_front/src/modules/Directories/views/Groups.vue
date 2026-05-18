<template>
    <Groups />
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'DirectoriesGroupsView',
    components: {
        Groups: () => import('@apps/Groups/index.vue')
    },
    created() {
        this.loadRouteMeta()
    },
    methods: {
        async loadRouteMeta() {
            try {
                await this.$store.dispatch('navigation/getRouteActions', {
                    name: 'groups'
                })
                await this.$store.dispatch('navigation/getRouterInfo', {
                    name: 'groups'
                })
            } catch (error) {
                errorHandler({ error, show: false })
            }
        }
    }
}
</script>
