<template>
    <DrawerTemplate
        :value="value"
        :width="drawerWidth"
        :loading="loading"
        destroyOnClose
        @close="$emit('close')">
        <template #title>
            <div class="contract_drawer__title">{{ drawerTitle }}</div>
        </template>

        <template #rightHeader>
            <div v-if="contract" class="flex items-center gap-2">
                <a-button
                    v-if="canEditContract"
                    type="ui"
                    ghost
                    shape="circle"
                    icon="fi-rr-edit"
                    flaticon
                    v-tippy
                    :content="$t('edit')"
                    :disabled="loading"
                    @click="$emit('edit')" />
                <a-button
                    v-if="canDeleteContract"
                    type="ui"
                    ghost
                    shape="circle"
                    icon="fi-rr-trash"
                    flaticon
                    v-tippy
                    :content="$t('remove')"
                    :disabled="loading"
                    @click="$emit('delete')" />
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    icon="fi-rr-refresh"
                    flaticon
                    v-tippy
                    :content="$t('update')"
                    @click="$emit('reload')" />
            </div>
        </template>

        <template #tabs>
            <a-tabs :activeKey="activeTab" @change="handleTabChange">
                <a-tab-pane key="overview" :tab="$t('deals_contracts.overview_tab')" />
                <a-tab-pane key="projects" :tab="$t('deals_contracts.projects_tab')" />
                <a-tab-pane key="files" :tab="$t('deals_contracts.files_tab')" />
            </a-tabs>
        </template>

        <a-tabs :activeKey="activeTab" class="body_tab contract_drawer__body_tabs">
            <a-tab-pane key="overview" :tab="$t('deals_contracts.overview_tab')">
                <a-alert
                    v-if="!edit"
                    type="info"
                    show-icon
                    class="mb-4"
                    :message="$t('deals_contracts.readonly_notice')" />

                <div class="contract_drawer__summary">
                    <div class="contract_drawer__card">
                        <span>{{ $t('deals_contracts.amount') }}</span>
                        <strong>{{ formatMoney(contract?.amount) }}</strong>
                    </div>
                    <div class="contract_drawer__card">
                        <span>{{ $t('deals_contracts.hours') }}</span>
                        <strong>{{ formatDecimal(contract?.hours_fact) }} / {{ formatDecimal(contract?.hours_plan) }}</strong>
                    </div>
                    <div class="contract_drawer__card contract_drawer__card--accent">
                        <span>{{ $t('deals_contracts.hours_balance') }}</span>
                        <strong>{{ formatDecimal(hoursBalance) }}</strong>
                    </div>
                </div>

                <div class="contract_drawer__grid">
                    <a-form-model-item :label="$t('deals_contracts.number')" class="mb-2">
                        <a-input :value="contract?.number || ''" size="large" disabled />
                    </a-form-model-item>

                    <a-form-model-item :label="$t('deals_contracts.customer')" class="mb-2">
                        <a-input :value="getClientLabel(contractClient)" :title="getClientLabel(contractClient)" size="large" disabled />
                    </a-form-model-item>

                    <a-form-model-item :label="$t('deals_contracts.organization')" class="mb-2">
                        <a-input :value="contract?.organization?.name || '-'" size="large" disabled />
                    </a-form-model-item>

                    <a-form-model-item :label="$t('deals_contracts.contract_date')" class="mb-2">
                        <a-input :value="formatDate(contract?.contract_date)" size="large" disabled />
                    </a-form-model-item>

                    <a-form-model-item :label="$t('deals_contracts.date_start')" class="mb-2">
                        <a-input :value="formatDate(contract?.date_start)" size="large" disabled />
                    </a-form-model-item>

                    <a-form-model-item :label="$t('deals_contracts.date_end')" class="mb-2">
                        <a-input :value="formatDate(contract?.date_end)" size="large" disabled />
                    </a-form-model-item>
                </div>

                <div class="contract_drawer__meta">
                    <a-tag>{{ contract?.is_signed ? $t('deals_contracts.signed') : $t('deals_contracts.not_signed') }}</a-tag>
                    <a-tag>{{ contract?.is_exists ? $t('deals_contracts.original_exists') : $t('deals_contracts.original_missing') }}</a-tag>
                </div>

                <ContractServiceCardsManager
                    v-if="contract"
                    :contract="contract"
                    :canEdit="canEditServiceCards"
                    @changed="$emit('reload')" />
            </a-tab-pane>

            <a-tab-pane key="projects" :tab="$t('deals_contracts.projects_tab')">
                <ContractProjectsWorkspaceTab
                    :contract="contract"
                    :savingProjects="savingProjects || saving"
                    @save-projects="$emit('save-projects', $event)"
                    @open-related="$emit('open-related', $event)" />
            </a-tab-pane>

            <a-tab-pane key="files" :tab="$t('deals_contracts.files_tab')">
                <div v-if="filesSourceId" class="contract_drawer__files">
                    <vue2Files
                        :sourceId="String(filesSourceId)"
                        :isFounder="filesIsFounder"
                        widgetEmbed
                        isStudent />
                </div>
                <a-empty v-else :description="$t('deals_contracts.files_empty')" />
            </a-tab-pane>
        </a-tabs>

        <template #footer>
            <div class="contract_drawer__footer">
                <a-button type="ui_ghost" @click="$emit('close')">{{ $t('close') }}</a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
