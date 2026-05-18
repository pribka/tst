<template>
    <DrawerTemplate
        :value="value"
        :width="drawerWidth"
        :loading="loading"
        destroyOnClose
        @close="$emit('close')">
        <template #title>
            <div class="deal_drawer__title_wrap">
                <div class="deal_drawer__title">
                    {{ drawerTitle }}
                </div>
                <div v-if="deal && !createMode" class="deal_drawer__subtitle">
                    {{ $t('deals_drawer.updated_prefix') }} {{ formatDateTime(deal.updated_at) || $t('deals_drawer.just_now') }}
                </div>
            </div>
        </template>

        <template #rightHeader>
            <a-button
                v-if="deal && !createMode"
                type="ui"
                ghost
                shape="circle"
                icon="fi-rr-refresh"
                flaticon
                v-tippy
                :content="$t('deals_drawer.reload_tooltip')"
                @click="$emit('reload')" />
        </template>

        <div class="deal_drawer">
            <ClientForm />

            <a-tabs :activeKey="activeTab" @change="activeTab = $event">
                <a-tab-pane key="overview" :tab="$t('deals_drawer.overview_tab')">
                    <a-form-model ref="form" :model="form" :rules="rules" layout="vertical">
                        <div class="deal_drawer__grid">
                            <a-form-model-item :label="$t('deals_drawer.name')" prop="name" class="mb-0">
                                <a-input
                                    v-model="form.name"
                                    size="large"
                                    :placeholder="$t('deals_drawer.name_placeholder')" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.stage')" prop="stage" class="mb-0">
                                <a-select
                                    v-model="form.stage"
                                    size="large"
                                    :placeholder="$t('deals_drawer.stage_placeholder')">
                                    <a-select-option
                                        v-for="stage in stageOptions"
                                        :key="stage.id"
                                        :value="stage.id">
                                        {{ stage.name }}
                                    </a-select-option>
                                </a-select>
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.responsible')" class="mb-0">
                                <UserDrawer
                                    :id="`deal_responsible_${deal && deal.id ? deal.id : 'new'}`"
                                    v-model="form.responsible"
                                    inputType="ghost"
                                    :title="$t('deals_drawer.responsible_select')"
                                    :inputPlaceholder="$t('deals_drawer.responsible_select')"
                                    class="w-full" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.customer')" class="mb-0">
                                <ListViewModal
                                    endpoint="help_desk/customer_cards/"
                                    tableType="clients"
                                    pageName="helpdesk_clients_all"
                                    :title="$t('deals_drawer.customers_title')"
                                    model="help_desk.CustomerCardModel"
                                    @select="selectCustomerCard"
                                    :add="addCustomerCard"
                                    ref="listViewModalClientsRef" />
                                <DSelect
                                    v-model="form.customer_card"
                                    apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                                    class="w-full"
                                    :showAllHandler="openAllClients"
                                    size="large"
                                    resultsKey="filteredSelectList"
                                    inputType="ghost"
                                    showSearch
                                    initList
                                    :initOptionList="customerCardInitList"
                                    :useOptionFlex="false"
                                    useSearchApi
                                    :placeholder="$t('deals_drawer.customer_placeholder')"
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
                                                v-else-if="form.customer_card"
                                                type="ui"
                                                ghost
                                                shape="circle"
                                                size="small"
                                                flaticon
                                                v-tippy
                                                :content="$t('deals_drawer.customer_open')"
                                                icon="fi-rr-user-pen"
                                                @click="openCustomerCard" />
                                            <a-button
                                                v-if="!getClientLoading"
                                                type="ui"
                                                ghost
                                                shape="circle"
                                                size="small"
                                                flaticon
                                                v-tippy
                                                :content="$t('deals_drawer.customer_create')"
                                                icon="fi-rr-user-add"
                                                @click="addCustomerCard" />
                                        </div>
                                    </template>
                                </DSelect>
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.source_ticket')" class="mb-0">
                                <DSelect
                                    :key="`ticket_${formKey}`"
                                    v-model="form.source_ticket"
                                    size="large"
                                    apiUrl="/app_info/filtered_select_list/"
                                    :params="{ model: 'help_desk.HelpDeskTicketModel' }"
                                    listObject="filteredSelectList"
                                    labelKey="string_view"
                                    showSearch
                                    useSearchApi
                                    initList
                                    :useOptionFlex="false"
                                    :initOptionList="ticketInitList"
                                    :default-active-first-option="false"
                                    :filter-option="false"
                                    :not-found-content="null"
                                    :placeholder="$t('deals_drawer.source_ticket_placeholder')" />
                                <div v-if="deal && deal.source_ticket" class="deal_drawer__inline_link">
                                    <a-button type="link" class="px-0" @click="$emit('open-related', { type: 'ticket', id: deal.source_ticket.id })">
                                        {{ $t('deals_drawer.source_ticket_open') }}
                                    </a-button>
                                </div>
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.planned_close_date')" class="mb-0">
                                <a-date-picker
                                    v-model="form.planned_close_date"
                                    size="large"
                                    class="w-full"
                                    format="DD.MM.YYYY"
                                    :getCalendarContainer="getPopupContainer"
                                    :placeholder="$t('deals_drawer.date_placeholder')" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.expected_amount')" class="mb-0">
                                <a-input-number
                                    v-model="form.expected_amount"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :precision="2"
                                    placeholder="0" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.internal_budget')" class="mb-0">
                                <a-input-number
                                    v-model="form.internal_budget"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :precision="2"
                                    placeholder="0" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.probability')" class="mb-0">
                                <a-input-number
                                    v-model="form.probability"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :max="100"
                                    placeholder="0..100" />
                            </a-form-model-item>
                        </div>

                        <div class="deal_drawer__summary">
                            <div class="deal_drawer__summary_card">
                                <span class="deal_drawer__summary_label">{{ $t('deals_drawer.summary_expected_amount') }}</span>
                                <strong>{{ formatMoney(form.expected_amount) }}</strong>
                            </div>
                            <div class="deal_drawer__summary_card">
                                <span class="deal_drawer__summary_label">{{ $t('deals_drawer.summary_internal_budget') }}</span>
                                <strong>{{ formatMoney(form.internal_budget) }}</strong>
                            </div>
                            <div class="deal_drawer__summary_card deal_drawer__summary_card--accent">
                                <span class="deal_drawer__summary_label">{{ $t('deals_drawer.summary_margin') }}</span>
                                <strong>{{ formatMoney(marginValue) }}</strong>
                            </div>
                        </div>

                        <div v-if="primaryContract" class="deal_drawer__contract">
                            <div class="deal_drawer__contract_head">
                                <div>
                                    <div class="deal_drawer__contract_title">
                                        {{ contractTitle }}
                                    </div>
                                    <div class="deal_drawer__contract_subtitle">
                                        {{ contractSubtitle }}
                                    </div>
                                </div>
                                <a-tag :color="contractStatusColor">
                                    {{ primaryContract.status?.name || $t('deals_drawer.contract_fallback') }}
                                </a-tag>
                            </div>

                            <div class="deal_drawer__contract_grid">
                                <div class="deal_drawer__contract_card">
                                    <span class="deal_drawer__summary_label">{{ $t('deals_drawer.contract_amount') }}</span>
                                    <strong>{{ formatMoney(primaryContract.amount) }}</strong>
                                </div>
                                <div class="deal_drawer__contract_card">
                                    <span class="deal_drawer__summary_label">{{ $t('deals_drawer.contract_period') }}</span>
                                    <strong>{{ contractPeriod }}</strong>
                                </div>
                                <div class="deal_drawer__contract_card">
                                    <span class="deal_drawer__summary_label">{{ $t('deals_drawer.contract_hours') }}</span>
                                    <strong>{{ contractHours }}</strong>
                                </div>
                            </div>

                            <div class="deal_drawer__contract_meta">
                                <span class="deal_drawer__contract_chip" :class="{ 'is-success': primaryContract.is_signed }">
                                    {{ primaryContract.is_signed ? $t('deals_drawer.contract_signed') : $t('deals_drawer.contract_not_signed') }}
                                </span>
                                <span class="deal_drawer__contract_chip" :class="{ 'is-success': primaryContract.is_exists }">
                                    {{ primaryContract.is_exists ? $t('deals_drawer.contract_original_present') : $t('deals_drawer.contract_original_missing') }}
                                </span>
                                <span v-if="primaryContract.organization?.name" class="deal_drawer__contract_chip">
                                    {{ $t('deals_drawer.contract_org') }}: {{ primaryContract.organization.name }}
                                </span>
                                <span
                                    v-if="primaryContractClientLabel"
                                    class="deal_drawer__contract_chip">
                                    {{ $t('deals_drawer.contract_customer') }}: {{ primaryContractClientLabel }}
                                </span>
                            </div>
                        </div>

                        <a-form-model-item :label="$t('deals_drawer.description')" class="mb-0">
                            <a-textarea
                                v-model="form.description"
                                :auto-size="{ minRows: 4, maxRows: 8 }"
                                :placeholder="$t('deals_drawer.description_placeholder')" />
                        </a-form-model-item>

                        <div class="deal_drawer__grid deal_drawer__grid--bottom">
                            <a-form-model-item :label="$t('deals_drawer.members')" class="mb-0">
                                <UserDrawer
                                    :id="`deal_members_${deal && deal.id ? deal.id : 'new'}`"
                                    v-model="form.members"
                                    inputType="ghost"
                                    multiple
                                    :title="$t('deals_drawer.members_select')"
                                    :inputPlaceholder="$t('deals_drawer.members_add')"
                                    class="w-full" />
                            </a-form-model-item>

                            <a-form-model-item :label="$t('deals_drawer.observers')" class="mb-0">
                                <UserDrawer
                                    :id="`deal_observers_${deal && deal.id ? deal.id : 'new'}`"
                                    v-model="form.observers"
                                    inputType="ghost"
                                    multiple
                                    :title="$t('deals_drawer.observers_select')"
                                    :inputPlaceholder="$t('deals_drawer.observers_add')"
                                    class="w-full" />
                            </a-form-model-item>
                        </div>
                    </a-form-model>
                </a-tab-pane>

                <a-tab-pane v-if="canShowTabs" key="tasks" :tab="`${$t('deals_drawer.tasks_tab')} (${deal.tasks_count || 0})`">
                    <DealTasksTab :dealId="deal.id" @open="$emit('open-related', { type: 'task', id: $event })" />
                </a-tab-pane>

                <a-tab-pane v-if="canShowTabs" key="files" :tab="`${$t('deals_drawer.files_tab')} (${deal.files_count || 0})`">
                    <div class="deal_drawer__files_wrap">
                        <vue2Files
                            :sourceId="deal.id"
                            widgetEmbed
                            :showHeader="false"
                            :showFilter="false" />
                    </div>
                </a-tab-pane>

                <a-tab-pane v-if="canShowTabs" key="meetings" :tab="`${$t('deals_drawer.meetings_tab')} (${deal.meetings_count || 0})`">
                    <RelationList
                        type="meetings"
                        :items="deal.meetings || []"
                        :emptyText="$t('deals_drawer.meetings_empty')"
                        @open="$emit('open-related', { type: 'meeting', id: $event.id })" />
                </a-tab-pane>

                <a-tab-pane v-if="canShowTabs" key="orders" :tab="`${$t('deals_drawer.orders_tab')} (${deal.orders_count || 0})`">
                    <RelationList
                        type="orders"
                        :items="deal.orders || []"
                        :emptyText="$t('deals_drawer.orders_empty')"
                        @open="$emit('open-related', { type: 'order', id: $event.id })" />
                </a-tab-pane>
            </a-tabs>
        </div>

        <template #footer>
            <div class="deal_drawer__footer">
                <div v-if="deal && !createMode" class="deal_drawer__footer_meta">
                    <a-tag v-if="primaryContract">
                        {{ contractTitle }}
                    </a-tag>
                    <a-tag>{{ $t('deals_drawer.footer_documents') }}: {{ deal.files_count || 0 }}</a-tag>
                    <a-tag>{{ $t('deals_drawer.footer_tasks') }}: {{ deal.tasks_count || 0 }}</a-tag>
                    <a-tag>{{ $t('deals_drawer.footer_meetings') }}: {{ deal.meetings_count || 0 }}</a-tag>
                    <a-tag>{{ $t('deals_drawer.footer_orders') }}: {{ deal.orders_count || 0 }}</a-tag>
                </div>
                <div class="deal_drawer__footer_actions">
                    <a-button @click="$emit('close')">
                        {{ $t('deals_drawer.close') }}
                    </a-button>
                    <a-button
                        type="primary"
                        :loading="saving"
                        @click="submit">
                        {{ createMode ? $t('deals_drawer.create_deal') : $t('deals_drawer.save_changes') }}
                    </a-button>
                </div>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'DealDrawer',
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        ListViewModal: () => import('@/components/ListView/ListViewModal.vue'),
        ClientForm: () => import('@apps/Directories/components/ClientForm.vue'),
        DealTasksTab: () => import('./DealTasksTab.vue'),
        RelationList: () => import('./RelationList.vue'),
        vue2Files: () => import('@apps/vue2Files'),
    },
    props: {
        value: {
            type: Boolean,
            required: true
        },
        createMode: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        },
        saving: {
            type: Boolean,
            default: false
        },
        deal: {
            type: Object,
            default: () => null
        },
        stageOptions: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            activeTab: 'overview',
            formKey: 0,
            getClientLoading: false,
            customerCardOptionList: [],
            form: this.getDefaultForm(),
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t('deals_drawer.name_required'),
                        trigger: 'blur'
                    }
                ]
            }
        }
    },
    computed: {
        drawerWidth() {
            return this.$store.state.isMobile ? '100%' : 1180
        },
        drawerTitle() {
            if (this.createMode) {
                return this.$t('deals_drawer.title_new')
            }
            return this.form.name || this.deal?.name || this.$t('deals_drawer.title_fallback')
        },
        canShowTabs() {
            return Boolean(this.deal && this.deal.id && !this.createMode)
        },
        marginValue() {
            return Number(this.form.expected_amount || 0) - Number(this.form.internal_budget || 0)
        },
        primaryContract() {
            return this.deal?.customer_contract || null
        },
        syncSourceKey() {
            return [this.createMode ? 1 : 0, this.deal?.id || '', this.deal?.updated_at || '', this.value ? 1 : 0].join(':')
        },
        contractTitle() {
            if (!this.primaryContract) return ''
            return this.primaryContract.number
                ? `${this.$t('deals_drawer.contract_title_prefix')}${this.primaryContract.number}`
                : this.$t('deals_drawer.contract_title_linked')
        },
        contractSubtitle() {
            if (!this.primaryContract) return ''
            const parts = [
                this.formatDate(this.primaryContract.contract_date),
                this.primaryContract.organization?.name,
            ].filter(Boolean)
            return parts.join(' • ') || this.$t('deals_drawer.contract_subtitle_fallback')
        },
        contractPeriod() {
            if (!this.primaryContract) return this.$t('deals_drawer.not_set')
            const start = this.formatDate(this.primaryContract.date_start)
            const end = this.formatDate(this.primaryContract.date_end)
            if (start && end) return `${start} - ${end}`
            return start || end || this.$t('deals_drawer.not_set')
        },
        contractHours() {
            if (!this.primaryContract) return this.$t('deals_drawer.hours_default')
            const plan = this.formatDecimal(this.primaryContract.hours_plan)
            const fact = this.formatDecimal(this.primaryContract.hours_fact)
            return `${fact} / ${plan} ${this.$t('deals_drawer.hours_suffix')}`
        },
        contractStatusColor() {
            if (!this.primaryContract?.status?.code) return 'blue'
            const colorMap = {
                lead: 'gold',
                active: 'green',
                on_pause: 'orange',
                completed: 'blue',
            }
            return colorMap[this.primaryContract.status.code] || 'blue'
        },
        primaryContractClientLabel() {
            if (!this.primaryContract) return ''
            const client = this.primaryContract.external_customer || this.primaryContract.customer_card
            if (!client) return ''
            return client.full_name || client.name || client.string_view || ''
        },
        customerCardInitList() {
            if (this.customerCardOptionList.length) {
                return this.customerCardOptionList
            }
            if (!this.deal?.customer_card) return []
            return [this.toOption(this.deal.customer_card.id, this.getCustomerCardLabel(this.deal.customer_card))]
        },
        ticketInitList() {
            if (!this.deal?.source_ticket) return []
            return [this.toOption(this.deal.source_ticket.id, this.ticketLabel(this.deal.source_ticket))]
        },
    },
    watch: {
        value(val) {
            if (val) {
                this.activeTab = 'overview'
            }
        },
        syncSourceKey: {
            immediate: true,
            handler() {
                this.syncFormState()
            }
        },
    },
    mounted() {
        eventBus.$on('helpdesc_return_client', this.handleReturnedCustomerCard)
    },
    beforeDestroy() {
        eventBus.$off('helpdesc_return_client', this.handleReturnedCustomerCard)
    },
    methods: {
        getDefaultForm() {
            return {
                name: '',
                description: '',
                stage: null,
                responsible: null,
                customer_card: null,
                source_ticket: null,
                expected_amount: null,
                internal_budget: null,
                probability: 0,
                planned_close_date: null,
                members: [],
                observers: [],
            }
        },
        syncFormState() {
            this.customerCardOptionList = []

            if (this.createMode) {
                this.form = this.getDefaultForm()
                if (this.stageOptions.length) {
                    this.form.stage = this.stageOptions[0].id
                }
                this.formKey += 1
                return
            }

            if (!this.deal) return

            this.form = {
                name: this.deal.name || '',
                description: this.deal.description || '',
                stage: this.deal.stage?.id || null,
                responsible: this.deal.responsible || null,
                customer_card: this.deal.customer_card?.id || null,
                source_ticket: this.deal.source_ticket?.id || null,
                expected_amount: this.normalizeNumber(this.deal.expected_amount),
                internal_budget: this.normalizeNumber(this.deal.internal_budget),
                probability: Number(this.deal.probability || 0),
                planned_close_date: this.deal.planned_close_date ? this.$moment(this.deal.planned_close_date) : null,
                members: (this.deal.members || []).map(item => ({ ...item })),
                observers: (this.deal.observers || []).map(item => ({ ...item })),
            }

            if (this.deal.customer_card) {
                this.customerCardOptionList = [this.toOption(this.deal.customer_card.id, this.getCustomerCardLabel(this.deal.customer_card))]
            }
            this.formKey += 1
        },
        submit() {
            this.$refs.form.validate(valid => {
                if (!valid) return
                this.$emit('save', {
                    name: this.form.name,
                    description: this.form.description,
                    stage: this.form.stage,
                    responsible: this.form.responsible?.id || null,
                    customer_card: this.form.customer_card,
                    source_ticket: this.form.source_ticket,
                    expected_amount: this.form.expected_amount,
                    internal_budget: this.form.internal_budget,
                    probability: Number(this.form.probability || 0),
                    planned_close_date: this.form.planned_close_date ? this.form.planned_close_date.format('YYYY-MM-DD') : null,
                    members: this.form.members.map(item => item.id),
                    observers: this.form.observers.map(item => item.id),
                })
            })
        },
        toOption(id, label) {
            return {
                id,
                string_view: label || String(id)
            }
        },
        getCustomerCardLabel(client) {
            if (!client) return ''
            return client.string_view || client.full_name || client.name || String(client.id || '')
        },
        normalizeNumber(value) {
            if (value === null || value === undefined || value === '') return null
            const numeric = Number(value)
            return Number.isFinite(numeric) ? numeric : null
        },
        formatMoney(value) {
            const numeric = Number(value || 0)
            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 2,
            }).format(numeric)
        },
        formatDate(value) {
            if (!value) return ''
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY') : ''
        },
        formatDecimal(value) {
            const numeric = Number(value || 0)
            if (!Number.isFinite(numeric)) return '0'
            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 2,
            }).format(numeric)
        },
        ticketLabel(ticket) {
            if (!ticket) return ''
            const prefix = ticket.number ? `#${ticket.number}` : ''
            return [prefix, ticket.name].filter(Boolean).join(' ')
        },
        formatDateTime(value) {
            if (!value) return ''
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY HH:mm') : ''
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        handleReturnedCustomerCard(client) {
            if (!this.value) return
            this.selectCustomerCard(client)
        },
        selectCustomerCard(client) {
            if (!client?.id) return
            this.customerCardOptionList = [this.toOption(client.id, this.getCustomerCardLabel(client))]
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
                this.customerCardOptionList = [this.toOption(data.id, this.getCustomerCardLabel(data))]
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.getClientLoading = false
            }
        },
        addCustomerCard() {
            eventBus.$emit('helpdesc_add_client', true, { slaSelect: true })
        },
        async openAllClients() {
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
        openCustomerCard() {
            if (!this.form.customer_card) return
            const query = { ...this.$route.query, client: this.form.customer_card }
            this.$router.push({ query })
        }
    }
}
</script>

