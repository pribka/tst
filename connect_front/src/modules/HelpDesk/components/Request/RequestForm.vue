<template>
    <a-modal
        :width="575"
        :afterClose="afterClose"
        :visible="visible"
        destroyOnClose
        :title="$t('helpdesk.create_ticket')"
        @afterVisibleChange="afterVisibleChange"
        wrapClassName="ticket_request_form_modal body_top_pd"
        @cancel="visible = false">
        <a-form-model
            ref="ruleForm"
            :model="form"
            class="mini_form mt-2"
            :rules="rules">
            <a-form-model-item ref="name" label="" prop="name">
                <a-input
                    v-model="form.name"
                    inputType="ghost"
                    noXPadding
                    :placeholder="$t('helpdesk.enter_name')"
                    @pressEnter="formSubmit()">
                    <template #prefix>
                        <i class="fi fi-rr-pencil" />
                    </template>
                </a-input>
            </a-form-model-item>
            <a-form-model-item ref="description" label="" prop="description">
                <div class="w-full description_editor bg-neutral-1 z-10 relative px-4 py-3 rounded-xl relative">
                    <component
                        v-if="editorGate"
                        ref="descEditor"
                        :is="ckEditor"
                        :taskId="form.id || null"
                        :placeholder="$t('helpdesk.ticket_description')"
                        :key="visible"
                        v-model="form.description"
                        @onReady="onEditorReady"/>
                </div>
            </a-form-model-item>
            <a-form-model-item v-if="plannerMode" ref="customer_card" label="" prop="customer_card">
                <DSelect
                    v-model="form.customer_card"
                    apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                    class="w-full"
                    ref="customerCardSelect"
                    infinity
                    size="default"
                    resultsKey="filteredSelectList"
                    inputType="ghost"
                    showSearch
                    :useOptionFlex="false"
                    useSearchApi
                    :selectUID="clientUUID"
                    :placeholder="$t('helpdesk.assign_contractor_placeholder')"
                    searchKey="search"
                    labelKey="string_view"
                    :params="customerCardParams"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @select="handleCustomerCardSelect"
                    @change="handleCustomerCardChange">
                    <template #prefixIcon>
                        <i class="fi fi-rr-user mr-2" />
                    </template>
                    <template #suffixSlot>
                        <a-button
                            type="ui"
                            ghost
                            shape="circle"
                            size="small"
                            flaticon
                            v-tippy
                            :content="$t('helpdesk.add_contractor')"
                            icon="fi-rr-user-add"
                            @click="addClient()" />
                    </template>
                </DSelect>
            </a-form-model-item>
            <a-form-model-item
                v-if="plannerMode && form.customer_card"
                ref="contact_person"
                label=""
                prop="contact_person">
                <ListViewModal
                    :endpoint="contactPersonEndpoint"
                    tableType="contact_person"
                    :title="$t('helpdesk.contact_persons')"
                    pageName="helpdesk_contact_person_all"
                    model="help_desk.ContactPersonModel"
                    @select="selectContactPerson"
                    :add="addContact"
                    ref="listViewModalConctactPersonRef" />
                <DSelect
                    :key="`${form.customer_card}_${personKey}`"
                    v-model="form.contact_person"
                    :apiUrl="contactPersonEndpoint"
                    class="w-full"
                    ref="contactPersonSelect"
                    :selectUID="contactUUID"
                    infinity
                    size="default"
                    inputType="ghost"
                    :useOptionFlex="false"
                    useSearchApi
                    showSearch
                    showPlaceholder
                    :showAllHandler="showAllContactPersonsHandler"
                    :initOptionList="initListConctactPerson"
                    :placeholder="$t('helpdesk.contact_person')"
                    searchKey="search"
                    labelKey="name"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @changeFull="changeFullPerson">
                    <template #suffixSlot>
                        <a-button
                            type="ui"
                            ghost
                            shape="circle"
                            size="small"
                            flaticon
                            :disabled="!form.customer_card"
                            v-tippy
                            :content="$t('helpdesk.add_contact_person')"
                            icon="fi-rr-user-add"
                            @click="addContact()" />
                    </template>
                </DSelect>
                <ContactModal
                    v-if="visible"
                    :contractor="form.org_admin ? (form.org_admin.id || form.org_admin) : null" />
            </a-form-model-item>
            <a-form-model-item v-if="!plannerMode" ref="org_admin" label="" prop="org_admin">
                <AdminOrgSelect 
                    v-model="form.org_admin"
                    inputType="ghost"
                    useIcon
                    firstSelect
                    placement="bottomLeft"
                    :placeholder="$t('helpdesk.select_service_organization')" />
            </a-form-model-item>
            <a-form-model-item v-if="!edit" ref="request_callback" label="" class="mb-0">
                <a-checkbox v-model="form.request_callback">
                    {{ $t('helpdesk.request_callback') }}
                </a-checkbox>
            </a-form-model-item>
        </a-form-model>
        <template #footer>
            <div class="flex" :class="isMobile ? 'flex-col w-full gap-2' : 'items-center gap-1'">
                <a-button type="primary" size="large" :block="isMobile" :loading="loading" @click="formSubmit()">
                    {{ $t('helpdesk.create_ticket') }}
                </a-button>
                <a-button type="ui_ghost" ghost size="large" :block="isMobile" @click="visible = false">
                    {{ $t('helpdesk.cancel') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { v1 as uuidv1 } from 'uuid'
export default {
    components: {
        AdminOrgSelect: () => import('../AdminOrgSelect.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        ContactModal: () => import('../ContactModal.vue'),
        ListViewModal: () => import('@/components/ListView/ListViewModal.vue')
    },
    computed: {
        ckEditor() {
            if (this.visible) return () => import("@apps/CKEditor");
            else return null;
        },
        plannerMode() {
            return Boolean(this.plannerPrefill?.__planner)
        },
        customerCardParams() {
            if (this.form.org_admin?.id)
                return { contractor: this.form.org_admin.id }

            return {}
        },
        showAllContactPersonsHandler() {
            return this.isMobile ? false : this.openAllContactPersons
        },
        contactPersonEndpoint() {
            return `help_desk/customer_cards/${this.form.customer_card}/contact_persons/`
        },
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            model: "help_desk.HelpDeskTicketModel",
            pageName: "help_desk.HelpDeskForClientTicketModel_page",
            edit: false,
            visible: false,
            loading: false,
            ticket: null,
            plannerPrefill: null,
            editorGate: false,
            clientUUID: null,
            contactUUID: null,
            personKey: Date.now(),
            fullPerson: null,
            initListConctactPerson: [],
            form: {
                name: "",
                description: "",
                org_admin: null,
                customer_card: null,
                contact_person: null,
                category: null,
                request_callback: false
            },
            rules: {
                description: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }],
                org_admin: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }],
                customer_card: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }],
                contact_person: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }],
                category: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }]
            }
        }
    },
    methods: { 
        onEditorReady() {
            if(this.$refs.descEditor && !this.isMobile)
                this.$refs.descEditor.editorFocus()
        },
        async createTicket(queryData) {
            const { data } = await this.$http.post('/help_desk/tickets/for_client/create/', queryData)
            return data
        },
        async getCustomerCard(customerCardId) {
            if (!customerCardId)
                return null

            const { data } = await this.$http.get(`/help_desk/customer_cards/${customerCardId}/`)
            return data || null
        },
        changeFullPerson(data) {
            this.fullPerson = data || null
        },
        async ensurePlannerOrgAdmin() {
            if (!this.form.customer_card)
                return this.form.org_admin

            if (this.form.org_admin?.id)
                return this.form.org_admin

            const customerCard = await this.getCustomerCard(this.form.customer_card)
            this.form.org_admin = customerCard?.org_admin || null
            return this.form.org_admin
        },
        async handleCustomerCardSelect(customerCardId) {
            if (!customerCardId)
                return

            try {
                const customerCard = await this.getCustomerCard(customerCardId)
                if (customerCard?.org_admin)
                    this.form.org_admin = customerCard.org_admin
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        async handleCustomerCardChange(customerCardId) {
            this.form.contact_person = null
            this.fullPerson = null
            this.initListConctactPerson = []
            this.personKey = Date.now()

            if (!customerCardId) {
                this.form.customer_card = null
                this.form.org_admin = null
                return
            }

            await this.handleCustomerCardSelect(customerCardId)
        },
        selectContactPerson(contact) {
            this.changeFullPerson(contact)
            this.form.contact_person = contact.id
            this.contactUUID = uuidv1()
            this.personKey = Date.now()
            this.initListConctactPerson = [{ ...contact }]
        },
        async openAllContactPersons() {
            let contactPersonData = null

            try {
                if (this.form.contact_person)
                    contactPersonData = await this.$http.get(`help_desk/contact_persons/${this.form.contact_person}/`)
            } catch (error) {
                return
            }

            if (!this.$refs.listViewModalConctactPersonRef)
                return

            await this.$refs.listViewModalConctactPersonRef.open()

            if (this.form.contact_person) {
                this.$nextTick(() => {
                    if (
                        this.$refs.listViewModalConctactPersonRef?.$refs?.refListView?.$refs?.tableRef
                        && contactPersonData
                    ) {
                        this.$refs.listViewModalConctactPersonRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            contactPersonData.data
                        ]
                    }
                })
            }
        },
        addClient() {
            const payload = {
                slaSelect: true
            }

            if (this.form.org_admin)
                payload.formPreset = { org_admin: this.form.org_admin }

            eventBus.$emit('helpdesc_add_client', true, payload)
        },
        addContact() {
            if (!this.form.customer_card)
                return

            eventBus.$emit('add_ticket_contact', this.form.customer_card)
        },
        async applyPlannerPrefill(ticket) {
            if(!ticket?.id)
                return ticket

            const payload = {}

            if (this.form.customer_card)
                payload.customer_card = this.form.customer_card
            if (this.form.contact_person)
                payload.contact_person = this.form.contact_person

            if(this.plannerPrefill?.specialist?.id)
                payload.specialist = this.plannerPrefill.specialist.id

            if(this.plannerPrefill?.start_date)
                payload.start_date = this.plannerPrefill.start_date
            if(this.plannerPrefill?.end_date)
                payload.end_date = this.plannerPrefill.end_date
            if(this.plannerPrefill?.dead_line)
                payload.dead_line = this.plannerPrefill.dead_line

            if (!Object.keys(payload).length)
                return ticket

            const { data } = await this.$http.patch(`/help_desk/tickets/${ticket.id}/`, payload)
            return data || ticket
        },
        isNameUnsupportedError(error) {
            const nameErrors = error?.response?.data?.name
            const messages = Array.isArray(nameErrors) ? nameErrors : [nameErrors]
            return messages
                .filter(Boolean)
                .map(message => String(message).toLowerCase())
                .some(message => message.includes('not allowed') || message.includes('не разреш'))
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        if (this.edit) {

                        } else {
                            const queryData = JSON.parse(JSON.stringify(this.form))
                            queryData.name = queryData.name?.trim()
                            if(!queryData.name)
                                delete queryData.name

                            if (this.plannerMode) {
                                const orgAdmin = await this.ensurePlannerOrgAdmin()
                                if (!orgAdmin?.id) {
                                    this.$message.warning(this.$t('helpdesk.required_field'))
                                    return
                                }
                            }

                            if(queryData.org_admin?.id)
                                queryData.org_admin = queryData.org_admin.id
                            delete queryData.customer_card
                            delete queryData.contact_person
                            const ticketName = queryData.name
                            let data = null
                            try {
                                data = await this.createTicket(queryData)
                            } catch (error) {
                                if(ticketName && this.isNameUnsupportedError(error)) {
                                    const fallbackQueryData = { ...queryData }
                                    delete fallbackQueryData.name
                                    data = await this.createTicket(fallbackQueryData)
                                    this.$message.warning(this.$t('helpdesk.client_title_server_fallback'))
                                } else {
                                    throw error
                                }
                            }
                            if(data) {
                                data = await this.applyPlannerPrefill(data)
                                this.visible = false
                                this.$message.success(this.$t('helpdesk.ticket_created'))
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                eventBus.$emit('planner_request_created', data)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/reloadList', {
                                        list: 'ticketList'
                                    })
                                }
                            }
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else 
                    return false
            })
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        async afterVisibleChange(val) {
            if(val) {
                this.clientUUID = uuidv1()
                this.contactUUID = uuidv1()
                this.editorGate = false
                await this.$nextTick()
                await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
                this.editorGate = true
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            const edComp = this.$refs.descEditor
                            const ed = edComp && (edComp.editorRef || edComp.editorRef)
                            if (ed && ed.ui && typeof ed.ui.update === 'function') ed.ui.update()
                            window.dispatchEvent(new Event('resize'))
                        })
                    })
                })
            } else {
                this.afterClose()
            }
        },
        afterClose() {
            this.edit = false
            this.form = {
                name: "",
                description: "",
                org_admin: null,
                customer_card: null,
                contact_person: null,
                category: null,
                request_callback: false
            }
            this.clientUUID = null
            this.contactUUID = null
            this.personKey = Date.now()
            this.fullPerson = null
            this.initListConctactPerson = []
            this.plannerPrefill = null
        }
    },
    mounted() {
        eventBus.$on('helpdesc_add_request_tickets', (payload = null) => {
            this.plannerPrefill = payload && payload.__planner ? payload : null
            this.visible = true
        })
        eventBus.$on('helpdesc_return_client', async (client) => {
            if(!this.visible)
                return

            this.$nextTick(() => {
                if(this.$refs.customerCardSelect)
                    this.$refs.customerCardSelect.unshiftItem(client)
            })

            this.form.customer_card = client.id
            this.form.contact_person = null
            this.fullPerson = null
            this.initListConctactPerson = []
            this.personKey = Date.now()

            if (client?.org_admin)
                this.form.org_admin = client.org_admin
            else
                await this.handleCustomerCardSelect(client.id)
        })
        eventBus.$on('helpdesc_return_contact', (contact) => {
            if(!this.visible)
                return

            this.selectContactPerson(contact)
        })
    },
    beforeDestroy() {
        eventBus.$off('helpdesc_add_request_tickets')
        eventBus.$off('helpdesc_return_client')
        eventBus.$off('helpdesc_return_contact')
    }
}
</script>

<style lang="scss" scoped>
.description_editor {
    z-index: 100;
    min-height: 108.65px;
  &::v-deep {
    .ck-editor__top {
      position: sticky !important;
      top: 0px !important;
      background: white !important;
      z-index: 999999;
    }
    .ck {
      &.ck-toolbar__items {
        margin-right: 0px !important;
      }
      &.ck-toolbar__separator {
        opacity: 0;
        margin-right: 0px !important;
      }
      &.ck-editor__top.ck-reset_all {
        border-radius: 8px !important;
      }
      &.ck-toolbar {
        border: 0px;
        // padding-left: 0px!important;
        // padding-right: 0px!important;
        // margin-left: -7px;
      }
      &.ck-content {
        border: 0px !important;
        box-shadow: none !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
      }
      &.ck-editor__main > .ck-editor__editable {
        background-color: transparent;
      }
    }
  }
}
</style>
