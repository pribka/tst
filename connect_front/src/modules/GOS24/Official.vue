<template>
    <Official/>
</template>

<script>
import routes from './config/router.js'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Official: () => import("./views/Official.vue"),
    },
    props: {
        tableType: {
            type: String,
            default: 'articles'
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        page_name: {
            type: String,
            default: 'page_list_projects.WorkgroupModel'
        },
        buttonSize: {
            type: String,
            default: 'large'
        },
        buttonText: {
            type: String,
            default: 'create'
        },
        templateButtonText: {
            type: String,
            default: 'project.templates'
        },
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        currentRoute() {
            if(this.$route.name === 'gos24')
                return 'articles'
            return this.$route.name
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    data() {
        return {
            routes
        }
    },
    methods: {
        createHandler() {
            eventBus.$emit('create_official_gos24')
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>