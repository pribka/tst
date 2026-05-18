<template>
    <component
        :is="switchComponent" 
        listProject
        :pageModel="pageModel"
        :model="pageModel"
        :tableType="tableType"
        :page_name="page_name" />
</template>

<script>
export default {
    name: 'GroupListInit',
    props: {
        tableType: {
            type: String,
            default: 'groups'
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
        switchComponent() {
            return () => import(/* webpackMode: "lazy" */'./TestTable')
        }
    }
}
</script>