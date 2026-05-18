<template>
    <a-input-number
        v-model="valueProxy"
        :placeholder="item.verbose_name"
        inputType="ghost"
        class="w-full"/>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        changeItemValue: {
            type: Function,
            required: true,
        },
    },
    computed: {
        valueProxy: {
            get() {
                return this.item.value
            },
            set(value) {
                this.changeItemValue(value)
            }
        },
        isDecimal() {
            return this.item.type.includes('DecimalField')
        }
    },
}
</script>
