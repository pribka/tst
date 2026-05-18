<template>
    <div>
        <component :is="groupShowDrawerAsync" v-if="$route.query.viewGroup" :isProject="false" />
        <component :is="groupShowDrawerCreateAsync" v-if="$route.query.createGroup || $route.query.updateGroup" />

        <CreateModal />
    </div>
</template>

<script>
import store from "./store/index"
export default {
    name: "GroupsInit",
    components: {
        CreateModal: () => import('./CreateModal.vue')
    },
    data() {
        return {
            groupShowDrawerAsync: null,
            groupShowDrawerCreateAsync: null,
            buttonSize: 'large'
        }
    },
    watch: {
        '$route.query.viewGroup': {
            immediate: true,
            handler(v) {
                if (v && !this.groupShowDrawerAsync)
                    this.groupShowDrawerAsync = () => import(/* webpackChunkName: "group-show-drawer" */ './MainPage/index.vue')
            }
        },
        '$route.query.createGroup': {
            immediate: true,
            handler(v) {
                if (v && !this.groupShowDrawerCreateAsync)
                    this.groupShowDrawerCreateAsync = () => import(/* webpackChunkName: "create-show-drawer" */ './CreateGroup')
            }
        },
        '$route.query.updateGroup': {
            immediate: true,
            handler(v) {
                if (v && !this.groupShowDrawerCreateAsync)
                    this.groupShowDrawerCreateAsync = () => import(/* webpackChunkName: "create-show-drawer" */ './CreateGroup')
            }
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    created() {
        if(!this.$store.hasModule('workgroups')) {
            this.$store.registerModule("workgroups", store)
            this.$store.commit('ADD_CONNECTED_MODULES', 'workgroups')
        }
    }
}
</script>