<style lang="scss" scoped>
.deal_drawer__title_wrap {
    min-width: 0;
}

.deal_drawer__title {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
}

.deal_drawer__subtitle {
    margin-top: 4px;
    color: #64748b;
    font-size: 12px;
}

.deal_drawer__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
}

.deal_drawer__grid--bottom {
    margin-top: 18px;
}

.deal_drawer__summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 18px 0;
}

.deal_drawer__contract {
    border: 1px solid #dbeafe;
    border-radius: 16px;
    background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
    padding: 18px;
    margin: 18px 0;
    display: grid;
    gap: 14px;
}

.deal_drawer__contract_head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
}

.deal_drawer__contract_title {
    color: #0f172a;
    font-size: 16px;
    font-weight: 600;
}

.deal_drawer__contract_subtitle {
    margin-top: 4px;
    color: #64748b;
    font-size: 13px;
}

.deal_drawer__contract_grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.deal_drawer__contract_card {
    border-radius: 14px;
    background: #fff;
    border: 1px solid var(--border2);
    padding: 14px 16px;
    display: grid;
    gap: 6px;
}

.deal_drawer__contract_meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.deal_drawer__contract_chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: #eef2ff;
    color: #334155;
    padding: 6px 12px;
    font-size: 12px;
    line-height: 1.2;
}

