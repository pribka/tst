<template>
    <div class="task_section">
        <p v-if="title" class="mb-2 text-base task_section__title">
            <span class="mr-1">{{ title }}</span>
            <a-tag>{{ count }}</a-tag>
        </p>
        <a-spin :spinning="loading">
            <TaskCard
                v-for="task in list"
                :key="task.id"
                :item="task"
                activeMobile
                showStatus
                :myTaskEnabled="false" />
        </a-spin>
        <div
            v-if="!loading && !list.length"
            class="pt-4">
            <a-empty>
                <template #description>
                    {{ $t('task.task_empty') }}
                </template>
            </a-empty>
        </div>
        <div class="mt-2 flex justify-end">
            <a-pagination
                v-model="page"
                size="small"
                :total="count"
                :pageSize="pageSize"
                hideOnSinglePage
                show-less-items
                @change="getTasks" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        TaskCard: () => import('../../../Kanban/Item.vue')
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        title: {
            type: String,
            default: ''
        },
        pageName: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        queryParams: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            count: 0,
            page: 1,
            pageSize: 15
        }
    },
    created() {
        this.getTasks()
    },
    mounted() {
        eventBus.$on('sprint_update_table_reload', this.reload)
        eventBus.$on(`update_filter_${this.model}_${this.pageName}`, this.reload)
    },
    beforeDestroy() {
        eventBus.$off('sprint_update_table_reload', this.reload)
        eventBus.$off(`update_filter_${this.model}_${this.pageName}`, this.reload)
    },
    methods: {
        reload() {
            this.page = 1
            this.getTasks()
        },
        async getTasks() {
            try {
                this.loading = true
                const params = {
                    ...this.$route.query,
                    ...this.queryParams,
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.pageName,
                    task_type: 'task,stage'
                }
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/tasks_list/`, { params })
                this.list = data?.results || []
                this.count = data?.count || 0
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.task_section{
    &:not(:last-child){
        margin-bottom: 22px;
    }
    &__title{
        color: #000;
    }
}
</style>
