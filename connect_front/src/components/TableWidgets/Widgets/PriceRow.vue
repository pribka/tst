<template>
    <div>
        {{ cellText }}
    </div>
</template>

<script>
import { priceFormatter } from '@/utils'

export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object]
        },
        record: {
            type: Object
        },
        column: {
            type: Object,
            required: true
        }
    },
    computed: {
        cellText() {
            const value = this.getNumericValue(this.text)
            if (value === null) return ''

            if(this.column.key === 'mustpaid')
                return this.priceFormatter(value)
            if(this.column.key === 'amount') {
                let cellText = this.priceFormatter(value)
                if(this.record.currency)
                    cellText += ' ' + this.record.currency.icon
                
                return cellText
            }
            return this.priceFormatter(value)
        }
    },
    methods: {
        getNumericValue(value) {
            if (value === null || value === undefined || value === '') return null
            if (typeof value === 'boolean' || typeof value === 'object') return null

            const normalized = String(value).trim().replace(/\s/g, '').replace(',', '.')
            if (!normalized) return null

            const numberValue = Number(normalized)
            return Number.isFinite(numberValue) ? normalized : null
        },
        priceFormatter
    }
}
</script>
