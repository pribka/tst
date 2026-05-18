<template>
    <div class="filter-row">
        <div class="flex items-center">
            <a-switch 
                :checked="isFilterActive"
                size="small"
                @change="toggleFilter" />
            <slot name="grab"></slot>
            <div>
                {{ item.title }}
            </div>
        </div>
        <ComparisonTypeField 
            :item="item"
            :changeComparisonType="setComparisonType" />
        <div class="flex items-center min-w-0">
            <component
                v-if="showInputComponent"
                :is="inputComponent"
                :changeItemValue="changeItemValue"
                :item="item" />
        </div>
        <a-button 
            type="ui" 
            ghost
            shape="circle"
            class="text_red" 
            flaticon
            icon="fi-rr-trash"
            @click="removeFilter">
        </a-button>
    </div>
</template>

<script>
export default {
    components: {
        ComparisonTypeField: () => import("../ComplexFilterWidgets/ComparisonTypeField.vue")
    },
    props: {
        item: {
            type: Object,
            required: true,
        },
        parentPath: {
            required: true,
            type: Array
        }
    },
    data() {
        return {
            metadata: {
                users: []
            }
        }
    },
    computed: {
        showInputComponent() {
            return !['isnull', 'not isnull'].includes(this.item.comparison_type)
        }, 
        inputComponent() {
            if (this.item.choices) {
                return () => import('../FilterWidgets/ChoicesField')
            }
            if (this.item.type.includes('DateTimeField') || this.item.type.includes('DateField')) {
                return () => import('../FilterWidgets/DateTimeField')
            }
            if (this.item.type.includes('IntegerField') || this.item.type.includes('DecimalField')) {
                return () => import('../FilterWidgets/IntegerField')
            }
            if (this.item.type.includes('BooleanField')) {
                return () => import('../FilterWidgets/BooleanField')
            }
            if (this.item.related_model) {
                return () => import('../FilterWidgets/ForeignKey')
            }
            return () => import('../FilterWidgets/ChartField.vue')
        },
        isFilterActive() {
            return this.item.active
        },
        filterValue() {
            return this.item.value
        }
    },
    methods: {
        initComparisonType() {
            if (this.item.type.includes('BooleanField')) {
                return this.setComparisonType('=')
            }
            if (this.item.related_model) {
                return this.setComparisonType('in')
            }
            if (this.item.type.includes('CharField')) {
                return this.setComparisonType('icontains')
            }
            return this.setComparisonType('=')
        },
        updateField(fieldName, value) {
            this.$store.commit('reports/CHANGE_COMPLEX_FILTER_FIELD', { 
                path: [...this.parentPath, this.item.id], 
                fieldName, 
                value 
            })
        },
        setComparisonType(value) {
            this.updateField('comparison_type', value)
        },
        changeItemValue(value) {
            this.updateField('value', value)
        },
        toggleFilter(value) {
            this.updateField('active', value)
        },
        removeFilter() {
            this.$store.commit('reports/REMOVE_COMPLEX_FILTER_FIELD', { 
                path: [...this.parentPath, this.item.id], 
            })
        }
    },
};
</script>


<style lang="scss" scoped>
.filter-row {
    padding: 8px 12px;
    display: grid;
    gap: 12px;
    align-items: center;
    grid-template-columns: 1fr 1fr 1fr 50px;
}
</style>