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
                    Создать вопрос-ответ
                </a-button>
            </template>
        </template>
        <Question/>
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Question: () => import("./views/Question.vue"),
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue')
    },
    props: {},
    computed: {
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
            eventBus.$emit('create_question_gos24')
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>