<template>
    <Kanban 
        :formParams="formParams"
        :showAddButton="false"
        :extendDrawer="true"
        :useScrollDummy="false"
        taskType="task"
        :page_name="page_name"
        :queryParams="queryParams"
        implementType="tickets" />
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Kanban: () => import('@apps/vue2TaskComponent/components/Kanban')
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
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            formParams: {},
            queryParams: {
                page_name: this.page_name,
                filters: { reason: this.ticket.id }
            }
        }
    },
    methods: {
        updateData() {
            eventBus.$emit(`update_filter_data_${this.page_name}`)
        }
    }
}
</script>