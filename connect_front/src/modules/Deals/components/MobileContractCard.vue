<template>
    <div class="contract_mobile_card" @click="$emit('open', item.id)">
        <div class="contract_mobile_card__top">
            <div class="contract_mobile_card__main">
                <div class="contract_mobile_card__number">
                    {{ numberTitle }}
                </div>
                <div v-if="customerName" class="contract_mobile_card__customer">
                    {{ customerName }}
                </div>
            </div>

            <a-tag
                v-if="statusName"
                :color="statusColor"
                class="contract_mobile_card__status">
                {{ statusName }}
            </a-tag>
        </div>

        <div class="contract_mobile_card__rows">
            <div class="contract_mobile_card__row contract_mobile_card__row_left">
                <div class="contract_mobile_card__label">{{ $t('deals_contracts.organization') }}:</div>
                <div class="contract_mobile_card__value">{{ organizationName }}</div>
            </div>

            <div class="contract_mobile_card__grid">
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.contract_date') }}</div>
                    <div class="contract_mobile_card__value">{{ formatDate(item.contract_date) }}</div>
                </div>
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.amount') }}</div>
                    <div class="contract_mobile_card__value">{{ formatMoney(item.amount) }}</div>
                </div>
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.date_start') }}</div>
                    <div class="contract_mobile_card__value">{{ formatDate(item.date_start) }}</div>
                </div>
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.hours_plan') }}</div>
                    <div class="contract_mobile_card__value">{{ formatDecimal(item.hours_plan) }}</div>
                </div>
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.date_end') }}</div>
                    <div class="contract_mobile_card__value">{{ formatDate(item.date_end) }}</div>
                </div>
                <div class="contract_mobile_card__meta">
                    <div class="contract_mobile_card__label">{{ $t('deals_contracts.hours_fact') }}</div>
                    <div class="contract_mobile_card__value">{{ formatDecimal(item.hours_fact) }}</div>
                </div>
            </div>

            <div class="contract_mobile_card__row">
                <div class="contract_mobile_card__label">{{ $t('deals_contracts.updated_at') }}:</div>
                <div class="contract_mobile_card__value">{{ formatDateTime(item.updated_at) }}</div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'DealsMobileContractCard',
    props: {
        item: {
            type: Object,
            required: true,
        },
    },
    computed: {
        numberLocale() {
            const locale = this.$i18n?.locale
            const localeMap = {
                ru: 'ru-RU',
                kk: 'kk-KZ',
                en: 'en-US',
            }

            return localeMap[locale] || 'ru-RU'
        },
        customer() {
            return this.item?.external_customer || this.item?.customer_card || null
        },
        customerName() {
            return this.customer?.string_view || this.customer?.full_name || this.customer?.name || ''
        },
        organizationName() {
            return this.item?.organization?.name || '-'
        },
        statusName() {
            return this.item?.status?.name || this.item?.status?.label || this.item?.status?.code || ''
        },
        statusColor() {
            return this.item?.status?.color || 'blue'
        },
        numberTitle() {
            return this.item?.number
                ? `${this.$t('deals_contracts.number')}: ${this.item.number}`
                : `${this.$t('deals_contracts.number')}: -`
        },
    },
    methods: {
        formatDate(value) {
            if (!value) return '-'
            const date = this.$moment(value)
            return date.isValid() ? date.format('DD.MM.YYYY') : '-'
        },
        formatDateTime(value) {
            if (!value) return '-'
            const date = this.$moment(value)
            return date.isValid() ? date.format('DD.MM.YYYY HH:mm') : '-'
        },
        formatMoney(value) {
            const numeric = Number(value)
            if (!Number.isFinite(numeric)) return '-'

            return new Intl.NumberFormat(this.numberLocale, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }).format(numeric)
        },
        formatDecimal(value) {
            const numeric = Number(value)
            if (!Number.isFinite(numeric)) return '0.00'

            return new Intl.NumberFormat(this.numberLocale, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }).format(numeric)
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_mobile_card {
    background: #fff;
    border-radius: var(--borderRadius);
    padding: 14px;
    margin-bottom: 10px;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);

    &__top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
    }

    &__main {
        min-width: 0;
        flex: 1;
    }

    &__number {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
        line-height: 1.35;
    }

    &__customer {
        margin-top: 4px;
        font-size: 13px;
        color: #334155;
        line-height: 1.4;
        word-break: break-word;
    }

    &__status {
        flex-shrink: 0;
    }

    &__rows {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    &__row {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
        font-size: 13px;
        line-height: 1.4;
    }

    &__row_left {
        align-items: baseline;
        justify-content: flex-start;
        gap: 6px;
    }

    &__grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 12px;
    }

    &__meta {
        padding: 9px 10px;
        border-radius: 12px;
        background: #f8fafc;
        min-width: 0;
    }

    &__label {
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
    }

    &__value {
        color: #0f172a;
        font-size: 13px;
        line-height: 1.4;
        word-break: break-word;
        text-align: right;
    }

    &__row_left &__value {
        text-align: left;
    }

    &__meta &__value {
        margin-top: 2px;
        text-align: left;
        font-weight: 600;
    }
}
</style>
