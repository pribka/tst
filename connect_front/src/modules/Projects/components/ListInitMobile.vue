<template>
    <div class="pj_mobile_padding">
        <component 
            :is="switchComponent" 
            :listProject="listProject"
            :pageModel="pageModel"
            :model="pageModel"
            :tableType="tableType"
            :page_name="page_name" />
        <div class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :model="pageModel"
                    :key="page_name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <!--<a-button 
                flaticon
                shape="circle"
                class="mb-3"
                size="large"
                icon="fi-rr-arrows-repeat"
                @click="openSprintPage()" />
            <a-button 
                v-if="addTemplateButton && addButton"
                flaticon
                shape="circle"
                class="mb-3"
                size="large"
                icon="fi-rr-layer-plus"
                @click="createTemplateHandler()" />-->
            <a-button 
                v-if="addButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="createHandler()" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'GroupListInit',
    components: {
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        templateButtonText: {
            type: String,
            default: 'project.templates'
        },
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
            default: 'project.create_project'
        },
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        switchComponent() {
            return () => import(/* webpackMode: "lazy" */'./List')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        createButton() {
            return this.pageConfig?.headerButtons?.createButton || null
        },
        getRouteInfo() {
            return this.$store.state.navigation.routerList.find(item => item.name === 'projects')
        },
        addButton() {
            if(this.getRouteInfo?.pageActions?.add) {
                return {
                    label: this.getRouteInfo?.buttonConfig?.label || this.$t(this.buttonText)
                }
            } else
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
        openSprintPage() {
            this.$router.push({
                name: 'projects-sprints'
            })
        },
        createHandler() {
            eventBus.$emit('add_proejct_modal')
        },

        createTemplateHandler() {
            this.$router.replace({
                query: { createProjectTemplate: true }
            })
        },
    }
}
</script>

<style lang="scss" scoped>
.list_group_header {
    margin-top: -10px;
    padding-top: 10px;
    padding-bottom: 10px;
    top: var(--headerHeight);
    background: var(--eBg);
}
</style>
