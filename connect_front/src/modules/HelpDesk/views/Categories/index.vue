<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable 
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            tableType="helpdesk_categories_page"
            :endpoint="endpoint" />
        <ModalCategoryCreate :model="initPageModel" contractorSelect />
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        ModalCategoryCreate: () => import('../../components/ModalCategoryCreate.vue')
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
            endpoint: "/help_desk/ticket_categories/"
        }
    }
}
</script>