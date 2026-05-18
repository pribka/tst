<template>
    <component 
        :is="listComponent" 
        :listProject="listProject" 
        :pageConfig="pageConfig" 
        :tableType="tableType" 
        buttonText="wgr.create_group" 
        page_name="page_list_workgroup_workgroups.WorkgroupModel" />
</template>

<script>
export default {
    props: {
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            listProject: false,
            listComponent: null,
            tableType: 'groups'
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./components/ListInitMobile.vue')
            : () => import('./components/ListInit.vue')
    }
}
</script>

<style lang="scss" scoped>
    .pj_mobile_padding {
        padding: 15px;
    }
</style>