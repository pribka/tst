<template>
    <ModuleWrapper 
        :pageTitle="pageTitle"
        :bodyPadding="$route.name === 'projects-gant' ? false : true"
        :headerBg="!isMobile">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :model="initPageModel"
                :key="initPageName"
                :popoverMaxWidth="600"
                :excludeFields="excludeFields"
                size="large"
                :page_name="initPageName" />
        </template>
        <template v-slot:h_right>
            <template v-if="isMobile">
                <HelpButton v-if="isSprints" partCode="sprints" type="button" />
                <template v-else>
                    <HelpButton v-if="!isGant" partCode="projects" type="button" />
                </template>
            </template>
            <template v-else>
                <template v-if="isSprints">
                    <a-button 
                        v-if="showCreateButton"
                        class="header__button"
                        icon="fi-rr-plus-small" 
                        flaticon
                        type="primary"
                        @click="addSprint()">
                        {{ $t('project.add_sprint') }}
                    </a-button>
                    <HelpButton partCode="sprints" type="button" class="ml-2" />
                    <component
                        :is="settingsButtonWidget"   
                        :pageName="initPageName"
                        size="default"
                        class="ml-2" />
                </template>
                <template v-else>
                    <a-button 
                        v-if="addButton"
                        class="header__button"
                        icon="fi-rr-plus-small" 
                        flaticon
                        type="primary"
                        @click="createHandler()" >
                        {{ addButton.label ? addButton.label : $t(buttonText) }}
                    </a-button>
                    <a-button 
                        v-if="addTemplateButton && addButton"
                        class="header__button"
                        type="flat_primary"
                        @click="createTemplateHandler()" >
                        {{ addTemplateButton.label ? addTemplateButton.label : $t(templateButtonText) }}
                    </a-button>
                    <template v-if="!isGant">
                        <HelpButton partCode="projects" type="button" class="ml-2" />
                        <component
                            :is="settingsButtonWidget"   
                            :pageName="initPageName"
                            size="default"
                            class="ml-2" />
                    </template>
                </template>
            </template>
        </template>
        <component 
            :is="listComponent" 
            :tableType="tableType" 
            :page_name="page_name"
            :pageModel="pageModel"
            :pageConfig="pageConfig" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue')
    },
    props: {
        tableType: {
            type: String,
            default: 'projects'
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
            default: 'project.add_project'
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
        showCreateButton() {
            return this.getRouteInfo?.pageActions?.add
        },
        isSprints() {
            return this.$route.name === 'projects-sprints' ? true : false
        },
        isGant() {
            return this.$route.name === 'projects-gant' ? true : false
        },
        initPageModel() {
            if(this.$route.name === 'projects-sprints')
                return 'tasks.TaskSprintModel'
            return this.pageModel
        },
        initPageName() {
            if(this.$route.name === 'projects-gant')
                return this.page_name + '_gant'
            if(this.$route.name === 'projects-sprints')
                return this.page_name + '_sprints'
            return this.page_name
        },
        excludeFieldsKey() {
            return this.excludeFields.length ? 'true' : 'false'
        },
        excludeFields() {
            if(this.$route.name === 'projects-gant')
                return ['dead_line', 'dead_line__exclude']
            return []
        },
        currentRoute() {
            if(this.$route.name === 'projects-gant' || this.$route.name === 'projects-list')
                return 'projects'
            return this.$route.name
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
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
            return this.$store.getters['navigation/getRouteInfo'](this.currentRoute)
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
    data() {
        return {
            listComponent: null
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./components/ListInitMobile.vue')
            : () => import('./components/ListInit.vue')
    },
    methods: {
        addSprint() {
            eventBus.$emit('add_sprint')
        },
        createTemplateHandler() {
            const query = {...this.$route.query}
            if(!query.createProjectTemplate) {
                query.createProjectTemplate = true
                this.$router.push({query})
            }
        },
        createHandler() {
            eventBus.$emit('add_proejct_modal')
            /*
            const query = {...this.$route.query}
            if(!query.create_project) {
                query.create_project = true
                this.$router.push({query})
            }*/
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>