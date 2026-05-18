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
            <a-button
                v-if="showCatalogButton"
                flaticon
                shape="circle"
                icon="fi-rr-menu-burger"
                size="large"
                type="ui"
                class="mb-2"
                ghost
                @click="openCatalogMenu" />
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
            default: 'wgr.create_project'
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
            const routeInfoGetter = this.$store.getters['navigation/getRouteInfo']
            if (this.$route.name === 'directories-groups') {
                return routeInfoGetter('groups') || routeInfoGetter(this.$route.name)
            }
            return routeInfoGetter(this.$route.name)
        },
        addButton() {
            if(this.getRouteInfo?.pageActions?.add) {
                return {
                    label: this.getRouteInfo?.buttonConfig?.label || this.$t(this.buttonText)
                }
            } else
                return null
        },
        showCatalogButton() {
            return this.$route.name === 'directories-groups'
        }
    },
    methods: {
        openCatalogMenu() {
            eventBus.$emit('directories_open_catalog_drawer')
        },
        createHandler() {
            if(this.listProject) {
                this.$router.replace({
                    query: { createProject: true }
                })
            } else {
                this.$router.replace({
                    query: { createGroup: true }
                })
            }
        }
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
