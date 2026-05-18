<template>
    <div ref="task_tab" :class="isMobile ? '' : 'h-full flex flex-col'">
        <div v-if="!isMobile" class="flex items-center gap-5 mb-3">
            <Segmented 
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
        </div>
        <component 
            :is="taskComponent"
            ref="taskListWidget"
            :ticket="ticket"
            :model="model"
            :actions="actions"
            :page_name="page_name" />
        <div v-if="isMobile" class="float_add">
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="page_name"
                    size="large"
                    :excludeFields="excludeFields"
                    :getPopupContainer="getPopupContainer"
                    :page_name="page_name" />
            </div>
        </div>
    </div> 
</template>

<script>
import Segmented from '@apps/UIModules/Segmented'
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Segmented,
        PageFilter
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
            viewType: 'table',
            listType: [
                {
                    key: 'table',
                    title: this.$t('helpdesk.list')
                },
                {
                    key: 'kanban',
                    title: this.$t('helpdesk.kanban')
                }
            ],
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        excludeFields() {
            if(this.active === 'table')
                return ['sprint__exclude', 'sprint']
            else
                return ['sprint__exclude', 'sprint', 'status__exclude', 'status']
        },
        taskComponent() {
            if(this.isMobile)
                return () => import('./ListView.vue')
            if(this.viewType === 'table')
                return () => import('./Table.vue')
            else
                return () => import('./Kanban.vue')
        }
    },
    methods: {
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
    },
    beforeDestroy() {
        eventBus.$off("TASK_CREATED_task")
    }
}
</script>