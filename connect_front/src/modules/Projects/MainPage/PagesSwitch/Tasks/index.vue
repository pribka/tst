<template>
    <div ref="task_tab" :class="!isMobile && 'h-full flex flex-col'">
        <div v-if="!isMobile" class="flex items-center gap-2 pb-2">
            <a-button v-if="actions && actions.create_task && actions.create_task.availability" type="primary" @click="addTask()">
                {{ $t('task.add_task') }}
            </a-button>
            <PageFilter 
                :model="model"
                :key="viewType"
                size="large"
                :excludeFields="excludeFields"
                :getPopupContainer="getPopupContainer"
                :page_name="page_name" />
        </div>
        <div v-if="!isMobile" class="flex items-center justify-between gap-3 pb-3">
            <div class="flex items-center gap-3">
                <Segmented 
                    v-model="viewType" 
                    bgInvert
                    :options="listType" />
                <StatusFilters 
                    :page_name="page_name" 
                    bgInvert
                    :queryParams="{
                        filters: {
                            project: id
                        }
                    }"
                    :model="model" />
            </div>
            <SettingsButton
                v-if="viewType === 'table'"
                :pageName="page_name"
                size="default"
                class="ml-2 flex items-center justify-center" />
        </div>
        <component 
            :is="taskComponent"
            ref="taskListWidget"
            :id="id"
            :model="model"
            :actions="actions"
            :page_name="page_name" />
        <div v-if="isMobile" class="float_add">
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="viewType"
                    size="large"
                    :excludeFields="excludeFields"
                    :getPopupContainer="getPopupContainer"
                    :page_name="page_name" />
            </div>
            <a-button 
                v-if="actions && actions.create_task && actions.create_task.availability" 
                type="primary" 
                flaticon
                size="large"
                shape="circle"
                icon="fi-rr-plus"
                @click="addTask()" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        PageFilter: () => import('@/components/PageFilter'),
        StatusFilters: () => import('@apps/vue2TaskComponent/components/TaskList/StatusFilters.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        isStudent: {
            type: Boolean,
            default: false
        },
        isFounder: {
            type: Boolean,
            default: false
        },
        actions: {
            type: Object,
            default: () => null
        },
        requestData: {
            type: Object,
            default: () => {}
        }
    },
    data() {
        return {
            model: "tasks.TaskModel",
            page_name: `tasks.project_${this.id}`,
            viewType: 'table',
            listType: [
                {
                    key: 'table',
                    title: 'Список'
                },
                {
                    key: 'kanban',
                    title: 'Канбан'
                }
            ],
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        excludeFields() {
            if(this.viewType === 'table')
                return ['project__exclude', 'project']
            else
                return ['project__exclude', 'project', 'status__exclude', 'status']
        },
        taskComponent() {
            if(this.viewType === 'table') {
                if(this.isMobile)
                    return () => import('../../../components/ProjectTaskTable/ListView.vue')
                else
                    return () => import('./Table.vue')
            } else
                return () => import('./Kanban.vue')
        }
    },
    methods: {
        addTask() {
            const data = {
                project: {
                    name: this.requestData.name, 
                    id: this.id,
                    workgroup_logo: this.requestData.workgroup_logo?.is_image ? this.requestData.workgroup_logo : null,
                    date_start_plan: this.requestData.date_start_plan,
                    dead_line: this.requestData.dead_line
                }
            }
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.page_name
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'add_task', data })
        },
        getPopupContainer() {
            return this.$refs.task_tab
        }
    },
    mounted() {
        eventBus.$on("TASK_CREATED_task", () => {
            this.$nextTick(() => {
                this.$refs.taskListWidget.updateData()
            })
        })
        eventBus.$on("TASK_CREATED_milestone", () => {
            this.$nextTick(() => {
                this.$refs.taskListWidget.updateData()
            })
        })
        eventBus.$on("TASK_CREATED_stage", () => {
            this.$nextTick(() => {
                this.$refs.taskListWidget.updateData()
            })
        })
    },
    beforeDestroy() {
        eventBus.$off("TASK_CREATED_task")
        eventBus.$off("TASK_CREATED_milestone")
        eventBus.$off("TASK_CREATED_stage")
    }
}
</script>