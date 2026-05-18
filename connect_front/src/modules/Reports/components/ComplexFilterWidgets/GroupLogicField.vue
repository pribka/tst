<template>
    <a-select
        v-model="valueProxy"
        inputType="ghost"
        class="w-full"
        :getPopupContainer="triggerNode => triggerNode.parentNode"
        :options="[
            { label: $t('AND'), value: 'and' },
            { label: $t('OR'), value: 'or' }
        ]"/>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        parentPath: {
            require: true,
            type: Array
        }
    },
    computed: {
        valueProxy: {
            get() {
                return this.item.logic
            },
            set(value) {
                this.$store.commit('reports/CHANGE_COMPLEX_FILTER_FIELD', { 
                    path: [...this.parentPath, this.item.id], 
                    fieldName: 'logic', 
                    value: value 
                })
            }
        }
    }
}
</script>
