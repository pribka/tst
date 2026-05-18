<template>
    <div :class="isMobile ? 'filter-row-mobile' : 'filter-row'">
        <template v-if="!isMobile">
            <div class="flex items-center">
                <a-switch 
                    :checked="isFilterActive"
                    size="small"
                    @change="toggleFilter" />
                <slot name="grab"></slot>
            </div>
            <div>
                {{ item.title }}
            </div>
            <div class="flex items-center">
                <component
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
        </template>

        <template v-else>
            <div class="filter-row-mobile__top">
                <div class="filter-row-mobile__controls">
                    <a-switch 
                        :checked="isFilterActive"
                        size="small"
                        @change="toggleFilter" />
                    <slot name="grab"></slot>
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
            <div class="filter-row-mobile__title">
                {{ item.title }}
            </div>
            <div class="filter-row-mobile__value">
                <component
                    :is="inputComponent"
                    :changeItemValue="changeItemValue"
                    :item="item" />
            </div>
        </template>
    </div>
</template>

<script>
// import DrawerSelect from "@apps/DrawerSelect/index.vue"
export default {
    components: {
        // DrawerSelect
    },
    props: {
        item: {
            type: Object,
            required: true,
        },
    },

    data() {
        return {
            metadata: {
                users: []
            }
        }
    },

    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        inputComponent() {
            if (this.item.choices) {
                return () => import('../FilterWidgets/ChoicesField')
            }
            if (this.item.type.includes('DateTimeField') || this.item.type.includes('DateField')) {
                return () => import('../FilterWidgets/DateRangeField')
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
    mounted() {
        this.initComparisonType('icontains')
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
        setComparisonType(value) {
            this.$store.commit('reports/SET_FILTER_FIELD', { filter: this.item, fieldName: 'comparison_type', value: value })
        },
        changeItemValue(newValue) {
            this.enableFilter()
            this.$store.commit('reports/SET_FILTER_FIELD', { filter: this.item, fieldName: 'value', value: newValue })
        },
        toggleFilter(active) {
            this.$store.commit('reports/SET_FILTER_FIELD', { filter: this.item, fieldName: 'active', value: active })
        },
        enableFilter() {
            this.$store.commit('reports/SET_FILTER_FIELD', { filter: this.item, fieldName: 'active', value: true })
        },
        removeFilter() {
            this.$store.commit('reports/REMOVE_LIST_ITEM', { listKey: 'filters', item: this.item })
        }
    },
};
</script>


<style lang="scss" scoped>
.filter-row {
    display: grid;
    gap: 12px;
    align-items: center;
    grid-template-columns: 50px 1fr 2fr 50px;
}

.filter-row-mobile {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
}

.filter-row-mobile__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.filter-row-mobile__controls {
    display: flex;
    align-items: center;
}

.filter-row-mobile__title {
    line-height: 1.35;
}

.filter-row-mobile__value {
    min-width: 0;
}
</style>
