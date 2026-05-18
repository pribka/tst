<template>
    <ModuleWrapper :pageTitle="pageTitle">
        <template v-slot:h_left>
            <PageFilter
                :model="pageModel"
                :key="page_name"
                size="large"
                :popoverMaxWidth="600"
                :page_name="page_name" />
        </template>
        <template v-slot:h_right>
            <a-button 
                v-if="addButton"
                class="header__button"
                icon="fi-rr-plus-small" 
                flaticon
                type="primary"
                @click="createHandler()" >
                {{ addButton.label ? addButton.label : $t(this.buttonText) }}
            </a-button>
            <HelpButton partCode="groups" type="button" class="ml-2" />
            <component
                :is="settingsButtonWidget"   
                :pageName="page_name"
                size="default"
                class="ml-2" />
        </template>
        <component 
            :is="switchComponent" 
            :listProject="listProject"
            :pageModel="pageModel"
            :model="pageModel"
            :tableType="tableType"
            :page_name="page_name" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'GroupListInit',
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        tableType: {
            type: String,
            default: 'groups'
        },
        listProject: {
            type: Boolean,
            default: true
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        page_name: {
            type: String,
            default: 'page_list_project_workgroups.WorkgroupModel'
        },
        buttonSize: {
            type: String,
            default: 'large'
        },
        buttonText: {
            type: String,
            default: 'wgr.add_project'
        },
        templateButtonText: {
            type: String,
            default: 'wgr.templates'
        },
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        switchComponent() {
            return () => import(/* webpackMode: "lazy" */'./TestTable')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        createButton() {
            return this.pageConfig?.headerButtons?.createButton || null
        },
        getRouteInfo() {
            const routeInfoGetter = this.$store.getters['navigation/getRouteInfo']
            if (this.$route.name === 'directories-groups') {
                return routeInfoGetter('groups') || routeInfoGetter(this.$route.name)
            }
            return routeInfoGetter(this.$route.name)
        },  
        addButton() {
            if(this.getRouteInfo?.pageActions?.add) 
                return {
                    label: this.getRouteInfo?.buttonConfig?.label || this.$t(this.buttonText)
                }
            return null
        },
        addTemplateButton() {
            if(this.getRouteInfo?.pageActions?.addTemplate) 
                return {
                    label: this.getRouteInfo?.templateButtonConfig?.label || this.$t(this.templateButtonText)
                }
            return null
        }
    },
    methods: {
        createTemplateHandler() {
            if(this.listProject) {
                this.$router.replace({
                    query: { createProjectTemplate: true }
                })
            }
        },
        createHandler() {
            eventBus.$emit('add_workgroup_modal')
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>
