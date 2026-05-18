<template>
    <a-input
        v-model="valueProxy"
        inputType="ghost"
        :placeholder="item.verbose_name"/>
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
        }
    }
}
</script>
