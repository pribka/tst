<template>
    <div class="h-full flex flex-col">
        <HelpDeskCostsMobile
            v-if="isMobile"
            :ticket="ticket"
            :actions="actions" />
        <UniversalTable
            v-else
            :model="model"
            :pageName="page_name"
            tableType="cost_table"
            autoHeight
            rowNumbers
            :params="{
                owner: ticket.id
            }"
            endpoint="/help_desk/costs/"
            taskType="task" />
    </div>
</template>

<script>
export default {
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
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        HelpDeskCostsMobile: () => import('./HelpDeskCostsMobile')
    },
    data() {
        return {
            model: "help_desk.HelpDeskCostModel",
            page_name: "help_desk.HelpDeskCostModel_page"
        }
    },
    computed:{
        isMobile() {
            return this.$store.state.isMobile
        },
    }
}
</script>