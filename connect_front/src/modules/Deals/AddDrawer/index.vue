<template>
    <DrawerTemplate
        v-model="visible"
        :width="drawerWidth"
        :loading="detailLoading"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="contract_add_drawer__title">
                {{ edit ? $t('deals_contracts.edit_contract') : $t('deals_contracts.create_contract') }}
            </div>
        </template>

        <a-form-model ref="form" :model="form" :rules="rules">
            <div class="contract_add_drawer__grid">
                <a-form-model-item :label="$t('deals_contracts.number')" prop="number" class="mb-0">
                    <a-input
                        v-model="form.number"
                        size="large"
                        :placeholder="$t('deals_contracts.enter_number')" />
                </a-form-model-item>

                <a-form-model-item :label="$t('deals_contracts.status')" prop="status" class="mb-0">
                    <DSelect
                        v-model="form.status"
                        size="large"
                        apiUrl="/app_info/select_list/"
                        listObject="selectList"
                        labelKey="string_view"
                        :params="{ model: 'customer_contracts.CustomerContractStatusModel' }"
                        :placeholder="$t('deals_contracts.select_from_list')"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null" />
                </a-form-model-item>

                <a-form-model-item :label="$t('deals_contracts.organization')" prop="organization" class="mb-0">
                    <OrgSelect
                        v-model="form.organization"
                        inputType="defaultInput"
                        apiUrl="/contractor_permissions/organizations/"
                        :params="{ permission_type: 'admin,create_workgroup' }"
                        :placeholder="$t('deals_contracts.select_from_list')"
                        placement="bottomLeft"
                        :autoAdjustOverflow="false"
                        :showDefaultOrganizationSwitcher="false"
                        :showRecent="false"
                        :pageSize="10"
                        @change="changeOrganization" />
                </a-form-model-item>

                <a-form-model-item :label="$t('deals_contracts.customer_field')" prop="customer_card" class="mb-0">
                    <ListViewModal
                        :endpoint="customerCardsListEndpoint"
                        tableType="clients"
                        pageName="helpdesk_clients_all"
                        :title="$t('deals_drawer.customers_title')"
                        model="help_desk.CustomerCardModel"
                        @select="selectCustomerCard"
                        :add="addCustomerCard"
                        ref="listViewModalClientsRef" />
                    <DSelect
                        :key="customerCardSelectKey"
                        v-model="form.customer_card"
                        apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                        class="w-full"
                        :params="customerCardParams"
                        :showAllHandler="openAllClients"
                        infinity
                        size="large"
                        resultsKey="filteredSelectList"
                        showSearch
                        initList
                        :initOptionList="customerCardOptionList"
                        :useOptionFlex="false"
                        useSearchApi
                        :disabled="!organizationId"
                        :placeholder="$t('deals_contracts.customer_placeholder')"
                        searchKey="search"
                        labelKey="string_view"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null"
                        @select="handleSelectCustomerCard"
                        @change="handleCustomerCardChange">
                        <template #suffixSlot>
                            <div class="flex items-center gap-2">
                                <a-spin v-if="getClientLoading" size="small" />
                                <a-button
                                    v-if="!getClientLoading"
                                    type="ui"
                                    ghost
                                    shape="circle"
                                    size="small"
                                    flaticon
                                    :disabled="!organizationId"
                                    v-tippy
                                    :content="$t('deals_drawer.customer_create')"
                                    icon="fi-rr-user-add"
                                    @click="addCustomerCard" />
                            </div>
                        </template>
                    </DSelect>
                </a-form-model-item>

                <a-form-model-item :label="$t('deals_contracts.project')" prop="projects" class="mb-0">
                    <ProjectSelect
                        :key="projectSelectKey"
                        v-model="form.projects"
                        inputType="defaultInput"
                        apiUrl="/work_groups/workgroups/list_short/"
                        :params="projectParams"
                        :disabled="!form.organization"
                        :placeholder="$t('deals_contracts.projects_placeholder')"
                        placement="bottomLeft"
                        :autoAdjustOverflow="false"
                        resultsKey="results"
                        stringifyFilters
                        :showRecent="false"
                        :pageSize="10" />
                </a-form-model-item>

                <a-form-model-item
                    :label="$t('deals_contracts.contract_date')"
                    prop="contract_date"
                    class="mb-0 contract_add_drawer__item contract_add_drawer__item--contract-date">
                    <a-date-picker
                        v-model="form.contract_date"
                        size="large"
                        class="w-full"
                        format="DD.MM.YYYY"
                        :open="datePickerOpen.contract_date"
                        :placeholder="$t('deals_contracts.select_date')"
                        :getCalendarContainer="getPopupContainer"
                        @openChange="handleDatePickerOpen('contract_date', $event)">
                        <template #renderExtraFooter>
                            <div class="contract_add_drawer__date_shortcuts">
                                <a-button
                                    v-for="item in dateShortcuts"
                                    :key="`contract_date_${item.key}`"
                                    size="small"
                                    type="ui"
                                    :title="item.title"
                                    @click="applyDateShortcut('contract_date', item.key)">
                                    {{ item.label }}
                                </a-button>
                            </div>
                        </template>
                    </a-date-picker>
                </a-form-model-item>

                <a-form-model-item
                    :label="$t('deals_contracts.amount')"
                    prop="amount"
                    class="mb-0 contract_add_drawer__item contract_add_drawer__item--amount">
                    <a-input
                        v-model="form.amount"
                        size="large"
                        class="w-full"
                        :placeholder="$t('deals_contracts.enter_amount')"
                        @input="onAmountInput"
                        @blur="onAmountBlur" />
                </a-form-model-item>

                <a-form-model-item
                    :label="$t('deals_contracts.date_start')"
                    prop="date_start"
                    class="mb-0 contract_add_drawer__item contract_add_drawer__item--date-start">
                    <a-date-picker
                        v-model="form.date_start"
                        size="large"
                        class="w-full"
                        format="DD.MM.YYYY"
                        :getCalendarContainer="getPopupContainer" />
                </a-form-model-item>

                <a-form-model-item
                    :label="$t('deals_contracts.date_end')"
                    prop="date_end"
                    class="mb-0 contract_add_drawer__item contract_add_drawer__item--date-end">
                    <a-date-picker
                        v-model="form.date_end"
                        size="large"
                        class="w-full"
                        format="DD.MM.YYYY"
                        :open="datePickerOpen.date_end"
                        :placeholder="$t('deals_contracts.select_date')"
                        :getCalendarContainer="getPopupContainer"
                        @openChange="handleDatePickerOpen('date_end', $event)">
                        <template #renderExtraFooter>
                            <div class="contract_add_drawer__date_shortcuts">
                                <a-button
                                    v-for="item in dateShortcuts"
                                    :key="`date_end_${item.key}`"
                                    size="small"
                                    type="ui"
                                    :title="item.title"
                                    @click="applyDateShortcut('date_end', item.key)">
                                    {{ item.label }}
                                </a-button>
                            </div>
                        </template>
                    </a-date-picker>
                </a-form-model-item>

                <a-form-model-item
                    :label="$t('deals_contracts.hours_plan')"
                    prop="hours_plan"
                    class="mb-0 contract_add_drawer__item contract_add_drawer__item--hours-plan">
                    <a-input-number
                        v-model="form.hours_plan"
                        size="large"
                        class="w-full"
                        :min="0"
                        :precision="0"
                        :placeholder="$t('deals_contracts.enter_hours_plan')" />
                </a-form-model-item>
            </div>

            <div v-if="isMobile" class="contract_add_drawer__mobile_switches">
                <div class="contract_add_drawer__switch">
                    <a-switch v-model="form.is_signed" />
                    <span @click="form.is_signed = !form.is_signed">{{ $t('deals_contracts.document_signed') }}</span>
                </div>

                <div class="contract_add_drawer__switch">
                    <a-switch v-model="form.is_exists" />
                    <span @click="form.is_exists = !form.is_exists">{{ $t('deals_contracts.document_exists') }}</span>
                </div>
            </div>
        </a-form-model>

        <template #footer>
            <div class="contract_add_drawer__footer" :class="{ 'w-full': isMobile }">
                <a-button
                    type="primary"
                    size="large"
                    class="contract_add_drawer__submit"
                    :block="isMobile"
                    :loading="saving"
                    @click="submit">
                    {{ edit ? $t('deals_contracts.save') : $t('deals_contracts.create') }}
                </a-button>

                <div v-if="!isMobile" class="contract_add_drawer__switch">
                    <a-switch v-model="form.is_signed" />
                    <span @click="form.is_signed = !form.is_signed">{{ $t('deals_contracts.document_signed') }}</span>
                </div>

                <div v-if="!isMobile" class="contract_add_drawer__switch">
                    <a-switch v-model="form.is_exists" />
                    <span @click="form.is_exists = !form.is_exists">{{ $t('deals_contracts.document_exists') }}</span>
                </div>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

