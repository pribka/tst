<template>
    <div class="sorting-select-wrap">
        <a-select
            v-model="selectValue"
            inputType="ghost"
            @change="selectChange"
            :getPopupContainer="triggerNode => triggerNode.parentNode"
            class="w-full"
            :options="[
                { label: $t('No sorting'), value: 0 },
                { label: $t('Ascending'), value: 'ASC' },
                { label: $t('Descending'), value: 'DESC' }
            ]"/>
        <span v-if="sortOrderNumber !== null" class="sort-order-badge">
            {{ sortOrderNumber }}
        </span>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
    },
    computed: {
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        activeOrdering() {
            return this.activeTemplate.metadata.ordering
        },
        activeOrderingItem() {
            const fieldName = this.item.aggregate ? this.item.title : this.item.name
            return this.activeOrdering.find(column => column.name === fieldName)
        },
        sortOrderNumber() {
            if (!this.activeOrderingItem?.orderBy) return null
            return Number(this.activeOrderingItem.order || 0) + 1
        },
        selectValue: {
            get() {
                return this.activeOrderingItem?.orderBy || 0
            },
            set(newValue) {
                const fieldName = this.item.aggregate ? this.item.title : this.item.name
                this.$store.commit('reports/SET_ORDERING', { fieldName, orderBy: newValue, aggregate: this.item.aggregate })
            },
        }
    },
    mounted() {
    },
    methods: {
        selectChange(value) {
            // this.changeItemValue(value === 'y')
        }
    }
}
</script>

<style scoped>
.sorting-select-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.sort-order-badge {
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 9999px;
    background: #f0f0f0;
    color: #595959;
    font-size: 12px;
    font-weight: 600;
    line-height: 22px;
    text-align: center;
    flex-shrink: 0;
}
</style>
