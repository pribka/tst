<template>
    <TaskList
        main
        extendDrawer
        showFilter
        :isScroll="true"
        model="tasks.TaskModel"
        tableType="tasks"
        :showAddButton="false"
        :pageName="pageName"
        :minVh="isMobile"
        :columnNameWidth="200"
        :pageConfig="pageConfig"
        :hash="false"
        bgInvert
        forceMobile
        :actionFix="false"
        :formParams="formParams"
        :queryParams="queryParams"
        :name="`chat_${id}`">
        <PageFilter 
            model="tasks.TaskModel"
            :key="pageName"
            size="large"
            :zIndex="2000"
            placement="bottomRight"
            :excludeFields="excludeFields"
            :page_name="pageName"/>
    </TaskList>
</template>

<script>
export default {
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        activeChat: {
            type: Object,
            default: () => {}
        }
    },
    components: {
        TaskList: () => import('@apps/vue2TaskComponent/components/TaskList/TaskList'),
        PageFilter: () => import('@/components/PageFilter')
    },
    computed:{
        isMobile() {
            return this.$store.state.isMobile
        },
        pageName() {
            return `tasks.chat_${this.id}`
        }
    },
    created(){
        this.queryParams = {filters: {message_share__chat: this.id}}
        this.queryParams['page_name'] = this.pageName
        //this.excludeFields = ['workgroup']
        this.render = true
    },
    methods: {
        getPopupContainer(trigger) {
            return trigger.parentNode
        }
    },
    data(){
        return{
            formParams: {
                reason: this.id
            },
            queryParams: {},
            excludeFields: [],
            // page_name: "tasks.groups_and_project",
            render: false,
            pageConfig: {
                showFilter: true
            }
        }
    }
}
</script>