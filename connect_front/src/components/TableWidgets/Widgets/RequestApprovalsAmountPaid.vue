<template>
    <div>
        <template v-if="hasIssuedAmount">
            {{ formatMoney(issuedAmount) }}
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
        hasIssuedAmount() {
            return this.record?.amount_paid !== null && this.record?.amount_paid !== undefined
        },
        issuedAmount() {
            return this.toNumber(this.record?.amount_paid)
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