<template>
    <component 
        :is="listComponent" 
        :tableType="tableType" 
        :page_name="page_name"
        :pageModel="pageModel"
        :pageConfig="pageConfig" />
</template>

<script>
export default {
    props: {
        pageConfig: {
            type: Object,
            default: () => null
        },
        page_name: {
            type: String,
            default: 'page_list_projects.WorkgroupModel'
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            listComponent: null,
            listProject: true,
            tableType: 'projects'
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('../components/ListInitMobile.vue')
            : () => import('../components/ListInit.vue')
    }
}
</script>