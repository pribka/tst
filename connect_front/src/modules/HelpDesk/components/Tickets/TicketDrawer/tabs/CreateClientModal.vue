<template>
    <a-modal
        :width="600"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        :afterClose="afterClose"
        :visible="visible"
        :title="$t('helpdesk.assign_contractor')"
        @cancel="visible = false">
        <a-form-model
            ref="formRef"
            :model="form"
            :rules="rules">
            <a-form-model-item 
                ref="customer_card" 
                class="mb-0"
                prop="customer_card">
                <DSelect
                    v-model="form.customer_card"
                    apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                    class="w-full"
                    oneSelect
                    ref="contact_person_select"
                    infinity
                    size="default"
                    resultsKey="filteredSelectList"
                    inputType="ghost"
                    showSearch
                    :useOptionFlex="false"
                    useSearchApi
                    :placeholder="$t('helpdesk.assign_contractor_placeholder')"
                    :selectUID="clientUUID"
                    searchKey="text"
                    labelKey="string_view"
                    :params="{ contractor: orgAdmin }"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @change="form.contact_person = null">
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
        </a-form-model>

        <template #footer>
            <div class="flex gap-1 items-center">
                <a-button type="primary" size="large" :loading="loading" @click="onSubmit()">
                    {{ $t('helpdesk.assign_contractor') }}
                </a-button>
                <a-button type="ui_ghost" ghost size="large" @click="visible = false">
                    {{ $t('helpdesk.cancel') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { v1 as uuidv1 } from 'uuid'

export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    data() {
        return {
            visible: false,
            form: {
                customer_card: null,
                contact_person: null
            },
            contactPerson: null,
            loading: false,
            rules: {
                customer_card: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'change' }],
            },
            clientUUID: null,
        }
    },
    computed: {
        orgAdmin() {
            return this.contactPerson?.customer_card?.org_admin
        }
    },
    mounted() {
        eventBus.$on('helpdesc_return_client', client => {
            if(this.form.contact_person) {
                this.form.contact_person = null
                eventBus.$emit(`select_exclude_${this.clientUUID}`, client)
            }
            this.$nextTick(() => {
                if(this.$refs.contact_person_select)
                    this.$refs.contact_person_select.unshiftItem(client)
            })
            this.form.customer_card = client.id
        })
    },
    beforeDestroy() {
        eventBus.$off('helpdesc_return_client')
    },
    methods: {
        async afterVisibleChange(val) {
            if(val) {
                this.clientUUID = uuidv1()
            }
        },
        openModal(contactPerson) {
            this.contactPerson = contactPerson
            this.visible = true
        },
        addClient() {
            eventBus.$emit('helpdesc_add_client', true, { hideOrgAdmin: true, formPreset: { org_admin: this.orgAdmin }, lead: this.$route.query.ticketView })
        },
        afterClose() {
            this.clientUUID = null
            this.contactPerson = null
        },
        onSubmit() {
            const url = `help_desk/contact_persons/${this.contactPerson.id}/set_customer_card/`
            const payload = {
                customer_card: this.form.customer_card,
                lead: this.$route.query.ticketView,
            }
            this.loading = true
            this.$http.post(url, payload)
                .then(() => {
                    this.$message.success(this.$t('helpdesk.contact_assigned'))
                    eventBus.$emit('ticket_in_client_reload')
                    this.visible = false
                })
                .catch((error) => {
                    this.$message.error(this.$t('helpdesk.failed_assign_contractor'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })


        }
    },
}
</script>