const defaultForm = () => ({
    id: null,
    number: '',
    contract_date: null,
    date_start: null,
    date_end: null,
    amount: '',
    hours_plan: null,
    is_signed: false,
    is_exists: true,
    status: null,
    organization: null,
    customer_card: null,
    projects: null,
})

export default {
    name: 'DealsContractAddDrawer',
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        ListViewModal: () => import('@/components/ListView/ListViewModal.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        OrgSelect: () => import('@apps/DrawerSelect/OrgSelect.vue'),
        ProjectSelect: () => import('@apps/DrawerSelect/ProjectSelect.vue'),
    },
    data() {
        return {
            visible: false,
            edit: false,
            saving: false,
            detailLoading: false,
            model: 'customer_contracts.CustomerContractModel',
            pageName: 'page_list_contracts_v3_customer_contracts.CustomerContractModel',
            form: defaultForm(),
            projectSelectKey: 0,
            customerCardSelectKey: 0,
            customerCardOptionList: [],
            getClientLoading: false,
            datePickerOpen: {
                contract_date: false,
                date_end: false,
            },
            rules: {
                organization: [
                    {
                        required: true,
                        message: this.$t('field_required'),
                        trigger: 'change',
                    },
                ],
            },
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            const baseWidth = 800
            const offset = 40
            return this.windowWidth > baseWidth + offset ? baseWidth : this.windowWidth
        },
        dateShortcuts() {
            const shortcuts = [
                { key: 'today', label: this.$t('task.date_today'), make: () => this.$moment() },
                { key: 'tomorrow', label: this.$t('task.date_tomorrow'), make: () => this.$moment().add(1, 'day') },
                { key: 'end_week', label: this.$t('task.date_end_week'), make: () => this.$moment().endOf('isoWeek') },
                { key: 'plus_week', label: this.$t('task.date_plus_week'), make: () => this.$moment().add(1, 'week') },
                { key: 'end_month', label: this.$t('task.date_end_month'), make: () => this.$moment().endOf('month') },
            ]

            return shortcuts.map(item => {
                const date = item.make().startOf('day')
                return {
                    ...item,
                    title: date.format('DD.MM.YYYY'),
                }
            })
        },
        projectParams() {
            return {
                is_project: 1,
                filters: {
                    organization: this.form.organization?.id || this.form.organization,
                },
            }
        },
        organizationId() {
            return this.form.organization?.id || this.form.organization || null
        },
        customerCardParams() {
            if (!this.organizationId) {
                return {}
            }

            return {
                contractor: this.organizationId,
            }
        },
        customerCardsListEndpoint() {
            return this.organizationId
                ? `help_desk/customer_cards/?contractor=${this.organizationId}`
                : 'help_desk/customer_cards/'
        },
    },
    methods: {
        openCreate() {
            this.edit = false
            this.resetForm()
            this.form.contract_date = this.$moment()
            this.visible = true
        },
        async openEdit(record) {
            if (!record?.id) return
            this.edit = true
            this.resetForm()
            this.visible = true
            await this.getDetail(record.id)
        },
        async getDetail(id) {
            try {
                this.detailLoading = true
                const { data } = await this.$http.get(`/customer_contracts/${id}/`)
                if (data) {
                    this.fillForm(data)
                }
            } catch (error) {
                errorHandler({ error })
                this.visible = false
            } finally {
                this.detailLoading = false
            }
        },
        fillForm(data) {
            const organization = data.organization || null
            const projects = Array.isArray(data.projects) ? data.projects : []
            const customerCard = data.customer_card || data.external_customer || null

            this.form = {
                id: data.id || null,
                number: data.number || '',
                contract_date: this.toMoment(data.contract_date),
                date_start: this.toMoment(data.date_start),
                date_end: this.toMoment(data.date_end),
                amount: this.normalizeAmount(data.amount),
                hours_plan: this.toNumberOrNull(data.hours_plan),
                is_signed: Boolean(data.is_signed),
                is_exists: Boolean(data.is_exists),
                status: data.status?.id || data.status || null,
                organization,
                customer_card: customerCard?.id || customerCard || null,
                projects: projects[0] || null,
            }
            this.customerCardOptionList = customerCard?.id
                ? [this.toCustomerCardOption(customerCard.id, this.getCustomerCardLabel(customerCard))]
                : []
            this.customerCardSelectKey += 1
            this.projectSelectKey += 1
        },
        changeOrganization() {
            this.resetCustomerCard()
            this.form.projects = null
            this.customerCardSelectKey += 1
            this.projectSelectKey += 1
        },
        toCustomerCardOption(id, label) {
            return {
                id,
                string_view: label || String(id),
            }
        },
        getCustomerCardLabel(client) {
            if (!client) return ''
            return client.string_view || client.full_name || client.name || String(client.id || '')
        },
        selectCustomerCard(client) {
            if (!client?.id) return
            this.customerCardOptionList = [this.toCustomerCardOption(client.id, this.getCustomerCardLabel(client))]
            this.handleCustomerCardChange(client.id)
        },
        handleSelectCustomerCard(clientId) {
            this.fetchCustomerCard(clientId)
        },
        async handleCustomerCardChange(clientId) {
            this.form.customer_card = clientId || null

            if (!clientId) {
                this.customerCardOptionList = []
                return
            }

            await this.fetchCustomerCard(clientId)
        },
        async fetchCustomerCard(clientId) {
            if (!clientId) return

            this.getClientLoading = true
            try {
                const { data } = await this.$http.get(`/help_desk/customer_cards/${clientId}/`)
                this.customerCardOptionList = [this.toCustomerCardOption(data.id, this.getCustomerCardLabel(data))]
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.getClientLoading = false
            }
        },
        addCustomerCard() {
            if (!this.organizationId) return
            eventBus.$emit('helpdesc_add_client', true, {
                slaSelect: true,
                formPreset: {
                    org_admin: this.organizationId,
                },
            })
        },
        async openAllClients() {
            if (!this.organizationId) return

            let customerCardData
            try {
                if (this.form.customer_card) {
                    customerCardData = await this.$http.get(
                        `/help_desk/customer_cards/${this.form.customer_card}/customer_card_detail/?page_name=helpdesk_clients_all`
                    )
                }
            } catch (error) {
                errorHandler({ error, show: false })
            }

            await this.$refs.listViewModalClientsRef?.open?.()

            if (this.form.customer_card) {
                this.$nextTick(() => {
                    if (this.$refs.listViewModalClientsRef?.$refs?.refListView?.$refs?.tableRef && customerCardData) {
                        this.$refs.listViewModalClientsRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            customerCardData.data,
                        ]
                    }
                })
            }
        },
        resetCustomerCard() {
            this.form.customer_card = null
            this.customerCardOptionList = []
        },
        handleReturnedCustomerCard(client) {
            if (!this.visible || !client?.id) return
            this.selectCustomerCard(client)
        },
        handleDatePickerOpen(field, open) {
            this.$set(this.datePickerOpen, field, open)
        },
        applyDateShortcut(field, key) {
            const shortcut = this.dateShortcuts.find(item => item.key === key)
            if (!shortcut) return

            const map = {
                today: () => this.$moment(),
                tomorrow: () => this.$moment().add(1, 'day'),
                end_week: () => this.$moment().endOf('isoWeek'),
                plus_week: () => this.$moment().add(1, 'week'),
                end_month: () => this.$moment().endOf('month'),
            }
            const createDate = map[key]
            if (!createDate) return

            this.form[field] = createDate().startOf('day')
            this.$set(this.datePickerOpen, field, false)
        },
        submit() {
            this.saving = true
            this.$refs.form.validate(async (valid) => {
                if (!valid) {
                    this.saving = false
                    this.$message.warning(this.$t('project.fill_all_fields'))
                    return
                }

                try {
                    const payload = this.buildPayload()
                    let response
                    if (this.edit) {
                        response = await this.$http.put(`/customer_contracts/${this.form.id}/`, payload)
                        this.$message.success(this.$t('deals_contracts.contract_updated'))
                    } else {
                        response = await this.$http.post('/customer_contracts/', payload)
                        this.$message.success(this.$t('deals_contracts.contract_created'))
                    }

                    eventBus.$emit('DEALS_CONTRACT_UPDATED', response?.data || payload)
                    eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                    this.visible = false
                } catch (error) {
                    errorHandler({ error })
                } finally {
                    this.saving = false
                }
            })
        },
        buildPayload() {
            const projects = Array.isArray(this.form.projects) ? this.form.projects : [this.form.projects]
            const payload = {
                number: this.form.number || '',
                status: this.form.status || null,
                customer_card: this.form.customer_card || null,
                projects: projects.map(project => project?.id || project).filter(Boolean),
                contract_date: this.formatDate(this.form.contract_date),
                date_start: this.formatDate(this.form.date_start),
                date_end: this.formatDate(this.form.date_end),
                amount: this.formatAmount(this.form.amount),
                hours_plan: this.formatDecimal(this.form.hours_plan),
                is_signed: Boolean(this.form.is_signed),
                is_exists: Boolean(this.form.is_exists),
            }

            if (this.edit) {
                payload.id = this.form.id
            } else {
                payload.organization = this.form.organization?.id || this.form.organization
            }

            return payload
        },
        onAmountInput(e) {
            let value = String(e.target.value || '')

            value = value.replace(',', '.')
            value = value.replace(/[^\d.]/g, '')

            const parts = value.split('.')
            const intPart = parts[0]
            const decPart = parts[1] ? parts[1].slice(0, 2) : ''

            value = decPart !== undefined
                ? `${intPart}${parts.length > 1 ? `.${decPart}` : ''}`
                : intPart

            this.form.amount = this.formatThousands(value)
        },
        onAmountBlur() {
            let value = String(this.form.amount || '').replace(/\s/g, '')

            if (!value) {
                this.form.amount = ''
                return
            }

            let [intPart, decPart = ''] = value.split('.')
            decPart = decPart.padEnd(2, '0').slice(0, 2)

            this.form.amount = this.formatThousands(`${intPart}.${decPart}`)
        },
        normalizeAmount(value) {
            if (value === undefined || value === null || value === '') return ''

            const str = String(value).replace(/\s/g, '').replace(',', '.')
            if (!str) return ''

            const parts = str.split('.')
            const intPart = parts[0].replace(/\D/g, '') || '0'
            const decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)
            const fixedDec = decPart.padEnd(2, '0')

            return this.formatThousands(`${intPart}.${fixedDec}`)
        },
        formatThousands(value) {
            if (!value) return ''

            const parts = String(value).split('.')
            const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
            const decPart = parts[1] !== undefined ? `.${parts[1]}` : ''

            return `${intPart}${decPart}`
        },
        formatAmount(value) {
            const normalized = String(value || '').replace(/\s/g, '').replace(',', '.')
            if (!normalized) return null
            const numberValue = Number(normalized)
            return Number.isFinite(numberValue) ? numberValue.toFixed(2) : null
        },
        formatDate(value) {
            if (!value) return null
            const date = this.$moment(value)
            return date.isValid() ? date.format('YYYY-MM-DD') : null
        },
        formatDecimal(value) {
            if (value === null || value === undefined || value === '') return null
            return Number(value).toFixed(2)
        },
        toMoment(value) {
            if (!value) return null
            const date = this.$moment(value)
            return date.isValid() ? date : null
        },
        toNumberOrNull(value) {
            if (value === null || value === undefined || value === '') return null
            const num = Number(value)
            return Number.isFinite(num) ? num : null
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        afterVisibleChange(visible) {
            if (!visible) {
                this.closeDrawer()
            }
        },
        closeDrawer() {
            this.resetForm()
            this.edit = false
            this.saving = false
            this.detailLoading = false
        },
        resetForm() {
            this.form = defaultForm()
            this.customerCardOptionList = []
            this.datePickerOpen = {
                contract_date: false,
                date_end: false,
            }
            this.customerCardSelectKey += 1
            this.projectSelectKey += 1
            this.$nextTick(() => {
                this.$refs.form?.clearValidate?.()
            })
        },
    },
    mounted() {
        eventBus.$on('DEALS_ADD_CONTRACT', this.openCreate)
        eventBus.$on('DEALS_EDIT_CONTRACT', this.openEdit)
        eventBus.$on('helpdesc_return_client', this.handleReturnedCustomerCard)
    },
    beforeDestroy() {
        eventBus.$off('DEALS_ADD_CONTRACT', this.openCreate)
        eventBus.$off('DEALS_EDIT_CONTRACT', this.openEdit)
        eventBus.$off('helpdesc_return_client', this.handleReturnedCustomerCard)
    },
}
</script>

<style lang="scss" scoped>
.contract_add_drawer__title {
    color: #111827;
    font-size: 18px;
    font-weight: 600;
}

.contract_add_drawer__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px 16px;
}

.contract_add_drawer__footer {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.contract_add_drawer__submit {
    height: 40px;
}

.contract_add_drawer__switch {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-height: 40px;

    span {
        cursor: pointer;
        user-select: none;
    }
}

.contract_add_drawer__date_shortcuts {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 4px;
}

.contract_add_drawer__mobile_switches {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-top: 16px;
}

@media (min-width: 768px) {
    .contract_add_drawer__item--contract-date {
        order: 6;
    }

    .contract_add_drawer__item--date-start {
        order: 7;
    }

    .contract_add_drawer__item--date-end {
        order: 8;
    }

    .contract_add_drawer__item--amount {
        order: 9;
    }

    .contract_add_drawer__item--hours-plan {
        order: 10;
    }
}

@media (max-width: 767px) {
    .contract_add_drawer__grid {
        grid-template-columns: minmax(0, 1fr);
    }

    .contract_add_drawer__footer {
        align-items: stretch;
        flex-direction: column;
        gap: 10px;
    }
}
</style>
