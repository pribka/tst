<template>
    <div>
        <component :is="projectShowDrawerAsync" v-if="$route.query.viewProject" isProject />
        <component :is="projectShowDrawerCreateAsync" v-if="isMobile && projectShowDrawerCreateAsync" />
        <component :is="projectTemplateShowDrawerAsync" v-if="$route.query.createProjectTemplate" />

        <CreateModal v-if="!isMobile" />
    </div>
</template>

<script>
import store from "./store/index"
export default {
    name: "ProjectsInit",
    components: {
        CreateModal: () => import('./CreateModal.vue')
    },
    data() {
        return {
            projectShowDrawerAsync: null,
            projectTemplateShowDrawerAsync: null,
            projectShowDrawerCreateAsync: null,
            buttonSize: 'large'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        '$route.query.viewProject': {
            immediate: true,
            handler(v) {
                if (v && !this.projectShowDrawerAsync)
                    this.projectShowDrawerAsync = () => import(/* webpackChunkName: "project-show-drawer" */ './MainPage/index.vue')
            }
        },
        isMobile: {
            immediate: true,
            handler(v) {
                if (v && !this.projectShowDrawerCreateAsync)
                    this.projectShowDrawerCreateAsync = () => import(/* webpackChunkName: "project-create-drawer" */ "./ProjectCreate.vue")
            }
        },
        '$route.query.createProjectTemplate': {
            immediate: true,
            handler(v) {
                if (v && !this.projectTemplateShowDrawerAsync)
                    this.projectTemplateShowDrawerAsync = () => import(/* webpackChunkName: "project-template-drawer" */ './CreateProjectTemplate')
            }
        }
    },
    created() {
        if(!this.$store.hasModule('projects')) {
            this.$store.registerModule("projects", store)
            this.$store.commit('ADD_CONNECTED_MODULES', 'projects')
        }
    }
}
</script>
