<template>
    <div>
        <component :is="approvalsDrawerAsync" v-if="$route.query.approvals" />
        <AddDrawer />
    </div>
</template>

<script>
export default {
    components: {
        AddDrawer: () => import('./AddDrawer/index.vue')
    },
    data() {
        return {
            approvalsDrawerAsync: null,
        }
    },
    watch: {
        '$route.query.approvals': {
            immediate: true,
            handler(v) {
                if (v && !this.approvalsDrawerAsync)
                    this.approvalsDrawerAsync = () => import(/* webpackPrefetch: true, webpackChunkName: "approvals-show-drawer" */ './ViewDrawer/index.vue')
            }
        }
    },
}
</script>