<template>
    <ModuleWrapper
        class="gos24"
        pageTitle="GOS24"
        :headerBg="!isMobile"
        :pageRoutes="routes">
        <router-view/>
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'
import eventBus from '@/utils/eventBus'
// import Articles from "@/views/Dashboard/PageWidgets/Articles.vue";
export default {
    components: {
        // Articles,
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
            if (this.currentRoute === 'articles'){
                eventBus.$emit('create_article_gos24')
            }else if(this.currentRoute === 'official'){
                eventBus.$emit('create_official_gos24')
            }else if(this.currentRoute === 'webinar'){
                eventBus.$emit('create_webinar_gos24')
            }else if(this.currentRoute === 'question'){
                eventBus.$emit('create_question_gos24')
            }else if(this.currentRoute === 'knowledgebase'){
                eventBus.$emit('create_knowledgebase_gos24')
            }else if(this.currentRoute === 'partition'){
                eventBus.$emit('create_partition_gos24')
            }else if(this.currentRoute === 'organ'){
                eventBus.$emit('create_organ_gos24')
            }else if(this.currentRoute === 'tag'){
                eventBus.$emit('create_tag_gos24')
            }else if(this.currentRoute === 'news'){
                eventBus.$emit('create_news_gos24')
            }else if(this.currentRoute === 'news_finance'){
                eventBus.$emit('create_news_finance')
            }

        }
    }
}
</script>

<style lang="scss">
.gos24{
    .header__button + .header__button {
        margin-left: 10px;
    }

}
.task_form_wrap {
    .ck-editor__top{
        position: sticky !important;
        top: -20px !important;
        background: white !important;
        z-index: 1;
    }
    blockquote {
        overflow: hidden !important;
        // font-weight: 300;
        border-left: 5px solid #008261 !important;
        background-color: rgba(34, 155, 125, 0.18) !important;
        padding: 10px 1.2em !important;
        margin: 4px 0 !important;

        ul, ol {
            padding-left: 1rem !important;
            font-family: "Montserrat", sans-serif !important;
        }
    }
}
</style>
