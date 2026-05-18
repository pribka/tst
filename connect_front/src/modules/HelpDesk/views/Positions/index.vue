<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable 
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            tableType="helpdesk_positions"
            :endpoint="endpoint" />
        <PositionFormModal :model="initPageModel" contractorSelect />
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        PositionFormModal: () => import('../../components/PositionFormModal.vue')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        }
    },
    data() {
        return {
            endpoint: "/help_desk/contact_person_post/"
        }
    }
}
</script>