<template>
    <div ref="wrapperRef" class="h-full flex flex-col">
        <div ref="specialistHeaderWrapper" class="flex items-center justify-between gap-2 mb-2">
            <div class="flex items-center gap-2">
                <a-button v-if="actions?.edit_specialist?.availability" type="primary" @click="addSpecialist()">
                    {{ $t('directories.add_specialist') }}
                </a-button>
                <!-- <PageFilter 
                    :model="listModel"
                    :key="listPageName"
                    size="large"
                    :getPopupContainer="getPopupContainer"
                    :page_name="listPageName" /> -->
            </div>
            <SettingsButton
                key="specialists"
                :pageName="listPageName"
                size="default" />
        </div>
        <SpecialistsAggregate 
            ref="specialistsAggregate"
            :client="client"
            :page="page"
            :listModel="listModel" 
            :listPageName="listPageName" />
        <div class="flex-grow flex flex-col">
            <UniversalTable 
                ref="specTable"
                :model="listModel"
                class="flex-grow"
                :colParams="{
                    actions: actions,
                    client: client,
                    getPopupContainer: getPopupContainerTable
                }"
                :pageName="listPageName"
                tableType="client_specialists"
                :endpoint="`/help_desk/customer_cards/${client.id}/specialists/`"
                @change_page="changePage" />
        </div>
        <SpecialistAddModal :client="client" />
    </div>
</template>

<script>
// import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        // PageFilter,
        SpecialistAddModal: () => import('./components/SpecialistAddModal.vue'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        SpecialistsAggregate: () => import('./components/SpecialistsAggregate.vue')
    },
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            page: 1,
            listModel: "models.CustomerSupportSpecialistModel",
            listPageName: `client_specialists_list_by_${this.client.id}`
        }
    },
    methods: {
        changePage(page) {
            this.page = page
            this.$nextTick(() => {
                if(this.$refs.specialistsAggregate)
                    this.$refs.specialistsAggregate.getList()
            })
        },
        getPopupContainerTable() {
            return this.$refs.wrapperRef
        },
        getPopupContainer() {
            return this.$refs.specialistHeaderWrapper
        },
        addSpecialist() {
            eventBus.$emit('add_specialist_modal')
        }
    }
}
</script>