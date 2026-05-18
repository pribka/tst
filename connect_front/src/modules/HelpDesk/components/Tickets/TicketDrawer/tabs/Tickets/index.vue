<template>
    <div ref="tickets_tab" class="h-full flex flex-col">
        <div class="flex items-center gap-5 mb-3">
            <Segmented 
                v-model="viewType" 
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
        <component 
            :is="taskComponent"
            ref="taskListWidget"
            :ticket="ticket"
            :model="model"
            :actions="actions"
            :page_name="pageName" />
    </div>
</template>

<script>
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        pageName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
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
        excludeFields() {
            return []
        },
        taskComponent() {
            if(this.viewType === 'table')
                return () => import('./Table.vue')
            else
                return () => import('./Kanban.vue')
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.tickets_tab
        }
    }
}
</script>