<template>
    <DrawerTemplate
        :width="drawerWidth"
        wrapClassName="s_base_drawer"
        v-model="visible"
        disabledBodyPadding
        :showHeader="false"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <component 
            :is="drawerComponent" 
            :initShowLoc="initShowLoc"
            :drawerClose="drawerClose" />
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    computed: {
        windowWidth() { 
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.isMobile)
                return '100%'
            if(this.windowWidth > 1600)
                return 1600
            return '98%'
        },
        drawerComponent() {
            if(this.showContent) {
                if(!this.initShow)
                    return () => import('./Content.vue')
                else
                    return () => import('./InitDrawer.vue')
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
            initShow: true
        }
    },
    watch: {
        '$route.query.help'(val) {
            if(val && !this.visible) {
                if(this.$route.query.sections || this.$route.query.chapters || this.$route.query.pages) {
                    this.initShow = false
                }
                this.visible = true
            }
            if(!val && this.visible) {
                this.visible = false
            }
        },
        '$route.query.sections'(val) {
            if(val && this.initShow) {
                this.initShow = false
            }
        },
        '$route.query.chapters'(val) {
            if(val && this.initShow) {
                this.initShow = false
            }
        },
        '$route.query.pages'(val) {
            if(val && this.initShow) {
                this.initShow = false
            }
        }
    },
    created() {
        if(this.$route.query?.help && !this.visible) {
            if(this.$route.query.sections || this.$route.query.chapters || this.$route.query.pages) {
                this.initShow = false
            }
            this.visible = true
        }
    },
    methods: {
        initShowLoc() {
            this.initShow = true
            const query = {...this.$route.query}
            if(query.help) {
                if(query.chapters)
                    delete query.chapters
                if(query.pages)
                    delete query.pages
                if(query.sections)
                    delete query.sections
                this.$router.push({ query })
            } 
        },
        drawerClose() {
            this.visible = false
        },
        afterVisibleChange(vis) {
            if(!vis) {
                const query = {...this.$route.query}
                if(query.help) {
                    delete query.help 
                    if(query.chapters)
                        delete query.chapters
                    if(query.pages)
                        delete query.pages
                    if(query.sections)
                        delete query.sections
                    this.$router.push({ query })
                } 
                this.initShow = true
            } else {
                
            }
            this.showContent = vis
        }
    },
    mounted() {
        eventBus.$on('open_support_base', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('open_support_base')
    }
}
</script>