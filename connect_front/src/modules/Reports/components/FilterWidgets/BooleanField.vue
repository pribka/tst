<template>
    <a-select
        :value="selectValue"
        inputType="ghost"
        @change="selectChange"
        class="w-full"
        :getPopupContainer="triggerNode => triggerNode.parentNode"
        :options="[
            { label: $t('Yes'), value: 'y' },
            { label: $t('No'), value: 'n' }
        ]"/>
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
        selectValue() { 
            return this.item.value ? 'y' : 'n'
        }
    },
    mounted() {
        if (this.item.value === null) {
            this.selectChange('y')
        }
    },
    methods: {
        selectChange(value) {
            this.changeItemValue(value === 'y')
        }
    }
}
</script>
