<template>
    <div 
        ref="task_tab" 
        class="task_tab flex-grow flex flex-col min-h-0">
        <div v-if="!isMobile" class="flex items-center justify-between pb-4 task_head">
            <div class="flex items-center gap-2">
                <Segmented 
                    v-model="active" 
                    bgInvert
                    :options="listType" />
                <PageFilter 
                    :model="model"
                    :key="pageName"
                    size="large"
                    :excludeFields="excludeFields"
                    :getPopupContainer="getPopupContainer"
                    :page_name="pageName" />
            </div>
            <div class="flex items-center">
                <a-button 
                    v-if="actions && actions.set_task && actions.set_task.availability && sprint.status !== 'completed'"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-plus-small"
                    @click="addTask()">
                    {{ $t('task.add_tasks') }}
                </a-button>
                <!-- <SettingsButton
                    v-if="active === 'table'"
                    :pageName="pageName"
                    class="ml-2"
                    size="default"
                    :zIndex="1200" /> -->
            </div>
        </div>
        <template v-if="active === 'table'">
            <component
                :is="taskComponent"
                :sprint="sprint"
                :actions="actions"
                :pageName="pageName"
                :page_name="pageName"
                :model="model" />
            <div 
                v-if="isMobile"
                class="float_add">
                <div class="filter_slot">
                    <PageFilter 
                        :model="model"
                        :key="pageName"
                        size="large"
                        :excludeFields="excludeFields"
                        :getPopupContainer="getPopupContainer"
                        :page_name="pageName" />
                </div>
                <a-button 
                    v-if="actions && actions.set_task && actions.set_task.availability && sprint.status !== 'completed'"
                    flaticon
                    shape="circle"
                    size="large"
                    type="primary"
                    icon="fi-rr-plus"
                    @click="addTask()"  />
            </div>
        </template>
        <div 
            v-if="active === 'kanban'" 
            class="sprint_kanban_wrapp flex-grow min-h-0">
            <Kanban 
                :implementId="sprint.id"
                :formParams="formParams"
                :showAddButton="false"
                :extendDrawer="true"
                :useScrollDummy="false"
                taskType="task"
                :queryParams="queryParams"
                implementType="sprint">
            </Kanban>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        Kanban: () => import('@apps/vue2TaskComponent/components/Kanban'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        changeActive: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            model: 'tasks.TaskModel',
            active: 'table',
            formParams: {},
            listType: [
                {
                    key: 'table',
                    title: this.$t('task.list')
                },
                {
                    key: 'kanban',
                    title: this.$t('task.kanban')
                }
            ],
            queryParams: {
                page_name: this.pageName
            }
        }
    },
    computed: {
        excludeFields() {
            if(this.active === 'table')
                return ['sprint__exclude', 'sprint']
            else
                return ['sprint__exclude', 'sprint', 'status__exclude', 'status']
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        taskComponent() {
            if(this.isMobile)
                return () => import('./TaskCardSectionList.vue')
            return () => import('./TaskTableList.vue')
        }
    },
    methods: {
        setActive(active) {
            this.active = active
            this.changeActive(active)
        },
        addTask() {
            eventBus.$emit('sprint_add_task', this.sprint.id)
        },
        getPopupContainer() {
            return this.$refs.task_tab
        },
        tableReload() {
            /*if(this.active === 2)
                eventBus.$emit(`RELOAD_COLUMN_FROM_${this.sprint.id}`)*/
            this.$nextTick(() => {
                if(this.$refs.taskListWidget)
                    this.$refs.taskListWidget.tableReload()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.sprint_kanban_wrapp {
    min-height: 0;
    height: calc(100% - 50px);
}
</style>
