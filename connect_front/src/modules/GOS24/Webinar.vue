<template>
    <ModuleWrapper
        pageTitle="GOS24"
        :headerBg="!isMobile"
        :pageRoutes="routes">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :popoverMaxWidth="600"
                size="large"/>
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <template>
                <a-button
                    class="header__button"
                    icon="plus"
                    size="large"
                    type="primary"
                    @click="createHandler()" >
                    Создать вебинар
                </a-button>
            </template>
        </template>
        <Webinar/>
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Webinar: () => import("./views/Webinar.vue"),
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue')
    },
    props: {},
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
            eventBus.$emit('create_webinar_gos24')
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>