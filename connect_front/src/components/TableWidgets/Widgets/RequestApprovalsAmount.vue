<template>
    <div>
        <template v-if="record.amount_requested">
            {{ formattedAmount }} &#8376;
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
        },
    },
    computed: {
        formattedAmount() {
            if (!this.record?.amount_requested) return ''

            const value = String(this.record.amount_requested)

            const [intPart, decimalPart] = value.split('.')

            const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

            if (decimalPart && Number(decimalPart) !== 0) {
                return `${formattedInt}.${decimalPart}`
            }

            return formattedInt
        }
    }
}
</script>