export default {
    name: 'ContractDrawer',
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        ContractProjectsWorkspaceTab: () => import('./ContractProjectsWorkspaceTab.vue'),
        ContractServiceCardsManager: () => import('./ContractServiceCardsManager.vue'),
        vue2Files: () => import('@apps/vue2Files'),
    },
    props: {
        value: { type: Boolean, required: true },
        loading: { type: Boolean, default: false },
        saving: { type: Boolean, default: false },
        savingProjects: { type: Boolean, default: false },
        contract: { type: Object, default: () => null },
        actions: { type: Object, default: () => null },
        isNew: { type: Boolean, default: false },
        edit: { type: Boolean, default: false },
        routeTab: { type: String, default: '' },
    },
    data() {
        return {
            activeTab: 'overview',
        }
    },
    computed: {
        drawerWidth() {
            return this.$store.state.isMobile ? '100%' : 1280
        },
        drawerTitle() {
            if (this.isNew) {
                return this.$t('deals_contracts.title_new')
            }
            if (!this.contract) {
                return this.$t('deals_contracts.title')
            }
            const number = this.getContractNumber(this.contract.number)
            const date = this.formatDate(this.contract.contract_date || this.contract.date_start || this.contract.created_at)
            if (number && date) {
                return this.$t('deals_contracts.title_existing_with_number_date', { number, date })
            }
            if (number) {
                return this.$t('deals_contracts.title_existing_with_number', { number })
            }
            if (date) {
                return this.$t('deals_contracts.title_existing_with_date', { date })
            }
            return this.$t('deals_contracts.title_existing_fallback')
        },
        filesSourceId() {
            return this.contract?.id || null
        },
        contractClient() {
            return this.contract?.external_customer || this.contract?.customer_card || null
        },
        filesIsFounder() {
            return Boolean(this.filesSourceId)
        },
        hoursBalance() {
            return Number(this.contract?.hours_plan || 0) - Number(this.contract?.hours_fact || 0)
        },
        numberLocale() {
            const locale = this.$i18n?.locale
            const localeMap = {
                ru: 'ru-RU',
                kk: 'kk-KZ',
                en: 'en-US',
            }
            return localeMap[locale] || 'ru-RU'
        },
        canEditContract() {
            return this.actionAvailable('edit')
        },
        canDeleteContract() {
            return this.actionAvailable('delete')
        },
        canEditServiceCards() {
            return this.actionAvailable('served_organizations_edit')
        },
    },
    watch: {
        value(val) {
            if (val) {
                this.activeTab = this.normalizeTab(this.routeTab)
            }
        },
        routeTab: {
            immediate: true,
            handler(val) {
                const normalized = this.normalizeTab(val)
                if (normalized !== this.activeTab) {
                    this.activeTab = normalized
                }
            },
        },
    },
    methods: {
        normalizeTab(tab) {
            const available = new Set(['overview', 'projects', 'files'])
            const key = String(tab || '')
            return available.has(key) ? key : 'overview'
        },
        handleTabChange(tab) {
            const normalized = this.normalizeTab(tab)
            if (normalized !== this.activeTab) {
                this.activeTab = normalized
            }
            this.$emit('tab-change', normalized)
        },
        actionAvailable(key) {
            const action = this.actions?.[key]
            return Boolean(action?.availability || action?.available)
        },
        getContractNumber(value) {
            if (value === null || value === undefined) return ''
            return String(value).trim()
        },
        getClientLabel(client) {
            if (!client) return ''
            return client.string_view || client.full_name || client.name || String(client.id || '')
        },
        formatMoney(value) {
            return new Intl.NumberFormat(this.numberLocale, { maximumFractionDigits: 2 }).format(Number(value || 0))
        },
        formatDecimal(value) {
            const numeric = Number(value || 0)
            return Number.isFinite(numeric) ? new Intl.NumberFormat(this.numberLocale, { maximumFractionDigits: 2 }).format(numeric) : '0'
        },
        formatDate(value) {
            if (!value) return ''
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY') : ''
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_drawer__title { font-size: 18px; font-weight: 600; color: #111827; }
.contract_drawer__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.contract_drawer__summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 12px 0; }
.contract_drawer__card { border: 1px solid var(--border2); border-radius: 14px; background: #fff; padding: 14px 16px; display: grid; gap: 6px; }
.contract_drawer__card--accent { background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%); border-color: #bfdbfe; }
.contract_drawer__card span { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
.contract_drawer__meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.contract_drawer__files { min-height: 420px; overflow: hidden; }
.contract_drawer__body_tabs {
    &::v-deep > .ant-tabs-bar {
        display: none;
    }
}
.contract_drawer__footer { display: flex; justify-content: flex-end; gap: 10px; }
@media (max-width: 991px) {
    .contract_drawer__grid,
    .contract_drawer__summary { grid-template-columns: minmax(0, 1fr); }
    .contract_drawer__footer { flex-direction: column; align-items: stretch; }
}
</style>
