<template>
    <div>
        <template v-if="hasReportedAmount">
            {{ formatMoney(reportedAmount) }}
        </template>
        <template v-else>
            -
        </template>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        hasReportedAmount() {
            return this.record?.amount_paid !== null &&
                   this.record?.amount_paid !== undefined &&
                   this.record?.balance !== null &&
                   this.record?.balance !== undefined
        },
        issuedAmount() {
            return this.toNumber(this.record?.amount_paid)
        },
        balanceAmount() {
            return this.toNumber(this.record?.balance)
        },
        reportedAmount() {
            return this.issuedAmount - this.balanceAmount
        }
    },
    methods: {
        toNumber(v) {
            if (v === null || v === undefined) return 0
            const n = Number(String(v).replace(/\s/g, '').replace(',', '.'))
            return Number.isFinite(n) ? n : 0
        },
        formatMoney(v) {
            const n = this.toNumber(v)
            const hasFrac = Math.round(n * 100) % 100 !== 0
            const opts = hasFrac
                ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
                : { minimumFractionDigits: 0, maximumFractionDigits: 0 }

            return new Intl.NumberFormat('ru-RU', opts).format(n) + ' ₸'
        }
    }
}
</script>