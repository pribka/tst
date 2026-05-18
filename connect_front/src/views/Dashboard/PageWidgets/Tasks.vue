<template>
    <div :class="!isMobile && 'task_wrapper'">
        <div :class="!isMobile && 'task_full_body_wrapper h-full'">
            <taskList
                :taskType="taskType" 
                showPageTitle
                :page_name="page_name" 
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
import { mapState } from 'vuex'
export default {
    mixins: [pageMeta],
    components: {
        taskList: () => import('@apps/vue2TaskComponent/views/Table/Page.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    computed: {
        ...mapState({
            viewType: state => state.task.mobileViewType
        }),
        isMobile() { 
            return this.$store.state.isMobile
        },
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        page_name() {
            return `page_list_${this.taskType}_task.TaskModel`
        },
        pageConfig() {
            return this.$route.meta?.pageConfig ? this.$route.meta.pageConfig : null
        }
    },
    data() {
        return {
            taskType: 'task,stage'
        }
    },
    created() {
        this.taskType = this.getRouteInfo?.task_type || 'task,stage'
    }
}
</script>