<template>
    <div class="task_wrapper">
        <div class="task_full_body_wrapper">
            <TaskKanban
                :taskType="taskType" 
                :pageConfig="pageConfig">
                <template>
                    <PageFilter 
                        model="tasks.TaskModel"
                        :key="page_name"
                        size="large"
                        :page_name="page_name"
                        :excludeFields="['status']" />
                </template>
            </TaskKanban>
        </div>
    </div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        TaskKanban: () => import('@apps/vue2TaskComponent/views/Kanban/index.vue'),
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
            return `page_kanban_${this.taskType}_tasks.TaskModel`
        },
        taskType() {
            return this.routeInfo?.task_type || 'task'
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
