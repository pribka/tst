<template>
    <div class="task_wrapper">
        <div class="task_full_body_wrapper">
            <taskList
                :tableType="tableType"
                :page_name="page_name"
                :taskType="taskType" 
                :pageConfig="pageConfig">
                <template>
                    <PageFilter 
                        model="tasks.TaskModel"
                        :key="page_name"
                        size="large"
                        :page_name="page_name" />
                </template>
            </taskList>
        </div>
    </div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        taskList: () => import('@apps/vue2TaskComponent/views/Table/Page.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    computed: {
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        routeInfo() {
            return this.getRouteInfo && Object.keys(this.getRouteInfo).length
                ? this.getRouteInfo
                : this.$route.meta || {}
        },
        page_name() {
            return `page_list_${this.taskType}_task.TaskModel`
        },
        taskType() {
            return this.routeInfo?.task_type || 'task'
        },
        tableType() {
            if(this.taskType === 'interest')
                return 'interests'
            if(this.taskType === 'logistic')
                return 'logistic'    
            return 'tasks'

        },
        pageConfig() {
            return this.$route.meta?.pageConfig ? this.$route.meta.pageConfig : null
        }
    }
}
</script>

<style lang="scss" scoped>
.task_full_body_wrapper{
    height: 100%;
}
</style>
