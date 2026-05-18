<template>
    <div class="select-wrapper">
        <a-select
            v-model="valueProxy"
            inputType="ghost"
            :getPopupContainer="triggerNode => triggerNode.parentNode"
            class="w-full"
            :options="comparisonOptions"/>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        changeComparisonType: {
            type: Function,
            required: true,
        },
    },
    data() {
        return {
        }
    },
    mounted() {
        if (!this.item.comparison_type) {
            this.changeComparisonType(this.comparisonOptions[0].value)
        }
    },
    computed: {
        comparisonOptions() {
            if (this.item.choices) {
                return [
                    { label: this.$t('Equals'), value: '=' },
                    { label: this.$t('Not equals'), value: '!=' },
                    { label: this.$t('In list'), value: 'in' },
                    { label: this.$t('Not in list'), value: 'not in' },
                    { label: this.$t('Filled'), value: 'not isnull' },
                    { label: this.$t('Not filled'), value: 'isnull' }
                ];
            }
            if (this.item.type.includes('DateTimeField') || this.item.type.includes('DateField')) {
                return [
                    { label: this.$t('Equals'), value: '=' },
                    { label: this.$t('Not equals'), value: '!=' },
                    { label: this.$t('Greater'), value: '>' },
                    { label: this.$t('Less'), value: '<' },
                    { label: this.$t('Greater or equal'), value: '>=' },
                    { label: this.$t('Less or equal'), value: '<=' },
                    { label: this.$t('Filled'), value: 'not isnull' },
                    { label: this.$t('Not filled'), value: 'isnull' }
                ];
            }
            if (this.item.type.includes('IntegerField') || this.item.type.includes('DecimalField')) {
                return [
                    { label: this.$t('Equals'), value: '=' },
                    { label: this.$t('Not equals'), value: '!=' },
                    { label: this.$t('Greater'), value: '>' },
                    { label: this.$t('Less'), value: '<' },
                    { label: this.$t('Greater or equal'), value: '>=' },
                    { label: this.$t('Less or equal'), value: '<=' },
                    { label: this.$t('Filled'), value: 'not isnull' },
                    { label: this.$t('Not filled'), value: 'isnull' }
                ];
            }
            if (this.item.type.includes('BooleanField')) {
                return [
                    { label: this.$t('Equals'), value: '=' },
                    { label: this.$t('Filled'), value: 'not isnull' },
                    { label: this.$t('Not filled'), value: 'isnull' }
                ];
            }
            if (this.item.related_model) {
                return [
                    { label: this.$t('Equals'), value: '=' },
                    { label: this.$t('Not equals'), value: '!=' },
                    { label: this.$t('In list'), value: 'in' },
                    { label: this.$t('Not in list'), value: 'not in' },
                    { label: this.$t('Filled'), value: 'not isnull' },
                    { label: this.$t('Not filled'), value: 'isnull' }
                ];
            }
            return [
                { label: this.$t('Contains'), value: 'icontains' },
                { label: this.$t('Not contains'), value: 'not icontains' },
                { label: this.$t('Equals'), value: '=' },
                { label: this.$t('Not equals'), value: '!=' },
                { label: this.$t('Filled'), value: 'not isnull' },
                { label: this.$t('Not filled'), value: 'isnull' }
            ];
        },
        valueProxy: {
            get() {
                return this.item.comparison_type
            },
            set(value) {
                this.changeComparisonType(value)
            }
        }
    }
}
</script>


<style lang="scss" scoped>
::v-deep {
    .ant-select-ghost:hover .ant-select-selection {
        background-color: #F0F1F7;
    }
}
</style>
