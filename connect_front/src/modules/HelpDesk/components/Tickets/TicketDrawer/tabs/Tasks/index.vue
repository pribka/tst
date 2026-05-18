<template>
    <div ref="task_tab" class="h-full flex flex-col">
        <div class="flex items-center gap-5 mb-3">
            <Segmented
                v-if="!isMobile"
                v-model="viewType"
                bgInvert
                :options="listType" />
            <PageFilter
                :model="model"
                :key="page_name"
                size="large"
                :excludeFields="excludeFields"
                :getPopupContainer="getPopupContainer"
                :page_name="page_name" />
            <a-button
                v-if="actions?.create_task?.availability"
                type="primary"
                @click="addTask">
                {{$t('task.add_task')}}
            </a-button>
        </div>
        <TaskList
            v-if="isMobile"
            ref="taskListWidget"
            main
            extendDrawer
            showFilter
            :isScroll="true"
            :model="model"
            tableType="tasks"
            :showAddButton="actions?.create_task?.availability"
            :pageName="page_name"
            :minVh="isMobile"
            :columnNameWidth="200"
            :pageConfig="pageConfig"
            :hash="false"
            bgInvert
            forceMobile
            :actionFix="false"
            :formParams="formParams"
            :queryParams="queryParams"
            :name="`tickets_${ticket.id}`">
        </TaskList>
        <template v-else>
            <component
                :is="taskComponent"
                ref="taskListWidget"
                :ticket="ticket"
                :model="model"
                :actions="actions"
                :page_name="page_name" />
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        PageFilter: () => import('@/components/PageFilter'),
        TaskList: () => import('@apps/vue2TaskComponent/components/TaskList/TaskList'),
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            model: "tasks.TaskModel",
            page_name: `tasks.TaskModel.Tickets_${this.ticket.id}`,

            // для десктопа (как было)
            viewType: 'table',
            listType: [
                { key: 'table', title: this.$t('helpdesk.list') },
                { key: 'kanban', title: this.$t('helpdesk.kanban') }
            ],

            // для TaskList (мобилка)
            formParams: {
                reason: this.ticket.id,
                create_handler: `tasks.TaskModel.Tickets_${this.ticket.id}`
            },
            queryParams: {},
            pageConfig: {
                showFilter: true
            }
        }
    },
    computed: {
        excludeFields() {
            if (this.active === 'table')
                return ['sprint__exclude', 'sprint']
            else
                return ['sprint__exclude', 'sprint', 'status__exclude', 'status']
        },
        taskComponent() {
            if (this.viewType === 'table')
                return () => import('./Table.vue')
            else
                return () => import('./Kanban.vue')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    created() {
        // фильтр задач по обращению (reason)
        this.queryParams = { filters: { reason: this.ticket.id } }
        this.queryParams['page_name'] = this.page_name
    },
    methods: {
        getPopupContainer() {
            return this.$refs.task_tab
        },
        addTask() {
            const form = {
                reason: this.ticket.id,
                create_handler: this.page_name,
            }
            this.$store.commit('task/SET_TASK_TYPE', 'task')
            this.$store.commit('task/SET_PAGE_NAME', { pageName: this.page_name })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', { type: 'add_task', data: form })
        }
    },
    mounted() {
        eventBus.$on(`TASK_CREATED_task_${this.page_name}`, () => {
            this.$nextTick(() => {
                if (this.$refs.taskListWidget && this.$refs.taskListWidget.updateData) {
                    this.$refs.taskListWidget.updateData()
                }
            })
        })
        eventBus.$on(`update_filter_${this.page_name}`, () => {
            this.$nextTick(() => {
                if (this.$refs.taskListWidget && this.$refs.taskListWidget.updateData) {
                    this.$refs.taskListWidget.updateData()
                }
            })
        })
    },
    beforeDestroy() {
        eventBus.$off(`TASK_CREATED_task_${this.page_name}`)
        eventBus.$off(`update_filter_${this.page_name}`)
    }
}
</script>
