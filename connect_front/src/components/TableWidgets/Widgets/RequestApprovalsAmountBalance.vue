<template>
    <div>
        <template v-if="hasBalance">
            <span :class="{ text_red: balanceAmount > 0, green: balanceAmount < 0 }">
                {{ formatMoney(balanceAmount) }}
            </span>
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
        hasBalance() {
            return this.record?.balance !== null && this.record?.balance !== undefined
        },
        balanceAmount() {
            return this.toNumber(this.record?.balance)
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

<style scoped>
.green {
    color: #16a34a;
}
.text_red {
    color: #ef4444;
}
</style>
