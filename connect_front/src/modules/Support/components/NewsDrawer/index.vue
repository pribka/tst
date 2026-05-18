<template>
    <DrawerTemplate
        title=""
        :width="isMobile ? '100%' : 700"
        class="news_drawer"
        v-model="visible"
        :zIndex="9999"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <component 
            :is="drawerComponent" 
            :key="listVersion"
            :drawerClose="drawerClose" />
        <template #footer>
            <a-button type="ui_ghost" size="large" block @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    computed: {
        drawerComponent() {
            if(this.showContent) {
                if(!this.initShow)
                    return null
                else
                    return () => import('./NewsList.vue')
            } else
                return null
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
            showContent: false,
            initShow: true,
            listVersion: 0
        }
    },
    methods: {
        drawerClose() {
            this.visible = false
        },
        afterVisibleChange(vis) {
            if(!vis) {
                const query = {...this.$route.query}
                if(query.newList) {
                    delete query.newList
                    this.$router.push({ query })
                } 
                this.initShow = true
            } else {
                
            }
            this.showContent = vis
        },
        reloadNewsList() {
            this.listVersion += 1
        }
    },
    watch: {
        '$route.query.newList': {
            immediate: true,
            handler(val) {
                if(val && !this.visible) {
                    this.visible = true
                }
                if(!val && this.visible) {
                    this.visible = false
                }
            }
        }
    },
    created() {
        eventBus.$on('support_news_list_reload', this.reloadNewsList)
    },
    beforeDestroy() {
        eventBus.$off('support_news_list_reload', this.reloadNewsList)
    }
}
</script>

<style lang="scss" scoped>
.news_drawer{
    &::v-deep{
        .drawer_header{
            display: none!important;
        }
        .drawer_body.padding{
            padding: 0px!important;
        }
    }
}
</style>
