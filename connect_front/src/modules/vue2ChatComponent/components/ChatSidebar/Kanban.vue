<template>
    <Kanban 
        :implementId="id"
        implementType="message_share__chat"
        :formParams="formParams"
        :pageConfig="pageConfig"
        :queryParams="queryParams">
        <PageFilter 
            model="tasks.TaskModel"
            :key="pageName"
            size="large"
            :page_name="pageName"/>
    </Kanban>
</template>

<script>
export default {
    props: {
        id: {
            type: [String, Number],
            required: true
        }
    },
    components: {
        Kanban: () => import('@apps/vue2TaskComponent/components/Kanban'),
        PageFilter: () => import('@/components/PageFilter')
    },
    computed:{
        pageName() {
            return `tasks.chat_${this.id}`
        }
    },
    created() {
        this.queryParams['page_name'] = this.pageName
    },
    data() {
        return{
            formParams: {},
            queryParams: {},
            excludeFields: ['status'],
            // page_name: "tasks.groups_and_project",
            pageConfig: {
                showFilter: true
            }
        }
    }
}
</script>