.deal_drawer__contract_chip.is-success {
    background: #ecfdf5;
    color: #047857;
}

.deal_drawer__summary_card {
    border: 1px solid var(--border2);
    border-radius: 14px;
    background: #fff;
    padding: 14px 16px;
    display: grid;
    gap: 6px;
}

.deal_drawer__summary_card--accent {
    background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
    border-color: #bfdbfe;
}

.deal_drawer__summary_label {
    color: #64748b;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.deal_drawer__inline_link {
    margin-top: 6px;
}

.deal_drawer__files_wrap {
    min-height: 420px;
    border: 1px solid var(--border2);
    border-radius: 16px;
    overflow: hidden;
}

.deal_drawer__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.deal_drawer__footer_meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.deal_drawer__footer_actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
}

@media (max-width: 991px) {
    .deal_drawer__grid,
    .deal_drawer__summary,
    .deal_drawer__contract_grid {
        grid-template-columns: minmax(0, 1fr);
    }

    .deal_drawer__contract_head {
        flex-direction: column;
    }

    .deal_drawer__footer {
        flex-direction: column;
        align-items: stretch;
    }

    .deal_drawer__footer_actions {
        width: 100%;
        margin-left: 0;
    }

    .deal_drawer__footer_actions ::v-deep .ant-btn {
        flex: 1;
    }
}
</style>
