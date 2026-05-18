<template>
    <div ref="wrapperRef" class="h-full flex flex-col">
        <div ref="specialistHeaderWrapper" class="flex items-center justify-between gap-2 mb-2">
            <div class="flex items-center gap-2">
                <a-button
                    v-if="actions?.create_contact_person?.availability"
                    type="primary"
                    @click="addContact()">
                    {{ $t('helpdesk.add_contact_person') }}
                </a-button>
                <PageFilter
                    :model="listModel"
                    :key="listPageName"
                    size="large"
                    :getPopupContainer="getPopupContainer"
                    :page_name="listPageName" />
            </div>
            <SettingsButton
                key="contact_person"
                :pageName="listPageName"
                size="default" />
        </div>
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
                tableType="contact_person"
                :endpoint="endpoint"
                @change_page="changePage" />
        </div>
        <ContactModal :contractor="client.org_admin ? client.org_admin.id : null" slaSelect />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ContactModal: () => import('../../ContactModal.vue')
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
            listModel: "help_desk.ContactPersonModel",
            listPageName: `helpdesk_contact_person_by_${this.client.id}`
        }
    },
    computed: {
        endpoint() {
            return `help_desk/customer_cards/${this.client.id}/contact_persons/`
        }
    },
    methods: {
        addContact() {
            eventBus.$emit("add_ticket_contact", this.client.id);
        },

        changePage(page) {
            this.page = page
            this.$nextTick(() => {
                // if(this.$refs.specialistsAggregate)
                //     this.$refs.specialistsAggregate.getList()
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