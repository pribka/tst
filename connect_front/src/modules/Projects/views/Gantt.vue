<template>
    <Gant 
        useProjects 
        :pageModel="pageModel"
        :page_name="page_name" />
</template>
  
<script>
export default {
    components: {
        Gant: () => import('@apps/UIModules/Gant/index.vue')
    },
    props: {
        page_name: {
            type: String,
            default: 'page_list_projects.WorkgroupModel'
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        }
    }
}
</script>
  